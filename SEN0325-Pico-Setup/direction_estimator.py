"""Experimental narrowband DOA from synchronous center-referenced cross spectra.

Q uses +sin in the Pico detector, so an earlier-arriving wave has negative phase.
Fit phase = -k * (x*ux + y*uy) + common_offset using weighted least squares.
"""
import json
import math
from pathlib import Path
import threading


def wrap(angle):
    return (angle + math.pi) % (2 * math.pi) - math.pi


def solve3(matrix, vector):
    rows = [list(row) + [value] for row, value in zip(matrix, vector)]
    for col in range(3):
        pivot = max(range(col, 3), key=lambda i: abs(rows[i][col]))
        if abs(rows[pivot][col]) < 1e-12:
            return None
        rows[col], rows[pivot] = rows[pivot], rows[col]
        scale = rows[col][col]
        rows[col] = [value / scale for value in rows[col]]
        for i in range(3):
            if i != col:
                scale = rows[i][col]
                rows[i] = [a-scale*b for a,b in zip(rows[i],rows[col])]
    return [rows[i][3] for i in range(3)]


class PhaseEstimator:
    def __init__(self, config_path):
        self.path = Path(config_path)
        self.config = json.loads(self.path.read_text(encoding="utf-8-sig"))
        self.lock = threading.Lock()
        self.previous_dropped = None
        self.smoothed = None
        self.last_valid_time = 0

    def save(self):
        self.path.write_text(json.dumps(self.config,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    def set_front(self, raw_angle):
        with self.lock:
            sign = -1 if self.config["mirror_view"] else 1
            self.config["heading_offset_deg"] = (-sign*raw_angle)%360
            self.config["heading_calibrated"] = True
            self.smoothed = None
            self.save()

    def set_mirror(self, mirror):
        with self.lock:
            self.config["mirror_view"] = bool(mirror)
            self.config["heading_calibrated"] = False
            self.config["heading_offset_deg"] = 0
            self.smoothed = None
            self.save()

    def estimate(self, phases, tones, frequency, health, now):
        with self.lock:
            config = dict(self.config)
        base = {"valid":False,"frequency":frequency,"method":"synchronous_narrowband_phase_WLS",
                "received_at":now,"heading_calibrated":config["heading_calibrated"]}
        def invalid(reason, **details):
            return {**base,"reason":reason,**details}
        if not config["minimum_frequency_hz"] <= frequency <= config["maximum_frequency_hz"]:
            return invalid("frequency_outside_doa_range")
        dropped = health.get("dropped",0)
        gap = self.previous_dropped is not None and dropped > self.previous_dropped
        self.previous_dropped = dropped
        if gap or health.get("rx_stall",0) or health.get("frames",0)==0:
            return invalid("capture_gap")
        ref = tones.get(config["reference"],{})
        if not ref.get("present") or ref.get("frequency") != frequency:
            return invalid("no_reference_tone")
        radius, speed = config["radius_m"], config["sound_speed_m_s"]
        k = 2*math.pi*frequency/speed
        observations=[]
        for name, bearing in config["clockwise_degrees_from_U7_M0"].items():
            phase, tone = phases.get(name), tones.get(name,{})
            if not phase or not tone.get("present") or tone.get("frequency") != frequency:
                continue
            if phase["coherence"] < .7:
                continue
            phi=wrap(phase["phase_rad"]-config.get("phase_offsets_rad",{}).get(name,0))
            angle=math.radians(bearing)
            observations.append({"channel":name,"row":[radius*math.sin(angle),radius*math.cos(angle),1.0],
                "value":-phi/k,"phase":phi,"weight":phase["coherence"]**2,"coherence":phase["coherence"]})
        if len(observations)<4:
            return invalid("insufficient_coherent_channels",channels=len(observations))
        def fit_rows(rows):
            weights=[row["weight"] for row in rows]
            fit=None
            for _ in range(3):
                matrix=[[sum(weight*row["row"][i]*row["row"][j] for row,weight in zip(rows,weights))
                         for j in range(3)] for i in range(3)]
                vector=[sum(weight*row["row"][i]*row["value"] for row,weight in zip(rows,weights))
                        for i in range(3)]
                fit=solve3(matrix,vector)
                if fit is None:
                    return None
                residuals=[k*(sum(a*b for a,b in zip(row["row"],fit))-row["value"]) for row in rows]
                weights=[row["weight"]*min(1,.15/max(abs(error),1e-9)) for row,error in zip(rows,residuals)]
            # Score with original coherence weights: robust reweighting must not
            # hide a large physical model error from the validity gate.
            rms=math.sqrt(sum(row["weight"]*error**2 for row,error in zip(rows,residuals))/sum(row["weight"] for row in rows))
            return fit,rms

        fitted=fit_rows(observations)
        if fitted is None:
            return invalid("degenerate_geometry")
        fit,residual=fitted
        excluded=[]
        # With all six channels available, reject at most one clear outlier,
        # only if the other five independently agree on a plausible wave.
        if len(observations)==6 and residual>.15:
            candidates=[]
            for omit,row in enumerate(observations):
                remaining=[item for i,item in enumerate(observations) if i!=omit]
                candidate=fit_rows(remaining)
                if candidate is None:
                    continue
                model,error=candidate
                held_error=abs(k*(sum(a*b for a,b in zip(row["row"],model))-row["value"]))
                magnitude=math.hypot(*model[:2])
                if (.25<=magnitude<=1.35 and error<=.12 and error<residual/2
                        and held_error>max(.35,4*error)):
                    candidates.append((error,omit,model,remaining))
            if candidates:
                residual,omit,fit,remaining=min(candidates,key=lambda item:item[0])
                excluded=[observations[omit]["channel"]]
                observations=remaining
        ux,uy,common=fit
        magnitude=math.hypot(ux,uy)
        coherence=sum(row["coherence"] for row in observations)/len(observations)
        quality=coherence*math.exp(-.5*(residual/.20)**2)*min(1,magnitude/.55)*len(observations)/6
        diagnostics={"channels":len(observations),"excluded_channels":excluded,"phase_residual_rad":round(residual,4),
                     "horizontal_projection":round(magnitude,4),"mean_coherence":round(coherence,4)}
        if magnitude < .25:
            return invalid("weak_horizontal_direction",**diagnostics)
        if magnitude > 1.35 or residual>.25 or quality<.45:
            return invalid("phase_model_mismatch",**diagnostics)
        raw_angle=math.degrees(math.atan2(ux,uy))%360
        sign=-1 if config["mirror_view"] else 1
        angle=(sign*raw_angle+config["heading_offset_deg"])%360
        vector=complex(math.sin(math.radians(angle)),math.cos(math.radians(angle)))
        if self.smoothed is not None and now-self.last_valid_time < .8:
            alpha=1-math.exp(-max(.001,now-self.last_valid_time)/.35)
            vector=self.smoothed*(1-alpha)+vector*alpha
        if abs(vector)>1e-8:
            vector/=abs(vector)
        self.smoothed=vector
        self.last_valid_time=now
        angle=math.degrees(math.atan2(vector.real,vector.imag))%360
        return {**base,"valid":True,"angle_deg":round(angle,2),"raw_angle_deg":round(raw_angle,2),
                "confidence":round(min(1,quality),3),"reason":"estimated",**diagnostics}

"""Check whether recorded pair delays can share ANY seven arrival times.

This diagnostic precedes geometric bearing fitting; no estimator changes.
"""
from pathlib import Path
import argparse
import json
import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
STAGE=PROJECT/'stages/05-direction-diagnostics'
CHANNELS=('D0L','D0R','D1L','D1R','D2L','D2R','D3R_CENTER')

def analyze(paths):
    rows=[]
    for path in paths:
        replay=json.loads(path.read_text(encoding='utf-8'))
        for row in replay['rows']:
            result=row['rx3_replay']
            if result['reason']!='group_delay_inconsistent':continue
            pairs=[p for p in result.get('pair_delay_diagnostics',[]) if p.get('used_in_fit')]
            if len(pairs)<6:continue
            incidence=np.zeros((len(pairs),7));target=[];weights=[]
            by_pair={}
            for i,pair in enumerate(pairs):
                a,b=[CHANNELS.index(name) for name in pair['pair']]
                incidence[i,a]=1;incidence[i,b]=-1
                target.append(pair['delay_samples']);weights.append(pair['coherence']**4)
                by_pair[a,b]=pair['delay_samples']
            target=np.array(target);weights=np.array(weights)
            solution=np.linalg.lstsq(incidence*np.sqrt(weights[:,None]),target*np.sqrt(weights),rcond=None)[0]
            residual=incidence@solution-target
            rms=float(np.sqrt(np.average(residual**2,weights=weights)))
            closures=[]
            for a in range(7):
                for b in range(a+1,7):
                    for c in range(b+1,7):
                        if all(p in by_pair for p in ((a,b),(b,c),(a,c))):
                            closures.append(abs(by_pair[a,b]+by_pair[b,c]-by_pair[a,c]))
            rows.append({'source':path.name,'sequence':row['sequence'],'code_pnr_db':result.get('code_pnr_db'),
                'fitted_pairs':len(pairs),'incidence_rank':int(np.linalg.matrix_rank(incidence)),
                'any_arrival_times_rms_samples':round(rms,4),
                'median_triangle_closure_samples':round(float(np.median(closures)),4) if closures else None,
                'primary_all_pair_rms_samples':result.get('all_pair_rms_samples')})
    report={'rows':rows,'analyzed_rejected_windows':len(rows),
            'median_any_arrival_times_rms_samples':round(float(np.median([r['any_arrival_times_rms_samples'] for r in rows])),4) if rows else None,
            'windows_any_arrival_times_rms_over_1_sample':sum(r['any_arrival_times_rms_samples']>1 for r in rows),
            'limitation':'Descriptive closure residual of pair-delay estimates, not a microphone fault diagnosis. Even arbitrary per-channel arrival times cannot remove this residual; geometric fitting can add further error. No ground-truth bearing is available.'}
    (STAGE/'pair-closure-analysis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('replay',nargs='+',type=Path)
    analyze(parser.parse_args().replay)

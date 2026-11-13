"""Build public aggregate metrics/figures from private telemetry. No serial I/O.

Requires matplotlib. Pass --private-output to the local dated output directory.
Only sanitized aggregates and derived angle/timing series are published; raw
events, session/device identifiers, audio and absolute input paths are omitted.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import sys


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ms_stats(value, divisor=1000):
    return {key: item/divisor if key != "count" and item is not None else item for key,item in value.items()}


def gather(private, project):
    sys.path.insert(0,str(project/'pico-standalone/tools'))
    from analyze_link_trial import parse_ack,fields
    root=private/'comm-link-v0.2';trials=[];source_hashes={};angle_series=[];rtts={}
    names=['01-link-recovery','02-phone','03-flash-warmup','04-flash-reboot']
    for name in names:
        analysis_name='02-phone-full' if name=='02-phone' else name
        summary_path=root/('analysis-trial-'+analysis_name)/'summary.json'
        event_path=root/('trial-'+name)/'events.jsonl'
        summary=read_json(summary_path);recording=read_json(event_path.parent/'summary.json')
        events=[json.loads(line) for line in event_path.read_text('utf-8').splitlines() if line.strip()]
        acks=[]
        for row in events:
            if row['line'].startswith('@'):
                try: acks.append(parse_ack(row['line']))
                except ValueError: pass
        c=summary['counts'];p=summary['pico_statistics'];b=[r for r in acks if r['type']==2]
        trial={'id':name,'seconds':recording['duration_s'],'overall_verdict':summary['overall_verdict'],
            'raw_event_count':len(events),'pico_windows':c['pico_windows'],'current_tx':c['current_tx'],
            'esp_bearings':c['esp_bearings'],'exact_packets':c['exact_packets'],'matched_packets':c['matched_packets'],
            'crc_valid_b_acks':len(b),'b_ack_status_counts':dict(Counter(str(r['status']) for r in b)),
            'later_pico_ack_confirmations':c['esp_and_pico_ack_confirmed'],
            'interior_missing_observations':c['interior_missing_observations'],
            'parse_error_count':len(summary['parse_errors']),'fit_valid':p['fit_valid'],'valid':p['valid'],
            'code_channels':p['code_channels'],'reasons':p['reasons'],'esp_classes':summary['esp_classes'],
            'dsp_ms':ms_stats(p['dsp_us']),'cycle_ms':ms_stats(p['cycle_us']),
            'measurement_age_ms':p['age_ms'],'ack_rtt_ms':ms_stats(p['unique_matched_ack_roundtrip_us']),
            'receiver_error_counter_deltas':{key:summary['esp_counter_deltas'][key]['observed_delta'] for key in ('bad','lines','ack_drop','usb_drop')},
            'boundary_unmatched_tx':sum(r.get('location')=='boundary_unmatched' for r in summary['missing_tx_observations']),
            'boundary_unmatched_esp':sum(r.get('location')=='boundary_unmatched' for r in summary['unmatched_esp_observations']),
            'final_ack_boundary':sum(r.get('missing_ack_location')=='boundary_unmatched' for r in summary['matches']),
            'warmup_used':bool(recording.get('warmup',{}).get('enabled'))}
        trials.append(trial)
        rtts[name]=[r['ack_roundtrip_us_including_foreground_delay']/1000 for r in summary['matches'] if r['ack_roundtrip_us_including_foreground_delay'] is not None]
        source_hashes['trial-'+name+'/events.jsonl']=sha(event_path)
        source_hashes['analysis-trial-'+analysis_name+'/summary.json']=sha(summary_path)
        if name=='02-phone':
            windows={r['seq']:r for r in summary['windows']}
            for match in summary['matches']:
                window=windows[match['result_seq']]
                angle_series.append({'elapsed_s':window['elapsed_s'],
                    'pico_tx_deg':match['fields']['tx_angle_cdeg']['pico']/100,
                    'esp_rx_deg':match['fields']['tx_angle_cdeg']['esp']/100,
                    'fit_valid':window['fit_valid'],'source_valid':match['fields']['tx_valid']['pico'],
                    'target_valid':match['target_valid']})
            prefix=[r for r in events[:4456] if r['line'].startswith(('source_age_ms=835','STAT count=231'))]
            startup={'repeated_esp_prefix_lines':len(prefix),'fragment_copies':sum(r['line']=='source_age_ms=835 target_valid=0' for r in prefix),
                'repeated_stat_copies':sum(r['line']=='STAT count=231 valid=0 bad=0 lines=0 ack_drop=0 usb_drop=0' for r in prefix),
                'prefix_end_elapsed_s':events[4455]['elapsed_s'],'malformed_stat_event_index':4456,
                'full_file_verdict':summary['overall_verdict'],'prefix_removed_from_analysis':False,
                'root_cause':'startup observation anomaly; FTDI driver cause not established'}

    event_path=root/'trial-05-no-pico-client/events.jsonl';events=[json.loads(line) for line in event_path.read_text('utf-8').splitlines() if line.strip()]
    recording=read_json(event_path.parent/'summary.json');bearings=[];acks=[];stats=[];errors=[]
    for index,row in enumerate(events):
        try:
            if row['line'].startswith('BEARING '):bearings.append(fields(row['line'],'BEARING'))
            elif row['line'].startswith('@'):acks.append(parse_ack(row['line']))
            elif row['line'].startswith('STAT '):stats.append(fields(row['line'],'STAT'))
        except ValueError as exc:errors.append({'index':index,'reason':str(exc)})
    b=[r for r in acks if r['type']==2]
    if len({r['session'] for r in acks}) != 1:
        raise ValueError('Trial 05 requires one observed ACK session; do not match by sequence alone')
    matched_ack=sum(any(a['seq']==r['seq'] and a['status']==r['ack_status'] for a in b) for r in bearings)
    trials.append({'id':'05-no-pico-client','seconds':recording['duration_s'],
        'overall_verdict':'esp_output_observed_without_pico_serial_client','raw_event_count':len(events),
        'pico_windows':None,'current_tx':None,'esp_bearings':len(bearings),'exact_packets':None,'matched_packets':None,
        'crc_valid_b_acks':len(b),'esp_records_with_matching_ack':matched_ack,
        'later_pico_ack_confirmations':None,'parse_error_count':len(errors),
        'observed_target_valid':sum(r['target_valid'] for r in bearings),'pico_serial_opened':False,
        'physical_usb_removed':False,'cold_start_test':False,
        'receiver_error_counter_deltas':{key:stats[-1][key]-stats[0][key] if len(stats)>1 else None for key in ('bad','lines','ack_drop','usb_drop')},
        'source_age_ms':{'min':min(r['source_age_ms'] for r in bearings),'median':statistics.median(r['source_age_ms'] for r in bearings),'max':max(r['source_age_ms'] for r in bearings)},
        'warmup_used':True})
    source_hashes['trial-05-no-pico-client/events.jsonl']=sha(event_path)
    task=read_json(private/'pico-task-breakdown.json')
    source_hashes['pico-task-breakdown.json']=sha(private/'pico-task-breakdown.json')
    resource_path=root/'candidates/flash-link-v0.2-11958e93/resource-audit.json';resource=read_json(resource_path)
    source_hashes['flash-link-v0.2/resource-audit.json']=sha(resource_path)
    resources={k:resource[k] for k in ('firmware','backend','image_kind','uf2_sha256','heap_capacity_linker','core0_stack_reserved','core1_stack_reserved','stack_high_water_measured','cpu_utilization_measured','core0_hz','core1_application_active','dma_buffers_bytes','pcm_window_bytes','dsp_workspace_bytes')}
    resources['application_static_stack_frames_bytes']={k:resource['application_stack_frames'][k]['bytes'] for k in ('main','report_result','gap_estimate','send_pending_result')}
    esp_build_path=project/'esp32-link/gap_receiver/firmware/BUILD.json'
    esp_build=read_json(esp_build_path)
    source_hashes['public/esp32-link/gap_receiver/firmware/BUILD.json']=sha(esp_build_path)
    assert esp_build['image_distributed'] is False, 'This release retains the tested ESP binary privately'
    for name,expected in esp_build['source_sha256'].items():
        assert sha(esp_build_path.parent.parent/name)==expected, 'ESP source does not match deployment manifest'
    categories=['fft_inverse','envelope_peaks','whitening_match','capture_scheduler','other_dsp','final_geometry']
    source_categories=['FFT 频域变换 + 逆变换','包络、峰值与候选提取','频谱白化 / 信标匹配','采集与调度（DSP 之外）','其他 DSP 工作','最终方向几何拟合']
    values=[task['breakdown_ms'][key] for key in source_categories]
    profile={'windows':task['windows'],'valid_fits':task['valid_fits'],'cycle_mean_ms':task['cycle_mean_ms'],
        'dsp_mean_ms':task['dsp_mean_ms'],'unpack_mean_ms':task['unpack_ms'],
        'phase_mean_ms':dict(zip(categories,values)),
        'timed_dsp_plus_unpack_fraction':(task['dsp_mean_ms']+task['unpack_ms'])/task['cycle_mean_ms'],
        'scope':'Earlier 17 FAST RAM windows; phase wall-time proxy, not CPU utilization; unpack overlaps capture'}
    return {'schema':'ee475-communication-public-v1','date':'2026-11-12','trials':trials,
        'trial02_startup':startup,'trial02_angle_transport_series':angle_series,'ack_rtt_series_ms':rtts,
        'timing_profile_17_windows':profile,'flash_resource_audit':resources,
        'esp32_deployed_build':{k:esp_build[k] for k in ('firmware','arduino_cli','core','fqbn','deployment_image_name','image_distributed','image_sha256','write_offset','program_bytes','global_bytes')},
        'historical_combo_reference':{'background_cycle_ms':188,'moving_phone_cycle_ms':203,'matched_conditions':False,
            'source':'earlier team combo reports; contextual reference supplied in the current handoff'},
        'bandwidth_calculated_not_measured':{'sample_rate_hz':48000,'i2s_bit_clock_hz':3072000,'four_data_lines_bits_per_s':12288000,
            'dma_bytes_per_s':1536000,'pcm16_seven_channels_bytes_per_s':672000,'uart_baud':115200,'uart_8n1_bytes_per_s':11520,
            'b_max_bytes':49,'b_max_wire_ms':49*10/115200*1000,'ack_max_bytes':45,'ack_max_wire_ms':45*10/115200*1000},
        'delay_target_ms':[200,500],'delay_target_met':False,'physical_angle_ground_truth_available':False,
        'physical_usb_disconnect_test_performed':False,'cold_start_test_performed':False,
        'source_hashes':source_hashes,'privacy':'Only aggregate/derived telemetry; no raw microphone audio, session identifiers, USB serial numbers or personal absolute paths'}


def figures(data,destination):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    font=Path('C:/Windows/Fonts/msyh.ttc')
    if font.exists():font_manager.fontManager.addfont(str(font))
    plt.rcParams.update({'font.family':'Microsoft YaHei' if font.exists() else 'DejaVu Sans','font.size':10,'axes.unicode_minus':False})
    blue='#1676a3';orange='#e98b20';green='#177b68';red='#b43d3d';grey='#8797a5'
    series=data['trial02_angle_transport_series'];profile=data['timing_profile_17_windows']
    for lang in ('EN','ZH'):
        zh=lang=='ZH';fig,axes=plt.subplots(3,2,figsize=(18,14));fig.patch.set_facecolor('#f7fafc')
        fig.subplots_adjust(left=.10,right=.97,top=.89,bottom=.09,wspace=.38,hspace=.66)
        fig.suptitle('Pico → ESP32：通信证据与剩余延迟' if zh else 'Pico → ESP32: communication evidence and remaining delay',fontsize=21,fontweight='bold',y=.975)
        fig.text(.5,.938,'全部控制目标仍为 valid=0；0.2–0.5 秒目标尚未达标。' if zh else 'All control targets remain valid=0; the 0.2–0.5 s delay target is not met.',ha='center',color=red,fontsize=13)
        ax=axes[0,0];ax.axis('off');ax.set_title('A  五轮观测的证据范围' if zh else 'A  Evidence scope across five recordings',loc='left',fontweight='bold')
        rows=[]
        for i,t in enumerate(data['trials']):
            rows.append([f'T{i+1:02d}',f"{t['exact_packets']}/{t['current_tx']}" if i<4 else '—',str(t['crc_valid_b_acks']),str(t['later_pico_ack_confirmations']) if i<4 else '—',
                (['背景/恢复','手机；启动异常','Flash背景','软件重启','仅监听ESP'][i] if zh else ['Background/recovery','Phone; startup anomaly','Flash background','Software reboot','ESP monitor only'][i])])
        table=ax.table(cellText=rows,colLabels=['测试','一致/TX','B ACK','Pico确认','条件'] if zh else ['Trial','Exact/TX','B ACK','Pico ACK','Condition'],loc='center',cellLoc='center',colWidths=[.1,.16,.14,.16,.44])
        table.auto_set_font_size(False);table.set_fontsize(9.5);table.scale(1,1.8)
        for (r,c),cell in table.get_celld().items():
            cell.set_edgecolor('#dce5eb');cell.set_facecolor('#e7f1f7' if r==0 else '#fff4e6' if r==2 else 'white')
        ax.text(0,-.08,'T02 全文件异常未过滤；T05 未拔 USB，也没有 Pico TX 对照。' if zh else 'T02 full-file anomaly is retained. T05 did not unplug USB; no Pico TX comparison.',transform=ax.transAxes,fontsize=9)
        ax=axes[0,1];times=[r['elapsed_s'] for r in series]
        ax.plot(times,[r['pico_tx_deg'] for r in series],color=blue,marker='.',label='Pico TX')
        ax.plot(times,[r['esp_rx_deg'] for r in series],linestyle='none',marker='o',markerfacecolor='none',markeredgecolor=orange,markersize=5,label='ESP RX')
        ax.axvspan(0,data['trial02_startup']['prefix_end_elapsed_s'],color=red,alpha=.15)
        ax.set(ylim=(-10,370),xlim=(0,30),yticks=[0,90,180,270,360],xlabel='录制经过时间 / s' if zh else 'Elapsed recording time / s',ylabel='原始阵列角度 / °' if zh else 'Raw array angle / °')
        ax.set_title('B  T02：33 组可匹配原始角度完全重合' if zh else 'B  T02: 33 matched raw-angle records overlap exactly',loc='left',fontweight='bold',fontsize=11)
        ax.legend(loc='upper right',fontsize=9);ax.grid(alpha=.2)
        ax.text(0,-.29,'仅证明字段传输一致；包含无拟合时的0值，无真实角度基准。\n原文件4453条异常前缀 + 1条坏STAT，整体不能判通过。' if zh else 'Transport agreement only; includes no-fit zero values, no physical angle truth.\nFull file: 4453 anomalous prefix lines + 1 malformed STAT; not a clean pass.',transform=ax.transAxes,fontsize=9,color=red)
        ax=axes[1,0];vectors=list(data['ack_rtt_series_ms'].values())
        boxes=ax.boxplot(vectors,tick_labels=['T01','T02','T03','T04'],patch_artist=True)
        for i,box in enumerate(boxes['boxes']):box.set_facecolor(orange if i==1 else '#9bc8dc')
        for i,values in enumerate(vectors):ax.text(i+1,min(values)-.15,f'n={len(values)}',ha='center',fontsize=9)
        ax.set(ylabel='ACK 往返观测 / ms' if zh else 'Observed ACK roundtrip / ms',ylim=(6.1,9.1))
        ax.set_title('C  ACK 记录包含前台解析等待' if zh else 'C  ACK timing includes foreground parsing delay',loc='left',fontweight='bold',fontsize=11);ax.grid(axis='y',alpha=.2)
        ax.text(0,-.23,'中位数：7.17 / 7.84 / 7.28 / 6.89 ms；不是纯线缆延迟。' if zh else 'Medians: 7.17 / 7.84 / 7.28 / 6.89 ms; not isolated cable latency.',transform=ax.transAxes,fontsize=9)
        ax=axes[1,1];bg=data['trials'][2];phone=data['trials'][1]
        values=[188,203,bg['dsp_ms']['median'],bg['measurement_age_ms']['median'],bg['cycle_ms']['median'],phone['dsp_ms']['median'],phone['measurement_age_ms']['median'],phone['cycle_ms']['median']]
        labels=['旧组合版：背景周期','旧组合版：移动周期','Pico Flash背景：DSP','Pico Flash背景：年龄','Pico Flash背景：周期','Pico RAM手机：DSP','Pico RAM手机：年龄','Pico RAM手机：周期'] if zh else ['Old combo: background cycle','Old combo: moving cycle','Pico Flash bg: DSP','Pico Flash bg: age','Pico Flash bg: cycle','Pico RAM phone: DSP','Pico RAM phone: age','Pico RAM phone: cycle']
        ax.axvspan(200,500,color=green,alpha=.09);ax.axvline(500,color=red,linestyle='--',linewidth=1)
        ax.barh(range(8),values,color=[grey,grey,blue,orange,green,blue,orange,green],height=.65)
        ax.set_yticks(range(8),labels,fontsize=8.5);ax.invert_yaxis();ax.set_xlim(0,1050);ax.set_xlabel('ms')
        for y,value in enumerate(values):ax.text(value+12,y,f'{value:.1f}',va='center',fontsize=9)
        ax.set_title('D  计时代理与旧周期参考；非同条件对照' if zh else 'D  Timing proxies and old cycles; conditions differ',loc='left',fontweight='bold',fontsize=11)
        ax.text(0,-.23,'浅绿为200–500ms目标区间；尚无声音起点同步测量。' if zh else 'Green band: 200–500 ms goal. Acoustic onset is not synchronized.',transform=ax.transAxes,fontsize=9)
        ax=axes[2,0];names=['FFT + 逆FFT','包络/峰值','白化/匹配','采集/调度','其他DSP','最终几何拟合'] if zh else ['FFT + inverse','Envelope / peaks','Whitening / match','Capture / scheduler','Other DSP','Final geometry']
        values=list(profile['phase_mean_ms'].values());ax.barh(range(6),values,color=[blue,orange,green,grey,'#887caf','#b48c63'])
        ax.set_yticks(range(6),names);ax.invert_yaxis();ax.set_xlim(0,565);ax.set_xlabel('平均每轮 ms' if zh else 'Mean milliseconds per cycle')
        for y,value in enumerate(values):ax.text(value+8,y,f'{value:.2f}  ({value/profile["cycle_mean_ms"]*100:.1f}%)',va='center',fontsize=9)
        ax.set_title('E  先前17个FAST窗口：计时占比，不是CPU利用率' if zh else 'E  Earlier 17 FAST windows: timed shares, not CPU load',loc='left',fontweight='bold',fontsize=11)
        ax.text(0,-.25,'周期均值881.24ms；解包14.59ms与采集重叠，未重复相加。' if zh else 'Mean cycle 881.24 ms. Unpack 14.59 ms overlaps capture; not added twice.',transform=ax.transAxes,fontsize=9)
        ax=axes[2,1];ax.axis('off');ax.set_title('F  资源与带宽边界' if zh else 'F  Resource and bandwidth boundaries',loc='left',fontweight='bold')
        lines=(['Core0 120MHz；Core1未使用，双核未实现。','Flash链接heap容量：104,660 B；不是实时空闲内存。','Core0预留栈：4096 B；未测运行时栈高水位。','PCM窗56KiB；DMA双缓冲32KiB；DSP工作区55,944B。','UART 115200/8N1：11,520 B/s；连续PCM需672,000 B/s。','B包上限49B≈4.25ms；ACK上限45B≈3.91ms。','带宽数字是源码计算，不是逻辑分析仪实测。','结论：当前链路传结果，不传七路原始音频。'] if zh else ['Core0 120 MHz; Core1 unused; no dual-core implementation.','Flash linker heap capacity: 104,660 B; not live free memory.','Core0 stack reserved: 4096 B; no runtime high-water measurement.','PCM 56 KiB; DMA 32 KiB; DSP workspace 55,944 B.','UART 115200/8N1: 11,520 B/s; continuous PCM needs 672,000 B/s.','B max 49 B ≈ 4.25 ms; ACK max 45 B ≈ 3.91 ms.','Bandwidth is calculated from source, not logic-analyzer measured.','This link carries results, not seven-channel raw audio.'])
        for i,line in enumerate(lines):ax.text(0,.9-i*.115,line,transform=ax.transAxes,fontsize=9.5,va='top')
        fig.text(.1,.025,'数据：2026-11-12真实串口日志与本机资源审计。无同步声源真值；有效控制目标仍为0；未实测物理拔线/冷启动。' if zh else 'Sources: 2026-11-12 recorded telemetry and local resource audit. No acoustic ground truth; valid targets remain zero; no physical unplug/cold-start test.',fontsize=10,color='#455869')
        fig.savefig(destination/f'communication_{lang}.png',dpi=170,facecolor=fig.get_facecolor());plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--private-output',type=Path,required=True)
    args=parser.parse_args();destination=Path(__file__).resolve().parent;project=destination.parents[1]
    data=gather(args.private_output.resolve(),project)
    (destination/'metrics.json').write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    folder=destination/'figures';folder.mkdir(exist_ok=True);figures(data,folder)
    print(json.dumps({'public_metrics':str(destination/'metrics.json'),'trials':[{k:t.get(k) for k in ('id','current_tx','esp_bearings','exact_packets','crc_valid_b_acks','later_pico_ack_confirmations')} for t in data['trials']]},ensure_ascii=False))


if __name__=='__main__':main()

"""Informe HTML autónomo; solo necesita los resultados transportados."""
import base64
import csv
import html
import io
import json
import statistics
from pathlib import Path

from .bench_common import VARIANTS, PROTOCOL, new_folder, percentile, read_json


def table(headers, rows):
    return '<table><thead><tr>' + ''.join(f'<th>{html.escape(str(x))}</th>' for x in headers) + '</tr></thead><tbody>' + ''.join(
        '<tr>'+''.join(f'<td>{html.escape(str(x))}</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table>'


def embedded(path):
    mime='image/png' if Path(path).suffix=='.png' else 'image/jpeg'
    return f'<img src="data:{mime};base64,{base64.b64encode(Path(path).read_bytes()).decode()}" alt="Resultado del benchmark">'


def compare(inputs, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    dest=new_folder(output,'comparison')
    groups={};excluded=[]
    for folder in inputs:
        folder=Path(folder).resolve();record=read_json(folder/'result.json')
        if not record.get('official') or record.get('status')!='finished':
            excluded.append(f'{folder.name}: diagnóstico o ejecución incompleta; excluida.')
            continue
        if any(len(m['repetitions'])!=3 for m in record['models'].values()):
            excluded.append(f'{folder.name}: faltan repeticiones; excluida.');continue
        key=json.dumps([record['bundle_sha'],record['protocol']],sort_keys=True)
        groups.setdefault(key,[]).append((folder,record))
    sections=['<h1>Benchmark OBC · YOLO26n original y optimizado</h1>',
              '<p>Jetson: PyTorch FP32/CUDA frente a TensorRT FP16. Raspberry Pi 5: PyTorch FP32/CPU frente a NCNN/CPU.</p>']
    allrows=[]
    if not groups:
        sections.append('<h2>Sin resultados oficiales</h2><p>Importar las carpetas completas de las plataformas con el comando compare. No hay cifras de rendimiento disponibles.</p>')
    if len(groups)>1:
        sections.append('<p>Se separaron los resultados: difieren los hashes del paquete o el protocolo.</p>')
    for index,items in enumerate(groups.values(),1):
        present={(r['platform'],name) for _,r in items for name in r['models']}
        missing={(p,n) for p in ('jetson','rpi5') for n in VARIANTS}-present
        sections.append(f'<h2>Grupo {index} · {"comparación parcial" if missing else "cuatro configuraciones disponibles"}</h2>')
        if missing: sections.append('<p>Faltan: '+html.escape(', '.join(f'{p}/{n}' for p,n in sorted(missing)))+'</p>')
        sections.append('<p>Paquete SHA-256: <code>'+html.escape(items[0][1]['bundle_sha'])+'</code></p>')
        rows=[]; quality_rows=[]; gallery=[]
        fig,axes=plt.subplots(3,1,figsize=(12,12))
        for folder,record in items:
            for name,model in record['models'].items():
                label=f"{record['platform']} / {name} / {folder.name}"
                reps=model['repetitions'];fps=[r['fps'] for r in reps]
                latency=[]
                for j,rep in enumerate(reps,1):
                    with (folder/name/f'repeat_{j}'/'timings.csv').open() as f:
                        latency.extend(float(r['latency_ms']) for r in csv.DictReader(f))
                    with (folder/name/f'repeat_{j}'/'telemetry.csv').open() as f:
                        telemetry=list(csv.DictReader(f))
                    leg=f'{record["platform"]}/{name} r{j}'
                    axes[0].plot([v['start_seconds'] for v in rep['windows']], [v['fps'] for v in rep['windows']], label=leg)
                    axes[1].plot([float(v['seconds']) for v in telemetry],[float(v['rss_bytes'])/2**20 for v in telemetry],label=leg)
                    temps=[v for v in telemetry if v['temperature_c']]
                    if temps: axes[2].plot([float(v['seconds']) for v in temps],[float(v['temperature_c']) for v in temps],label=leg)
                acc=model['accuracy'];ref=record['reference']['models']['yolo26n']
                baseline = record['models'].get('pytorch')
                base_fps = (sum(r['images'] for r in baseline['repetitions']) /
                            sum(r['elapsed_seconds'] for r in baseline['repetitions'])) if baseline else None
                row=dict(group=index,run=folder.name,platform=record['platform'],model=name,
                         precision=100*acc['precision'],recall=100*acc['recall'],
                         map50=100*acc['map50'],map50_95=100*acc['map50_95'],
                         delta_map50_95_pp=100*(acc['map50_95']-ref['map50_95']),
                         fps=sum(r['images'] for r in reps)/sum(r['elapsed_seconds'] for r in reps),
                         fps_std=statistics.stdev(fps),fps_min=min(fps),fps_max=max(fps),
                         latency_median_ms=percentile(latency,.5),latency_p95_ms=percentile(latency,.95),
                         rss_peak_mib=max(r['rss_peak_bytes'] for r in reps)/2**20)
                row['speedup_vs_pt'] = row['fps']/base_fps if base_fps else None
                row['delta_vs_pt_device_pp'] = 100*(acc['map50_95']-baseline['accuracy']['map50_95']) if baseline else None
                row['rss_saving_vs_pt_percent'] = 100*(1-max(r['rss_peak_bytes'] for r in reps)/max(r['rss_peak_bytes'] for r in baseline['repetitions'])) if baseline else None
                allrows.append(row)
                rows.append([label]+[f'{row[k]:.2f}' if row[k] is not None else 'N/D' for k in ('fps','speedup_vs_pt','fps_std','latency_median_ms','latency_p95_ms','rss_peak_mib','rss_saving_vs_pt_percent')])
                quality_rows.append([label]+[f'{row[k]:.2f}' if row[k] is not None else 'N/D' for k in ('precision','recall','map50','map50_95','delta_vs_pt_device_pp')])
                gallery.append((label,folder/name/'accuracy/annotated',record['gallery']))
                sections.append('<details><summary>'+html.escape(label)+' · entorno y clases</summary><pre>'+html.escape(json.dumps(
                    dict(environment=record['environment'],conditions=record['conditions'],effective=reps[0]['effective'],
                         model_hashes=record['exports']['models'][name]['files'],accuracy=acc,
                         reference=ref,protocol=record['protocol'],caveat=record['caveat'],
                         temperatures=[{'initial':r['sensors_initial'],'final':r['sensors_final'],
                                        'throttle_before':r['throttle_before'],'throttle_after':r['throttle_after']} for r in reps]),
                    indent=2,ensure_ascii=False))+'</pre></details>')
        sections.append('<h3>Calidad de detección</h3>'+table(['Configuración','Precisión %','Recall %','mAP50 %','mAP50–95 %','Δ vs .pt en placa (pp)'],quality_rows))
        sections.append('<h3>Rendimiento</h3>'+table(['Configuración','FPS','Aceleración ×','DE FPS','Latencia p50 ms','p95 ms','Pico RSS MiB','Ahorro RSS %'],rows))
        for ax,ylabel in zip(axes,['FPS desde archivos','RSS del proceso (MiB)','Temperatura máxima sensores (°C)']):
            ax.set(xlabel='Segundos desde inicio de repetición',ylabel=ylabel)
            ax.grid(alpha=.2)
            if ax.lines: ax.legend(fontsize=6,ncol=2)
        fig.tight_layout();plot=dest/f'grupo_{index}.png';fig.savefig(plot,dpi=150);plt.close(fig)
        sections.append(embedded(plot))
        sections.append('<h3>Mismas doce imágenes · referencia y predicciones</h3>')
        for image in items[0][1]['gallery']:
            sections.append('<details><summary>'+html.escape(Path(image).name)+'</summary>')
            for label,folder,_ in gallery:
                path=folder/Path(image).name
                sections.append('<h4>'+html.escape(label)+'</h4>')
                sections.append(embedded(path) if path.exists() else '<p>Imagen anotada no disponible.</p>')
            sections.append('</details>')
    if allrows:
        with (dest/'comparacion.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=list(allrows[0]));writer.writeheader();writer.writerows(allrows)
    sections+=['<h2>Alcance de las mediciones</h2>',
        '<p>FPS incluye lectura y decodificación local, preprocesamiento, inferencia y postprocesamiento. No incluye cámara, dibujo ni escritura de imágenes. La latencia empieza con la imagen decodificada. DE: desviación estándar entre tres repeticiones. Los percentiles reúnen las muestras de las tres repeticiones.</p>',
        '<p>RSS incluye el proceso Python y sus bibliotecas; no equivale a memoria exclusiva de la red. La memoria de CPU/GPU de Jetson es compartida: no se suman esos contadores. Los picos se muestrean cada 200 ms y pueden omitir eventos más breves. Los sensores ausentes figuran como null.</p>',
        '<p>mAP corresponde al evaluador Ultralytics sobre 300 imágenes de test-dev, no al evaluador oficial VisDrone ni al split completo. Parte de test-dev fue observada durante el entrenamiento de YOLO26. La comparación entre placas incluye diferencias de hardware, motor y precisión numérica.</p>']
    if excluded: sections.append('<h2>Entradas excluidas</h2>'+''.join('<p>'+html.escape(x)+'</p>' for x in excluded))
    page='<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Benchmark OBC</title><style>body{font:16px system-ui;max-width:1300px;margin:40px auto;padding:0 24px;color:#182536}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:9px;border-bottom:1px solid #ccc;text-align:left}img{max-width:100%}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f4f7;padding:16px}details{margin:14px 0}summary{cursor:pointer}code{overflow-wrap:anywhere}</style>'+''.join(sections)+'</html>'
    target=dest/'informe.html';target.write_text(page,encoding='utf-8')
    return target

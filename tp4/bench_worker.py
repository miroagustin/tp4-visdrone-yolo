"""Trabajos aislados: exportación, inferencia medida, evaluación y anotación."""
import csv
import json
import shutil
import subprocess
import threading
import time
from pathlib import Path

from .bench_common import (PROTOCOL, artifact_files, command, dataset_yaml, file_text,
                           percentile, write_json)


def sensors():
    import psutil
    temperatures = {}
    for folder in Path('/sys/class/thermal').glob('thermal_zone*'):
        try:
            temperatures[file_text(folder / 'type') or folder.name] = float(file_text(folder / 'temp')) / 1000
        except (TypeError, ValueError):
            pass
    try:
        frequency = psutil.cpu_freq()
    except (NotImplementedError, OSError):
        frequency = None
    return dict(temperatures=temperatures, temperature_c=max(temperatures.values(), default=None),
                cpu_mhz=frequency.current if frequency else None,
                ram_available_bytes=psutil.virtual_memory().available,
                swap_used_bytes=psutil.swap_memory().used)


class Monitor:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.stop = threading.Event()
        self.peak = 0
        self.error = None
        self.tegrastats = None

    def __enter__(self):
        if shutil.which('tegrastats'):
            self.raw = (self.folder / 'tegrastats.txt').open('w')
            self.tegrastats = subprocess.Popen(['tegrastats', '--interval', '200'], stdout=self.raw, stderr=self.raw)
        self.thread = threading.Thread(target=self.sample, daemon=True)
        self.thread.start()
        return self

    def sample(self):
        import psutil
        process = psutil.Process()
        start = time.perf_counter()
        try:
            with (self.folder / 'telemetry.csv').open('w', newline='') as f:
                fields = ['seconds', 'rss_bytes', 'ram_available_bytes', 'swap_used_bytes', 'temperature_c', 'cpu_mhz']
                writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
                while True:
                    sample = sensors()
                    rss = process.memory_info().rss
                    self.peak = max(self.peak, rss)
                    writer.writerow(dict(seconds=time.perf_counter()-start, rss_bytes=rss,
                                         **{k:sample[k] for k in fields[2:]}))
                    if self.stop.wait(PROTOCOL['sampling_seconds']): break
        except Exception as exc:
            self.error = str(exc)

    def __exit__(self, *args):
        self.stop.set(); self.thread.join(timeout=5)
        if self.tegrastats is not None:
            self.tegrastats.terminate()
            self.tegrastats.wait(timeout=5)
            self.raw.close()


def predictor_for(artifact, platform, folder):
    import cv2
    import torch
    from ultralytics.models.yolo.detect import DetectionPredictor
    torch.set_num_threads(4)
    cv2.setNumThreads(1)
    predictor = DetectionPredictor(overrides=dict(model=str(artifact), device='0' if platform == 'jetson' else 'cpu',
              imgsz=PROTOCOL['imgsz'], batch=1, rect=False, conf=.25, iou=.7, max_det=300,
              save=False, verbose=False, project=str(folder), name='inference', exist_ok=True))
    predictor.setup_model(str(artifact), verbose=False)
    effective = {'backend': type(predictor.model.backend).__name__, 'device': str(predictor.device),
                 'input_fp16': bool(predictor.model.fp16), 'torch_threads': torch.get_num_threads(), 'opencv_threads': 1,
                 'torch_cuda': torch.version.cuda,
                 'gpu': torch.cuda.get_device_name(0) if predictor.device.type == 'cuda' else None,
                 'torch_matmul_tf32': torch.backends.cuda.matmul.allow_tf32,
                 'torch_cudnn_tf32': torch.backends.cudnn.allow_tf32}
    is_pytorch = Path(artifact).suffix == '.pt'
    if is_pytorch and effective['input_fp16']:
        raise RuntimeError('La referencia PyTorch debe utilizar FP32.')
    if platform == 'rpi5' and not is_pytorch:
        net = predictor.model.backend.net
        net.opt.num_threads = 4
        if net.opt.use_vulkan_compute:
            raise RuntimeError('NCNN debe ejecutarse en CPU, sin Vulkan.')
        effective['ncnn_options'] = {k: getattr(net.opt, k) for k in
             ('num_threads','use_vulkan_compute','use_fp16_packed','use_fp16_storage','use_fp16_arithmetic')}
    if platform == 'jetson' and predictor.device.type != 'cuda':
        raise RuntimeError('La ejecución Jetson no está utilizando CUDA.')
    return predictor, effective


def performance(job):
    import cv2
    import psutil
    import torch
    folder = Path(job['output']); cfg = job['protocol']; bundle = Path(job['bundle'])
    process = psutil.Process()
    before = process.memory_info().rss
    predictor, effective = predictor_for(job['artifact'], job['platform'], folder)
    loaded = process.memory_info().rss
    paths = [bundle / x['image'] for x in job['manifest']['images']]
    def predict(picture):
        if job['platform'] == 'jetson': torch.cuda.synchronize()
        begin = time.perf_counter()
        results = predictor(source=picture)
        # Materializar detecciones en CPU es parte de la tarea medida.
        boxes = results[0].boxes.data.cpu().numpy()
        if job['platform'] == 'jetson': torch.cuda.synchronize()
        return (time.perf_counter()-begin)*1000, len(boxes)
    for index in range(cfg['warmup']):
        picture = cv2.imread(str(paths[index % len(paths)]))
        if picture is None: raise ValueError(f'Imagen ilegible: {paths[index % len(paths)]}')
        predict(picture)
    del picture
    initial = sensors()
    throttle_before = command(['vcgencmd', 'get_throttled'])
    latencies, windows = [], {}
    with Monitor(folder) as monitor, (folder / 'timings.csv').open('w', newline='') as f:
        writer = csv.writer(f); writer.writerow(['index','image','elapsed_seconds','latency_ms','detections'])
        start = time.perf_counter(); count = 0
        while time.perf_counter()-start < cfg['seconds']:
            path = paths[count % len(paths)]
            picture = cv2.imread(str(path))
            if picture is None: raise ValueError(f'Imagen ilegible: {path}')
            latency, detections = predict(picture)
            del picture
            elapsed = time.perf_counter()-start
            latencies.append(latency)
            bucket = int(elapsed // cfg['window_seconds'])
            windows[bucket] = windows.get(bucket, 0) + 1
            writer.writerow([count, path.name, elapsed, latency, detections])
            count += 1
        elapsed = time.perf_counter()-start
    if monitor.error:
        raise RuntimeError(f'Falló el muestreo de memoria: {monitor.error}')
    result = dict(images=count, elapsed_seconds=elapsed, fps=count/elapsed,
                  latency_median_ms=percentile(latencies,.5), latency_p95_ms=percentile(latencies,.95),
                  rss_before_load_bytes=before, rss_loaded_bytes=loaded, rss_peak_bytes=monitor.peak,
                  sensors_initial=initial, sensors_final=sensors(),
                  throttle_before=throttle_before, throttle_after=command(['vcgencmd','get_throttled']),
                  tegrastats_available=monitor.tegrastats is not None, effective=effective,
                  windows=[dict(start_seconds=k*cfg['window_seconds'],
                           seconds=min(cfg['window_seconds'],elapsed-k*cfg['window_seconds']),
                           fps=v/min(cfg['window_seconds'],elapsed-k*cfg['window_seconds']))
                           for k,v in sorted(windows.items())],
                  scope='FPS: archivos locales + detección; latencia: imagen decodificada a cajas en CPU.')
    write_json(folder / 'performance.json', result)


def accuracy(job):
    from ultralytics import YOLO
    from .experiment import metrics_dict
    bundle, folder = Path(job['bundle']), Path(job['output'])
    model = YOLO(job['artifact'], task='detect')
    dataset = dataset_yaml(bundle, folder, job['manifest'])
    # quick comprueba inferencia y dibujo; no publica un mAP parcial como oficial.
    if not job.get('quick'):
        result = model.val(data=str(dataset), split='test', imgsz=PROTOCOL['imgsz'], batch=1, rect=False,
                           conf=.001, iou=.7, max_det=300, workers=0, device=job['device'],
                           plots=False, project=str(folder), name='validation', exist_ok=True)
        metrics = metrics_dict(result)
    else:
        metrics = {'diagnostic_only': True}
    if job.get('annotate'):
        from PIL import Image, ImageDraw
        import cv2
        (folder / 'annotated').mkdir(exist_ok=True)
        samples = job['manifest']['images'][:2] if job.get('quick') else job['manifest']['images']
        with (folder / 'predictions.jsonl').open('w', encoding='utf-8') as f:
            for sample in samples:
                path = bundle / sample['image']
                picture = cv2.imread(str(path))
                result = model.predict(picture, imgsz=PROTOCOL['imgsz'], rect=False, conf=.25, iou=.7, max_det=300,
                                       device=job['device'], verbose=False, save=False)[0]
                boxes = result.boxes.data.cpu().tolist()
                f.write(json.dumps(dict(image=sample['image'], xyxy_conf_class=boxes))+'\n')
                predicted = Image.fromarray(result.plot()[:,:,::-1])
                truth = Image.open(path).convert('RGB'); draw = ImageDraw.Draw(truth)
                for line in (bundle / sample['label']).read_text().splitlines():
                    c,x,y,w,h = map(float,line.split()); W,H = truth.size
                    box=((x-w/2)*W,(y-h/2)*H,(x+w/2)*W,(y+h/2)*H)
                    draw.rectangle(box,outline='yellow',width=2)
                    draw.text((box[0],box[1]),job['manifest']['classes'][int(c)],fill='yellow')
                truth.thumbnail((900,650)); predicted.thumbnail((900,650))
                panel=Image.new('RGB',(1800,690),'#182536'); paint=ImageDraw.Draw(panel)
                paint.text((10,8),'Anotaciones de referencia',fill='white')
                paint.text((910,8),f"{job['model']} - predicciones conf >= 0.25",fill='white')
                panel.paste(truth,(0,35));panel.paste(predicted,(900,35))
                panel.save(folder/'annotated'/path.name,quality=85)
    write_json(folder/'accuracy.json', metrics)


def export(job):
    import numpy as np
    from ultralytics import YOLO
    folder=Path(job['output']); bundle=Path(job['bundle'])
    source=folder/f"{job['model']}.pt"
    shutil.copy2(bundle/'models'/source.name,source)
    settings=dict(format='engine' if job['platform']=='jetson' else 'ncnn', imgsz=PROTOCOL['imgsz'], batch=1,
                  device=0 if job['platform']=='jetson' else 'cpu')
    if job['platform']=='jetson': settings.update(quantize=16,dynamic=False,nms=False,workspace=1)
    exported=Path(YOLO(str(source)).export(**settings)).resolve()
    predictor,effective=predictor_for(exported,job['platform'],folder)
    prediction=predictor(source=np.zeros((PROTOCOL['imgsz'],PROTOCOL['imgsz'],3),dtype=np.uint8))[0]
    if prediction.boxes is None: raise RuntimeError('La exportación no produce detecciones válidas.')
    if job['platform']=='jetson' and not effective['input_fp16']:
        raise RuntimeError('El motor TensorRT no tiene entrada FP16 como se solicitó.')
    write_json(folder/'export.json',dict(path=str(exported.relative_to(folder)), settings=settings,
                                        effective=effective,files=artifact_files(exported)))


def worker(job):
    folder=Path(job['output']); folder.mkdir(parents=True,exist_ok=True)
    try:
        {'performance': performance, 'accuracy': accuracy, 'export': export}[job['action']](job)
    except BaseException as exc:
        write_json(folder/'error.json',dict(action=job['action'],error=repr(exc)))
        raise

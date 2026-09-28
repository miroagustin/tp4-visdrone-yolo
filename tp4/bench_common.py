"""Contrato portable y diagnóstico del benchmark OBC (sin importar PyTorch)."""
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# imgsz es la única fuente de la resolución: la usan la referencia, la exportación y las mediciones.
# 1280 px es la configuración por defecto de la misión (ver wiki/mision/objetivo-deteccion-pasada.md).
PROTOCOL = dict(imgsz=1280, batch=1, rect=False, confidence=0.25, iou=0.7,
                max_det=300, warmup=50, repetitions=3, seconds=300,
                pause_seconds=60, window_seconds=10, sampling_seconds=0.2,
                threads=4, accuracy_confidence=0.001)
MODELS = {'yolo26n': '20260928T003017Z'}  # YOLO26n reentrenado con persona y vehículo a 1280 px
VARIANTS = ('pytorch', 'optimized')


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding='utf-8')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def command(args):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=15)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def file_text(path):
    try:
        return Path(path).read_text().strip('\x00\n ')
    except (OSError, UnicodeError):
        return None


def new_folder(parent, label):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    dest = Path(parent).resolve() / f'{label}_{stamp}'
    dest.mkdir(parents=True, exist_ok=False)
    return dest


def doctor():
    import psutil
    packages = {}
    for name in ('ultralytics', 'torch', 'torchvision', 'tensorrt', 'ncnn', 'pnnx', 'numpy', 'psutil', 'onnx', 'onnxslim', 'onnxruntime'):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    if packages['tensorrt'] is None and file_text('/etc/nv_tegra_release'):
        packages['tensorrt'] = command([sys.executable, '-c', 'import tensorrt; print(tensorrt.__version__)'])
    return dict(timestamp=datetime.now(timezone.utc).isoformat(), system=platform.platform(),
                architecture=platform.machine(), python=sys.version, bits=64 if sys.maxsize > 2**32 else 32,
                board=file_text('/proc/device-tree/model'), l4t=file_text('/etc/nv_tegra_release'),
                jetpack=command(['dpkg-query', '-W', 'nvidia-jetpack']),
                power_mode=command(['nvpmodel', '-q']), os_release=file_text('/etc/os-release'),
                ram_bytes=psutil.virtual_memory().total, swap_bytes=psutil.swap_memory().total,
                disk_free_bytes=shutil.disk_usage(Path.cwd()).free, packages=packages,
                git_commit=command(['git', 'rev-parse', 'HEAD']), git_status=command(['git', 'status', '--porcelain']))


def check_platform(target, info=None):
    info = info or doctor()
    if info['bits'] != 64 or info['architecture'].lower() not in ('aarch64', 'arm64'):
        raise RuntimeError('El benchmark oficial requiere Linux ARM64 en la placa objetivo.')
    board = (info.get('board') or '').lower()
    if target == 'rpi5' and 'raspberry pi 5' not in board:
        raise RuntimeError('No se detectó Raspberry Pi 5 en /proc/device-tree/model.')
    if target == 'jetson':
        if not info.get('l4t'):
            raise RuntimeError('No se detectó L4T; instalar el entorno compatible con JetPack.')
        # El orquestador no retiene una segunda instancia de PyTorch en RAM.
        probe = command([sys.executable, '-c',
                         "import torch; assert torch.cuda.is_available(); "
                         "print((torch.ones(8, device='cuda') + 1).sum().item())"])
        if probe != '16.0':
            raise RuntimeError('CUDA no disponible. No se permite fallback a CPU en Jetson.')
    if info['packages']['ultralytics'] != '8.4.162':
        raise RuntimeError('Se requiere ultralytics==8.4.162, la versión de estos checkpoints.')
    return info


def inside(root, relative):
    root = Path(root).resolve()
    result = (root / relative).resolve()
    if not result.is_relative_to(root):
        raise ValueError(f'Ruta fuera del paquete: {relative}')
    return result


def verify_bundle(root):
    root = Path(root).resolve()
    m = read_json(root / 'manifest.json')
    if (m.get('schema') != 1 or m.get('study') != 'yolo26_deployment_v1' or
            set(m.get('models', {})) != set(MODELS) or
            m.get('split') != 'test-dev' or len(m['images']) != 300):
        raise ValueError('Se esperaba el paquete oficial de 300 imágenes de test-dev.')
    if len({x['image'] for x in m['images']}) != 300 or len({x['label'] for x in m['images']}) != 300:
        raise ValueError('Hay imágenes o etiquetas duplicadas en el paquete.')
    if m.get('protocol', {}).get('imgsz') != PROTOCOL['imgsz']:
        raise ValueError(f"El paquete usa {m.get('protocol', {}).get('imgsz')} px y este código {PROTOCOL['imgsz']} px: "
                         'regenerar el paquete con benchmark pack.')
    from .data import MISSION_CLASSES
    if (m.get('classes') != list(MISSION_CLASSES) or
            any(m['models'][name].get('started_utc') != run for name, run in MODELS.items())):
        raise ValueError('El paquete no trae el checkpoint ni las clases (persona y vehículo) de este código: '
                         'regenerar el paquete con benchmark pack.')
    for rel, checksum in m['files'].items():
        path = inside(root, rel)
        if not path.is_file() or sha(path) != checksum:
            raise ValueError(f'Archivo ausente o alterado: {rel}')
    required = [f"models/{name}.pt" for name in MODELS] + ['reference.json']
    required += [x[k] for x in m['images'] for k in ('image', 'label')]
    if any(p not in m['files'] for p in required):
        raise ValueError('El manifiesto no cubre todos los pesos, imágenes y etiquetas.')
    return m, sha(root / 'manifest.json')


def dataset_yaml(bundle, dest, manifest):
    import yaml
    path = Path(dest) / 'dataset.yaml'
    # Solo val/test se usan; train permite satisfacer el esquema de Ultralytics.
    path.write_text(yaml.safe_dump(dict(path=str(Path(bundle).resolve()),
                        train='images/test', val='images/test', test='images/test',
                        names=dict(enumerate(manifest['classes'])))), encoding='utf-8')
    return path


def artifact_files(path):
    path = Path(path)
    if path.is_file():
        return {path.name: sha(path)}
    return {p.relative_to(path).as_posix(): sha(p) for p in sorted(path.rglob('*')) if p.is_file()}


def percentile(values, q):
    ordered = sorted(values)
    if not ordered:
        raise ValueError('No hay muestras')
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    return ordered[lo] + (ordered[min(lo + 1, len(ordered)-1)] - ordered[lo]) * (pos-lo)


def freeze(dest):
    text = command([sys.executable, '-m', 'pip', 'freeze'])
    Path(dest).write_text(text or 'No disponible\n', encoding='utf-8')

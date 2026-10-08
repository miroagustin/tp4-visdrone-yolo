"""python -m tp4.benchmark: preparación y orquestación del bonus OBC."""
import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

from .bench_common import (MODELS, VARIANTS, PROTOCOL, artifact_files, check_platform, dataset_yaml,
                           doctor, freeze, new_folder, read_json, sha, verify_bundle, write_json)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / 'benchmark_artifacts'


def child(job, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    config = folder / 'job.json'
    write_json(config, job)
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4', MKL_NUM_THREADS='4',
               ULTRALYTICS_AUTOINSTALL='false', PYTHONUTF8='1')
    with (folder / 'log.txt').open('w', encoding='utf-8') as log:
        result = subprocess.run([sys.executable, '-m', 'tp4.benchmark', '_worker', str(config)],
                                cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"Falló {job['action']}; revisar {folder / 'log.txt'}")


def pack(args):
    from PIL import Image
    from .data import MISSION_CLASSES
    dest = new_folder(args.output, 'package')
    bundle = dest / 'bundle'
    for rel in ('models', 'images/test', 'labels/test'):
        (bundle / rel).mkdir(parents=True)
    sources = sorted((ROOT / 'data/yolo/images/test').glob('*.jpg'))
    if len(sources) < 300:
        raise ValueError('Faltan imágenes de test-dev preparado: se requieren al menos 300.')
    chosen = random.Random(42).sample(sources, 300)
    images = []
    for source in chosen:
        label = ROOT / 'data/yolo/labels/test' / (source.stem + '.txt')
        if not label.is_file():
            raise FileNotFoundError(label)
        rows = label.read_text().splitlines()
        for row in rows:
            values = row.split()
            if len(values) != 5 or not 0 <= int(values[0]) < len(MISSION_CLASSES):
                raise ValueError(f'Etiqueta inválida: {label}')
            if any(not 0 <= float(v) <= 1 for v in values[1:]) or min(map(float, values[3:])) <= 0:
                raise ValueError(f'Caja inválida: {label}')
        with Image.open(source) as im:
            im.verify()
        with Image.open(source) as im:
            width, height = im.size
        image_rel, label_rel = f'images/test/{source.name}', f'labels/test/{label.name}'
        shutil.copy2(source, bundle / image_rel)
        shutil.copy2(label, bundle / label_rel)
        images.append(dict(image=image_rel, label=label_rel, width=width, height=height, objects=len(rows)))
    provenance = {}
    for name, run_id in MODELS.items():
        run = ROOT / 'runs/full' / run_id
        info = read_json(run / 'run.json')
        if info['status'] != 'finished' or Path(info['settings']['model']).stem != name:
            raise ValueError(f'Checkpoint no aceptado: {run}')
        shutil.copy2(run / 'train/weights/best.pt', bundle / f'models/{name}.pt')
        provenance[name] = info
    manifest = dict(schema=1, study='yolo26_deployment_v1', split='test-dev', seed=42, classes=MISSION_CLASSES, images=images,
                    gallery=[x['image'] for x in images[:12]], protocol=PROTOCOL,
                    models=provenance, source_audit=sha(ROOT / 'data/yolo/labels/test/manifest.json'),
                    caveat='YOLO26 observó imágenes de test-dev durante el seguimiento del entrenamiento.')
    write_json(dest / 'source.json', manifest)
    print('Calculando referencias .pt en procesos separados...', flush=True)
    reference = {}
    for name in MODELS:
        jobdir = dest / f'reference_{name}'
        child(dict(action='accuracy', platform='reference', model=name, artifact=str(bundle / f'models/{name}.pt'),
                   bundle=str(bundle), manifest=manifest, output=str(jobdir), device=args.device,
                   annotate=False), jobdir)
        reference[name] = read_json(jobdir / 'accuracy.json')
    write_json(bundle / 'reference.json', dict(models=reference, environment=doctor()))
    manifest['files'] = {p.relative_to(bundle).as_posix(): sha(p) for p in sorted(bundle.rglob('*'))
                         if p.is_file() and p.suffix != '.cache'}
    write_json(bundle / 'manifest.json', manifest)
    verify_bundle(bundle)
    archive = dest / 'tp4_obc_bundle.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel in [*manifest['files'], 'manifest.json']:
            z.write(bundle / rel, f'bundle/{rel}')
    (dest / 'tp4_obc_bundle.zip.sha256').write_text(sha(archive) + '  tp4_obc_bundle.zip\n')
    print(archive)


def export_models(args):
    manifest, bundle_sha = verify_bundle(args.bundle)
    info = check_platform(args.platform)
    dest = new_folder(args.output, f'exports_{args.platform}')
    write_json(dest / 'doctor.json', info)
    result = dict(schema=1, platform=args.platform, bundle_sha=bundle_sha, models={}, environment=info)
    for name in MODELS:
        jobdir = dest / name
        child(dict(action='export', platform=args.platform, model=name, bundle=str(args.bundle.resolve()),
                   output=str(jobdir)), jobdir)
        artifact = read_json(jobdir / 'export.json')
        artifact['path'] = str((jobdir / artifact['path']).relative_to(dest))
        result['models']['optimized'] = artifact
        original = dest / 'yolo26n.pt'
        shutil.copy2(args.bundle / 'models/yolo26n.pt', original)
        result['models']['pytorch'] = dict(path=original.name, files=artifact_files(original),
                                          settings=dict(format='pt', precision='FP32'))
    write_json(dest / 'exports.json', result)
    freeze(dest / 'requirements.lock.txt')
    print(dest)


def verify_exports(path, target, bundle_sha):
    info = read_json(Path(path) / 'exports.json')
    if info['platform'] != target or info['bundle_sha'] != bundle_sha:
        raise ValueError('Exportación de otra plataforma o paquete.')
    if set(info['models']) != set(VARIANTS):
        raise ValueError('Se requieren las variantes pytorch y optimized de YOLO26.')
    for name in VARIANTS:
        record = info['models'][name]
        from .bench_common import inside
        artifact = inside(path, record['path'])
        if not record['files'] or artifact_files(artifact) != record['files']:
            raise ValueError(f'Modelo exportado alterado: {name}')
        if name == 'pytorch' and artifact.suffix != '.pt':
            raise ValueError('La referencia requiere el checkpoint .pt de YOLO26n.')
        if name == 'optimized' and target == 'jetson' and artifact.suffix != '.engine':
            raise ValueError('Jetson requiere TensorRT .engine')
        if name == 'optimized' and target == 'rpi5' and not artifact.is_dir():
            raise ValueError('Raspberry requiere directorio NCNN')
    return info


def run(args):
    manifest, bundle_sha = verify_bundle(args.bundle)
    info = check_platform(args.platform)
    exports = verify_exports(args.exports, args.platform, bundle_sha)
    if exports['models']['pytorch']['files'].get('yolo26n.pt') != manifest['files']['models/yolo26n.pt']:
        raise ValueError('El .pt de referencia no coincide con el paquete.')
    if info['packages'] != exports['environment']['packages']:
        raise ValueError('Las dependencias cambiaron desde export; volver a exportar en este entorno.')
    if any(info.get(k) != exports['environment'].get(k) for k in ('board', 'l4t', 'architecture')):
        raise ValueError('La plataforma difiere de la que produjo la exportación.')
    dest = new_folder(args.output, f'{args.platform}_{"quick" if args.quick else "official"}')
    protocol = dict(PROTOCOL)
    if args.quick:
        protocol.update(repetitions=1, seconds=5, warmup=2, pause_seconds=0)
    summary = dict(schema=1, status='running', official=not args.quick, platform=args.platform,
                   bundle_sha=bundle_sha, protocol=protocol, environment=info, exports=exports,
                   conditions=dict(power=args.power, cooling=args.cooling), models={},
                   reference=read_json(args.bundle / 'reference.json'), gallery=manifest['gallery'],
                   caveat=manifest['caveat'])
    write_json(dest / 'result.json', summary)
    freeze(dest / 'requirements.lock.txt')
    try:
        measurement = 0
        for rep in range(protocol['repetitions']):
            for name in (list(VARIANTS) if rep % 2 == 0 else list(reversed(VARIANTS))):
                if measurement:
                    print(f"Pausa {protocol['pause_seconds']} s", flush=True)
                    time.sleep(protocol['pause_seconds'])
                measurement += 1
                folder = dest / name / f'repeat_{rep+1}'
                artifact = (args.exports / exports['models'][name]['path']).resolve()
                print(f'{args.platform}: {name}, repetición {rep+1}', flush=True)
                child(dict(action='performance', platform=args.platform, model=name, artifact=str(artifact),
                           bundle=str(args.bundle.resolve()), manifest=manifest, output=str(folder),
                           protocol=protocol), folder)
                record = read_json(folder / 'performance.json')
                summary['models'].setdefault(name, {'repetitions': []})['repetitions'].append(record)
                write_json(dest / 'result.json', summary)
        # Evaluación y dibujo quedan fuera de los procesos de rendimiento.
        for name in VARIANTS:
            folder = dest / name / 'accuracy'
            child(dict(action='accuracy', platform=args.platform, model=name,
                       artifact=str((args.exports / exports['models'][name]['path']).resolve()),
                       bundle=str(args.bundle.resolve()), manifest=manifest, output=str(folder),
                       device='0' if args.platform == 'jetson' else 'cpu', annotate=True,
                       quick=args.quick), folder)
            summary['models'][name]['accuracy'] = read_json(folder / 'accuracy.json')
        summary['status'] = 'finished'
    except BaseException as exc:
        summary.update(status='failed', error=str(exc))
        raise
    finally:
        write_json(dest / 'result.json', summary)
    print(dest)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('pack'); a.add_argument('--device', default='cpu')
    a.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    a = sub.add_parser('doctor'); a.add_argument('--output', type=Path)
    a = sub.add_parser('verify'); a.add_argument('--bundle', type=Path, required=True)
    for name in ('export', 'run'):
        a = sub.add_parser(name)
        a.add_argument('--platform', choices=['jetson','rpi5'], required=True)
        a.add_argument('--bundle', type=Path, required=True)
        a.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
        if name == 'run':
            a.add_argument('--exports', type=Path, required=True)
            a.add_argument('--quick', action='store_true')
            a.add_argument('--power', required=True, help='Alimentación utilizada')
            a.add_argument('--cooling', required=True, help='Refrigeración utilizada')
    a = sub.add_parser('compare'); a.add_argument('results', nargs='*', type=Path)
    a.add_argument('--output', type=Path, required=True)
    a = sub.add_parser('_worker', help='Uso interno: trabajo aislado en un proceso'); a.add_argument('job', type=Path)
    args = p.parse_args()
    if args.command == 'pack': pack(args)
    elif args.command == 'doctor':
        result = doctor()
        if args.output: write_json(args.output, result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.command == 'verify':
        _, checksum = verify_bundle(args.bundle); print(f'Paquete válido: {checksum}')
    elif args.command == 'export': export_models(args)
    elif args.command == 'run': run(args)
    elif args.command == 'compare':
        from .bench_report import compare
        print(compare(args.results, args.output))
    else:
        from .bench_worker import worker
        worker(read_json(args.job))


if __name__ == '__main__':
    main()

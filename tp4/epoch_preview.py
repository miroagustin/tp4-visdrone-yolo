"""Predicciones didácticas por época; nunca utiliza etiquetas de test."""
from __future__ import annotations

import json
import random
import time
import warnings
from pathlib import Path


def select_image(images, seed, epoch):
    return random.Random(f"{seed}:{epoch}").choice(images)


def display_frame(folder, record):
    from IPython.display import Image, Markdown, display
    display(Markdown(
        f"**Época {record['epoch']} · test-dev · {record['image']}**  \n"
        f"Confianza ≥ {record['confidence']:.2f} · {record['detections']} detecciones · pesos EMA"
    ))
    display(Image(filename=str(Path(folder) / record['figure']), width=1000))


class EpochPreview:
    def __init__(self, settings, run):
        self.settings = settings
        self.folder = Path(run) / "epoch_previews"
        # data.py convierte el split oficial test-dev al directorio YOLO test.
        self.images = sorted((Path(settings['data_dir']) / 'yolo' / 'images' / 'test').glob('*.jpg'))
        if not self.images:
            raise FileNotFoundError("La vista por época requiere imágenes de test-dev preparadas.")
        self.confidence = float(settings.get('epoch_preview', {}).get('confidence', .25))
        self.done = set()

    def __call__(self, trainer):
        # Ultralytics repite este evento al evaluar best.pt al final.
        epoch = int(trainer.epoch) + 1
        if epoch in self.done:
            return
        self.done.add(epoch)
        self.folder.mkdir(parents=True, exist_ok=True)
        target = self.folder / f"epoch_{epoch:03d}.json"
        if target.exists():
            return
        try:
            import numpy as np
            import torch
            from PIL import Image
            from ultralytics.models.yolo.detect import DetectionPredictor

            image = select_image(self.images, self.settings['seed'], epoch)
            python_rng, numpy_rng = random.getstate(), np.random.get_state()
            began = time.perf_counter()
            try:
                with torch.random.fork_rng(devices=[]):
                    predictor = DetectionPredictor(overrides={
                        'device': 'cpu', 'imgsz': self.settings['imgsz'],
                        'conf': self.confidence, 'save': False, 'verbose': False,
                        'project': str(self.folder), 'name': 'inference', 'exist_ok': True,
                    })
                    # setup_model copia la red antes de moverla/fusionarla.
                    predictor.setup_model(model=trainer.ema.ema, verbose=False)
                    result = predictor(source=str(image))[0]
                    picture = Image.fromarray(result.plot()[:, :, ::-1])
                    picture.thumbnail((1280, 960))
                    figure = f"epoch_{epoch:03d}.jpg"
                    temporary = self.folder / f"epoch_{epoch:03d}.tmp"
                    picture.save(temporary, format='JPEG', quality=88)
                    temporary.replace(self.folder / figure)
            finally:
                random.setstate(python_rng)
                np.random.set_state(numpy_rng)
            record = {
                'epoch': epoch, 'split': 'test-dev', 'image': image.name,
                'figure': figure, 'confidence': self.confidence,
                'detections': len(result.boxes), 'imgsz': self.settings['imgsz'],
                'seed': self.settings['seed'], 'weights': 'EMA de esta época',
                'device': 'cpu', 'seconds': time.perf_counter() - began,
                'purpose': 'Seguimiento cualitativo; test-dev observado durante el ajuste.',
            }
            temporary = target.with_suffix('.tmp')
            temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
            temporary.replace(target)
            from IPython import get_ipython
            if get_ipython() is not None and getattr(get_ipython(), 'kernel', None) is not None:
                display_frame(self.folder, record)
            else:
                print(f"Vista test-dev · época {epoch}: {self.folder / figure}")
        except Exception as exc:
            error = {'epoch': epoch, 'error': str(exc)}
            (self.folder / f'error_{epoch:03d}.json').write_text(json.dumps(error), encoding='utf-8')
            warnings.warn(f"No se pudo crear la vista de la época {epoch}: {exc}", RuntimeWarning)


def attach_epoch_preview(model, settings, run):
    if settings.get('epoch_preview', {}).get('enabled', False):
        model.add_callback('on_fit_epoch_end', EpochPreview(settings, run))


def show_history(root, run=None, *, watch=False, poll_seconds=5):
    """Acumula imágenes en el output; watch permite observar otro proceso."""
    root = Path(root)
    if run is None:
        candidates = sorted((root / 'runs' / 'full').glob('*/epoch_previews'))
        if not candidates:
            from .notebook_view import space
            space()
            return
        folder = candidates[-1]
    else:
        folder = (root / run).resolve() / 'epoch_previews'
    if folder.exists():
        from IPython.display import Markdown, display
        display(Markdown(f"**Ejecución: `{folder.parent.name}`**"))
    seen = set()
    while True:
        for path in sorted(folder.glob('epoch_*.json')):
            if path.name not in seen:
                display_frame(folder, json.loads(path.read_text(encoding='utf-8')))
                seen.add(path.name)
        if not watch:
            return
        manifest = folder.parent / 'run.json'
        try:
            if json.loads(manifest.read_text(encoding='utf-8')).get('status') in ('finished', 'failed'):
                # Una última lectura recoge la imagen escrita entre el escaneo y el cierre.
                watch = False
                continue
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        time.sleep(max(1, poll_seconds))

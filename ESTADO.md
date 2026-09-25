# Estado verificado del TP4

Fecha local: 24 de septiembre de 2026. Los ID de runs usan UTC y por eso comienzan con `20260925`.

## Entorno

- Windows 11 Home; Python 3.14.4 en `.venv`, kernel Jupyter `tp4-visdrone-yolo` registrado.
- NVIDIA GeForce RTX 5070 Laptop GPU (8151 MiB), driver 610.74; `nvidia-smi` informa soporte CUDA 13.3.
- PyTorch 2.13.0+cu130, torchvision 0.28.0+cu130, Ultralytics 8.4.162. `torch.cuda.is_available()` devolvió `True`; multiplicación matricial en GPU devolvió 32.0.
- Otras versiones comprobadas: OpenCV 5.0.0, Pillow 12.1.1, Matplotlib 3.10.8 y PyYAML 6.0.3. Dependencias restantes fijadas en `requirements.txt`.

## Datos

Descargados los ZIP train, val y test-dev del mirror documentado de Ultralytics. Hashes SHA-256 y tamaños figuran en `data/archives/*.json`; se conservaron originales en `data/raw/`. Las cantidades reales coinciden con las [documentadas](https://docs.ultralytics.com/datasets/detect/visdrone/): train 6471, val 548, test-dev 1610 imágenes, con una anotación por imagen.

| Split | Cajas convertidas | Regiones con score 0 | Cajas inválidas |
|---|---:|---:|---:|
| Train | 343204 | 10345 | 1 |
| Val | 38759 | 1410 | 0 |
| Test-dev | 75102 | 2445 | 0 |

La caja inválida es `9999985_00000_d_0000020.txt:12`: ancho 4 y alto 0. Quedó excluida y registrada en la auditoría. Se revisaron visualmente cajas convertidas sobre tres imágenes de validación; se alinean con los objetos. Los archivos `data/audit.png` y `data/box_review.png` guardan la revisión.

## Pruebas y resultados

- Tres pruebas de conversión, faltantes y reutilización pasaron con `pytest`; la prueba de reutilización también detecta y repara una etiqueta alterada.
- Smoke por CLI: `runs/smoke/20260925T011221Z`, 2 épocas, 128 train / 32 val; completó entrenamiento y validación.
- Notebook ejecutado de arriba abajo con perfil smoke: `runs/smoke/20260925T011344Z`, mismo protocolo, 31,2 segundos de entrenamiento más validación. Guardó `best.pt`, `last.pt`, configuración, versiones, curvas, matriz y predicciones.
- En ese smoke: Precision 0,0050; Recall 0,0134; mAP@0.5 0,00163; mAP@0.5:0.95 0,00093 (Ultralytics en 32 imágenes val). **Son resultados técnicos preliminares, no conclusiones académicas ni cifras oficiales de VisDrone.**
- Galería de ocho imágenes del subconjunto val smoke: 0 verdaderos positivos, 0 falsos positivos y 499 falsos negativos con confianza 0,25 e IoU 0,5. Con ese umbral, el smoke no predijo cajas en esta muestra; la galería ilustra el límite de dos épocas.
- Latencia en RTX 5070 Laptop: 22,67 ms por imagen, batch 1, resolución 640, cinco warm-up y 20 repeticiones de `predict` completo sobre una imagen repetida, con sincronización CUDA.
- El notebook se volvió a ejecutar desde kernel limpio en perfil presentación, sin descarga ni entrenamiento. El HTML autónomo se abrió en Edge mediante Playwright: título correcto, 12 diapositivas y seis imágenes embebidas. Se revisó visualmente la portada.

## Pendiente para la entrega académica

El entrenamiento full de 50 épocas y la evaluación final de test-dev **no se iniciaron**, como se pidió para esta preparación. Tampoco se ejecutó en Colab. Antes de entregar, completar integrantes, lanzar full, analizar métricas y errores de ese run, evaluar test-dev una sola vez y reemplazar las conclusiones condicionales por conclusiones sustentadas. Si se hace la comparación opcional 640/960, registrar explícitamente el batch de cada run.

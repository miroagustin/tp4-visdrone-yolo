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

Durante la preparación inicial no se iniciaron full ni la evaluación final de test-dev. Posteriormente, el usuario informó que ya está entrenando el modelo. La revisión editorial del notebook no inicia cómputo de entrenamiento ni modifica sus datos, checkpoints o configuración. Colab sigue sin ejecución verificada. Antes de entregar, completar integrantes, finalizar full, analizar sus métricas y errores y evaluar test-dev después de fijar el modelo. Si se hace la comparación opcional 640/960, registrar explícitamente el batch de cada run.

## Revisión académica del notebook

Actualización editorial: el notebook se convirtió en un informe académico de entrega. Las instrucciones, guion, controles y notas de trabajo se trasladaron al README. La selección de resultados ahora acepta sólo full terminado; si falta evidencia final, las secciones conservan espacios vacíos, sin usar métricas smoke. Esta versión se ejecutó completa y se regeneró su HTML sin iniciar entrenamiento. Se comprobó que el texto visible no contiene notas de tareas futuras, comandos operativos ni cifras de smoke. Las comprobaciones descritas a continuación corresponden a la revisión anterior.

Se aplicaron los criterios de la skill `jupyter-notebook`: apertura sin estado oculto, celdas enfocadas, objetivo y audiencia, ejercicio guiado, salidas compactas y conclusiones vinculadas a evidencia. Se incorporó el criterio de mensaje, evidencia y alcance de [MIT Communication Lab](https://mitcommlab.mit.edu/nse/commkit/structuring-a-slide-presentation/).

El notebook incluye un guion de nueve minutos, índice con enlaces, tablas de protocolo y métricas en porcentajes, pies de figura y separación entre validación, muestra de errores y test-dev. La exposición carga sólo runs terminados. Los controles de entrenamiento, preparación y diagnóstico están desactivados por defecto y no dependen de variables de entorno antiguas.

Se ejecutó el notebook completo desde un kernel nuevo en modo lectura de artefactos. El exportador ejecutó por separado únicamente las celdas PRESENTACIÓN y produjo 12 diapositivas con dos figuras embebidas; curvas, matriz y lotes completos permanecen en el notebook como respaldo. Se comprobó en Edge con red bloqueada: imágenes cargadas, sin desbordes verticales a 1440×900. Se revisaron visualmente tablas, ejemplos y conclusiones. Las capturas de esta revisión están en `data/notebook_review/`.

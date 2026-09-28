# Bonus TP4: benchmark de YOLO26 original y optimizado en OBC

Esta guía es el handoff para los equipos de Jetson y Raspberry Pi 5 y sus asistentes de IA. Ejecutar los pasos en orden y conservar los registros. El objetivo es medir **FPS sostenidos, latencia, memoria y precisión** del checkpoint YOLO26n del TP, original y optimizado, sin volver a entrenarlos.

| Equipo | Referencia | Optimizado |
|---|---|---|
| Jetson | PyTorch FP32, CUDA | TensorRT FP16, CUDA |
| Raspberry Pi 5 | PyTorch FP32, CPU | NCNN, CPU, cuatro hilos |

Ultralytics recomienda [TensorRT para Jetson](https://docs.ultralytics.com/guides/nvidia-jetson/) y [NCNN para Raspberry Pi](https://docs.ultralytics.com/guides/raspberry-pi/). [NCNN](https://docs.ultralytics.com/integrations/ncnn/) soporta detección con YOLO11 y YOLO26. La recomendación justifica la elección del motor; no prueba cuál de las variantes de YOLO26 será más rápido. Entre placas se comparan soluciones completas: hardware, motor y precisión numérica diferentes.

## 1. Coordinación y paquete común

El coordinador publica el código de este bonus en el repositorio y entrega **el mismo ZIP** a ambos equipos. No subir automáticamente dataset o checkpoints al repositorio. Utilizar los datos con las condiciones académicas de VisDrone documentadas en el README.

En la computadora que contiene los entrenamientos y el dataset preparado, desde `tp4-yolo`:

```powershell
.venv/Scripts/python.exe -m pip install psutil==7.2.2
.venv/Scripts/python.exe -m tp4.benchmark pack --device 0
```

El comando crea un directorio nuevo en `benchmark_artifacts`, imprime la ruta del ZIP y conserva también una carpeta `bundle`. `--device cpu` permite preparar referencias sin CUDA. La creación del paquete evalúa los `.pt`; no los entrena ni los modifica.

Contenido: 300 imágenes únicas de test-dev elegidas sin reemplazo con semilla 42, sus etiquetas, el `best.pt` de YOLO26n, clases, dimensiones, conteo de objetos, orden fijo, doce imágenes de galería, configuración y SHA-256 por archivo. Las rutas son relativas. `reference.json` contiene la evaluación de los `.pt` sobre esta misma muestra, con batch 1, entrada cuadrada 1280 y confianza 0,001. La resolución sale de `PROTOCOL['imgsz']` en `tp4/bench_common.py` (1280 px, la configuración por defecto de la misión); `verify` rechaza un paquete generado con otra resolución.

El checkpoint proviene de `20260928T003017Z`: YOLO26n reentrenado con las clases de la misión (persona y vehículo) a 1280 px. Su hash y manifiesto de entrenamiento acompañan el paquete. **No reemplazar estos pesos por yolo26n.pt descargado de Internet.**

Compartir el ZIP y su archivo `.sha256` por el medio acordado. El paquete original ya se genera localmente; las plataformas no necesitan descargar train, val ni el test completo.

El paquete vigente también está publicado como dos archivos adjuntos en la [release v0.0.1](https://github.com/miroagustin/tp4-visdrone-yolo/releases/tag/v0.0.1): `tp4_obc_bundle.zip` y `tp4_obc_bundle.zip.sha256`. Verificar el checksum antes de extraerlo; no usar los paquetes anteriores de diez clases.

## 2. Inicio en cada plataforma

Se supone Python instalado, acceso al repositorio y al ZIP. La herramienta requiere Python 3.10 o superior; verificar que la combinación elegida sea compatible con JetPack. Instalar paquetes del sistema solo cuando el diagnóstico identifique que faltan.

```bash
git clone https://github.com/miroagustin/tp4-visdrone-yolo.git
cd tp4-visdrone-yolo
git rev-parse HEAD
python3 --version
uname -m
cat /proc/device-tree/model
```

El commit debe incluir `tp4/benchmark.py`. Ambos equipos deben trabajar sobre el mismo commit publicado. Si la carpeta ya existe, actualizar la rama acordada conservando sus cambios locales.

Crear el entorno siguiendo la sección específica de la placa. Luego copiar `tp4_obc_bundle.zip` y su checksum al directorio del proyecto:

```bash
sha256sum -c tp4_obc_bundle.zip.sha256
mkdir -p benchmark_input
python -m zipfile -e tp4_obc_bundle.zip benchmark_input
python -m tp4.benchmark verify --bundle benchmark_input/bundle
python -m tp4.benchmark doctor --output benchmark_artifacts/doctor.json
```

Resultado esperado: checksum correcto, `Paquete válido` y diagnóstico JSON con arquitectura ARM64, Python de 64 bits, memoria y versiones. Un archivo ausente o alterado debe corregirse volviendo a copiar el paquete, no editando el manifiesto.

El diagnóstico no importa PyTorch y puede realizarse antes de instalar los motores, una vez instalado `psutil`. Los valores `null` indican información no disponible, no cero consumo.

## 3. Jetson: entorno y TensorRT

Identificar la placa y el sistema antes de elegir paquetes:

```bash
cat /etc/nv_tegra_release
dpkg-query -W nvidia-jetpack
nvpmodel -q
```

`nvidia-jetpack` puede no estar registrado aunque L4T esté instalado. Conservar ambos resultados. Consultar la [instalación oficial de PyTorch para Jetson](https://docs.nvidia.com/deeplearning/frameworks/install-pytorch-jetson-platform/index.html) y la [guía Ultralytics por versión de JetPack](https://docs.ultralytics.com/guides/nvidia-jetson/). Elegir PyTorch, torchvision y TensorRT compatibles con el JetPack detectado. **No instalar las ruedas CUDA de Windows/x86 ni actualizar drivers o JetPack automáticamente.**

Si PyTorch y TensorRT compatibles están instalados por el sistema, el entorno puede exponerlos:

```bash
python3 -m venv --system-site-packages .venv-obc
source .venv-obc/bin/activate
python -m pip install psutil==7.2.2
python -m tp4.benchmark doctor --output benchmark_artifacts/doctor-before.json
python -c "import torch, torchvision, tensorrt; print(torch.__version__, torchvision.__version__, tensorrt.__version__); assert torch.cuda.is_available(); print((torch.ones(8, device='cuda') + 1).sum().item())"
```

Esperado: importaciones correctas, CUDA disponible y `16.0`. Si falta algún paquete, instalar la combinación oficial correspondiente a JetPack. Si no existe una combinación compatible con Python y Ultralytics 8.4.162, informar el bloqueo y el diagnóstico al coordinador; no cambiar de backend para obtener cifras.

Proteger las versiones de PyTorch al instalar el resto:

```bash
python -c "import importlib.metadata as m; print('\n'.join(n+'=='+m.version(n) for n in ('torch','torchvision')))" > .venv-obc/torch-constraints.txt
python -m pip install -r requirements-benchmark.txt -c .venv-obc/torch-constraints.txt
```

Instalar además las dependencias de exportación ONNX que requiere la versión fijada de Ultralytics, conservando las restricciones anteriores:

```bash
python -m pip install "onnx>=1.12,<2" "onnxslim>=0.1.82" onnxruntime -c .venv-obc/torch-constraints.txt
python -m pip check
```

ONNX es un paso intermedio para TensorRT; ONNX Runtime CPU puede utilizarse durante la simplificación y no se mide como otra configuración. Consultar [exportación TensorRT](https://docs.ultralytics.com/integrations/tensorrt/) para requisitos adicionales del TensorRT instalado. El runner desactiva instalaciones automáticas: un faltante queda en el log para resolverlo explícitamente.

```bash
python -m tp4.benchmark export --platform jetson --bundle benchmark_input/bundle
```

La salida es una carpeta `exports_jetson_FECHA`. Contiene el motor y una copia del .pt original, hashes, parámetros, prueba de carga/inferencia y `requirements.lock.txt`. Los motores se construyen en esta Jetson para su entorno; no copiar un `.engine` de la laptop. Se usa FP16, entrada fija 1280 × 1280 y batch 1. Si CUDA, TensorRT o FP16 fallan, corregir el entorno según el log; no sustituir CPU silenciosamente.

## 4. Raspberry Pi 5: entorno y NCNN

Se requiere sistema ARM64 y Python de 64 bits. Si `uname -m` muestra un sistema de 32 bits, detener este procedimiento y acordar la preparación de un sistema de 64 bits.

```bash
python3 -m venv .venv-obc
source .venv-obc/bin/activate
python -m pip install -r requirements-benchmark.txt
python -m pip install ncnn pnnx==20260526
python -m pip check
python -m tp4.benchmark doctor --output benchmark_artifacts/doctor.json
python -m tp4.benchmark export --platform rpi5 --bundle benchmark_input/bundle
```

PyTorch CPU se usa para exportar y para medir la referencia .pt. Cada medición carga exclusivamente su variante, PyTorch o NCNN. Ante ausencia de ruedas compatibles, revisar Python/ARM64 y la [guía de instalación oficial](https://docs.ultralytics.com/guides/raspberry-pi/); registrar cualquier dependencia del sistema agregada. No cambiar la versión de Ultralytics sin coordinar un protocolo nuevo.

Esperado: carpeta `exports_rpi5_FECHA` con el modelo NCNN, una copia del .pt original, metadatos y prueba de inferencia. Se fuerza CPU, cuatro hilos NCNN y Vulkan desactivado. Se conservan las opciones por defecto de FP16 de NCNN, registrando sus valores efectivos. Un archivo de pesos FP32 no implica que toda la aritmética se ejecute en FP32.

## 5. Prueba corta y benchmark oficial

Reemplazar `EXPORTS` por la carpeta impresa al exportar y `PLATAFORMA` por `jetson` o `rpi5`. Usar descripciones reales de alimentación y refrigeración:

```bash
python -m tp4.benchmark run --platform PLATAFORMA --bundle benchmark_input/bundle --exports EXPORTS --quick --power "fuente utilizada" --cooling "refrigeración utilizada"
```

La prueba corta realiza dos calentamientos y cinco segundos por modelo, genera dos imágenes anotadas y no calcula mAP. Debe terminar con `status: finished`. Se etiqueta como diagnóstico y el comparador la excluye de cifras oficiales.

Después de verificar la prueba corta:

```bash
python -m tp4.benchmark run --platform PLATAFORMA --bundle benchmark_input/bundle --exports EXPORTS --power "fuente utilizada" --cooling "refrigeración utilizada"
```

Protocolo fijo:

- Tres repeticiones de cinco minutos por modelo, 50 imágenes de calentamiento por repetición. Orden PyTorch/optimizado, optimizado/PyTorch, PyTorch/optimizado y 60 segundos entre procesos. Reservar al menos 35 minutos más exportación, calentamientos y evaluación.
- Una imagen a la vez desde disco, batch 1, letterbox cuadrado 1280, confianza 0,25 y máximo de 300 detecciones. NMS IoU 0,7 cuando la arquitectura lo utiliza; no imponer NMS a la salida end-to-end de YOLO26.
- Los FPS incluyen lectura, decodificación y detección completa. La latencia empieza después de decodificar y termina con las cajas materializadas en CPU. CUDA se sincroniza. No hay dibujo ni guardado de imágenes en este intervalo. La referencia PyTorch usa FP32; TensorRT usa FP16. Su diferencia combina efectos del motor y la precisión numérica.
- El mismo orden de 300 imágenes se repite cíclicamente. No hay caché Python del dataset completo; puede existir caché de archivos del sistema operativo. No se modifican sus políticas entre modelos.
- RSS antes/después de cargar el modelo y pico muestreado cada 200 ms durante medición; incluye bibliotecas y harness Python. El orquestador no mantiene otro modelo ni PyTorch cargados. Se registran RAM disponible y swap del sistema.
- Temperaturas y frecuencias disponibles se muestrean junto con la memoria. Jetson guarda `tegrastats` si está disponible; Raspberry registra además `vcgencmd get_throttled` al inicio/final. Un sensor ausente se indica como tal. La memoria de CPU y GPU de Jetson es compartida: no sumar contadores como memorias independientes.
- Usar la misma fuente, refrigeración y modo de potencia para ambos modelos. Cerrar aplicaciones ajenas al estudio y conservar esos datos. No modificar `nvpmodel` o clocks entre modelos. Las temperaturas iniciales/finales permiten identificar diferencias térmicas entre repeticiones.

Cada medición utiliza un proceso nuevo que solo carga la variante correspondiente: .pt o modelo optimizado. Nunca se exporta dentro del proceso medido. Si hay un error, queda `status: failed` con su log; se corrige y se lanza una ejecución nueva, sin mezclar repeticiones de intentos distintos. Interrumpir durante las pausas o con Ctrl+C deja resultados incompletos excluidos de la comparación oficial.

## 6. Precisión y resultados que entrega cada equipo

Al terminar las seis mediciones, el runner lanza procesos separados para evaluar y anotar las 300 imágenes. Se calculan mAP50, mAP50–95 y métricas por clase con confianza 0,001. El dibujo de predicciones usa 0,25; el panel incluye anotaciones de referencia a la izquierda y predicciones a la derecha.

Cada carpeta de ejecución contiene:

- `result.json`: estado, protocolo, plataforma, condiciones, métricas y referencias.
- `requirements.lock.txt`: versiones efectivas.
- Por modelo/repetición: `timings.csv`, `telemetry.csv`, `performance.json`, trabajo resuelto y log; `tegrastats.txt` cuando existe.
- Por modelo: `accuracy/accuracy.json`, `predictions.jsonl` e `accuracy/annotated/` con las 300 imágenes.

Las evaluaciones son sobre una muestra fija de test-dev con etiquetas convertidas, no el evaluador oficial VisDrone. Parte de test-dev fue observada en las vistas por época de YOLO26. No modificar checkpoints o hiperparámetros según los resultados del benchmark. Una diferencia de mAP respecto al `.pt` debe investigarse como posible efecto de exportación/precisión, no ocultarse.

Entregar la carpeta oficial completa comprimida y conservar también la carpeta de exportación en la placa:

```bash
python -m zipfile -c resultados_PLATAFORMA.zip benchmark_artifacts/PLATAFORMA_official_FECHA
```

No hace falta incluir el ZIP de entrada ni los motores para visualizar los resultados. La carpeta de exportación conserva los motores y hashes para reproducirlos si se necesitan.

## 7. Comparación conjunta

En una computadora con el repositorio, Python y `matplotlib`, extraer los resultados de ambos equipos y ejecutar desde `tp4-yolo`:

```bash
python -m tp4.benchmark compare RUTA_RESULTADO_JETSON RUTA_RESULTADO_RPI5 --output benchmark_artifacts/reports
```

Se crea una carpeta nueva con `informe.html`, `comparacion.csv` y gráficos PNG. El HTML contiene imágenes embebidas y funciona sin dataset, pesos ni red. Incluye mAP, diferencia contra `.pt` en la misma placa, factor de aceleración, ahorro de RSS, FPS, dispersión entre repeticiones, latencias p50/p95, pico RSS, curvas de memoria/temperatura y la misma galería de doce imágenes.

Con una sola plataforma se muestra **comparación parcial**. Los paquetes/protocolos distintos se separan y los diagnósticos o intentos incompletos se excluyen. Se puede generar una portada honesta sin resultados con:

```bash
python -m tp4.benchmark compare --output benchmark_artifacts/reports
```

El análisis debe discutir el compromiso precisión/velocidad/memoria, sin afirmar superioridad universal ni FPS de cámara. El ahorro de RSS puede ser negativo si la variante optimizada consume más memoria. La referencia PyTorch conserva pesos/entradas FP32; también se registran las opciones TF32 de PyTorch cuando se usa CUDA. No se mide consumo eléctrico; temperatura, RAM y potencia configurada no equivalen a energía por inferencia.

## 8. Aceptación y estado de validación

Antes de entregar, comprobar en cada placa: la referencia .pt y el optimizado cargan, quick termina, seis mediciones oficiales completan, 300 paneles por modelo, métricas y telemetría presentes, hashes comunes y HTML abierto en otra computadora.

Las pruebas locales cubren selección/integridad, rutas portables, cálculos, restricciones y reporte. Las referencias `.pt` del paquete se ejecutan en la computadora del proyecto. **TensorRT en Jetson y NCNN en Raspberry requieren validación real de cada equipo; no se atribuyen resultados de estas placas a la laptop.**

La comparación principal es **YOLO26 original frente a YOLO26 optimizado en cada placa**. YOLO11 queda fuera de este bonus. La referencia local del ZIP sirve para detectar diferencias entre entornos; la ganancia de rendimiento y la variación de calidad se calculan contra el .pt medido en esa misma placa.

### Validación local realizada — 26 de septiembre de 2026; paquete regenerado el 28

- Paquete de esta entrega: `benchmark_artifacts/package_20260928T020732595419Z/tp4_obc_bundle.zip` (aproximadamente 61 MiB, SHA-256 `52e61d052a9063e0b611605eda1e879a061bc53047ef62f806cc5b1c227a1b2f`), YOLO26n reentrenado con persona y vehículo, a 1280 px. Reemplaza a los paquetes anteriores de 10 clases (`package_20260926T215439979200Z` a 1280 px y `package_20260926T172031125947Z` a 640 px), que el código actual ya no acepta. Compartir también el `.sha256` de esa carpeta. Es el paquete **solo YOLO26**, no el paquete preliminar de dos arquitecturas.
- Referencia real del checkpoint sobre la muestra a 1280 px, con las dos clases: mAP50 **57,52 %**, mAP50–95 **32,02 %** (AP50 persona 35,0 %, vehículo 80,0 %), calculada con CUDA en la laptop. Son métricas de estas 300 imágenes, no del conjunto completo de validación.
- ZIP comprobado mediante CRC, extracción a otro directorio temporal y verificación de todos los hashes; se comprobó que la selección de imágenes se reproduce.
- Nueve pruebas automatizadas pasaron: alteraciones/ausencias/duplicados, checkpoint y clases del paquete, rutas, percentiles, rechazo de plataformas y formatos, exclusión de diagnósticos y comparación agrupada con datos sintéticos de prueba.
- Se ejecutaron procesos reales de inferencia en CPU y anotación de dos imágenes en Windows, marcados como diagnóstico local. No se presentaron como cifras de Raspberry o Jetson.
- El HTML sin resultados de placas se abrió en Edge sin solicitudes de red. La comparación con tablas y gráficos se comprobó con fixtures sintéticas en directorios temporales de tests.
- La exportación y las mediciones físicas de TensorRT/NCNN corresponden a los equipos de las placas; aún no se han ejecutado aquí.

### Resultado real en Raspberry Pi 5 — 28 de septiembre de 2026

- Sobre el commit `c1ed7e7` y el paquete vigente, el benchmark oficial terminó con tres mediciones de cinco minutos por variante y 300 paneles anotados por modelo. La fuente fue USB-C Power Delivery de 33 W y la refrigeración, un disipador con ventilador.
- PyTorch FP32/CPU: **0,911 FPS**, mAP50 **57,50 %**, mAP50–95 **32,00 %**. NCNN/CPU con cuatro hilos: **3,110 FPS**, mAP50 **57,41 %**, mAP50–95 **31,72 %**. NCNN aceleró **3,41 veces** y perdió **0,276 puntos porcentuales** de mAP50–95 frente al `.pt` en la misma placa.
- La temperatura máxima muestreada fue **69,4 °C** y `vcgencmd get_throttled` permaneció en `0x0`. El objetivo operativo de **5 FPS** no se alcanzó en esta Raspberry. La evaluación usa `max_det=300`, aunque una imagen contiene 333 objetos; esto puede limitar el recall medido.
- Evidencia versionada: [resultado JSON](analysis/benchmark_rpi5_result.json), [comparación CSV](analysis/benchmark_rpi5.csv), [entorno Python](analysis/benchmark_rpi5_requirements.txt), [checksum del ZIP](resultados_rpi5.zip.sha256) y [análisis en la wiki](wiki/obc/benchmark.md). El [ZIP completo y el informe HTML](https://github.com/alanblanco3223/tp4-visdrone-yolo/releases/tag/v0.0.2-rpi5) se adjuntan a la release por su tamaño. Jetson sigue pendiente.

# OMNI Agro — MVP de censo de plantas por dron (ApexCorp)

Dashboard funcional de **visión computacional para agricultura** sobre video
real de dron. Detecta y **cuenta plantas con YOLO26-UAV + ByteTrack**, y
entrega, con **datos reales** del procesamiento (no simulados):

- **Conteo de plantas únicas** del sobrevuelo (tracking evita contar doble).
- **Presión de maleza** (% de lo detectado que es maleza — clases crop/weed).
- **Despoblamiento**: huecos de siembra por grilla sobre las hileras
  (heurística *experimental*, celdas huecas pintadas en rojo sobre el video).
- **ROI de lote** dibujable (opcional): solo se analiza lo de adentro.
- **Alertas** reales (presión de maleza alta, despoblamiento sostenido).
- **Exportación a CSV** de todo el reporte.

> **Modelo:** YOLO26 entrenado en imágenes UAV con clases `crop`/`weed`
> (HuggingFace `smAIL-WS/uav_weed_detection`) — no se entrena desde 0.
> **Aceleración:** CUDA (RTX 3060), ~36 fps de inferencia a 640px.
> Alternativa en la UI: YOLO-World open-vocabulary (vegetación por nombre).

## 1. Instalar

Este MVP **comparte el mismo Python global** que `first_mvp_ppe` y
`first_mvp_tranking` (ya trae torch CUDA, ultralytics y supervision).
**No hay nada nuevo que instalar.**

```bash
cd first_mvp_agro
python download_models.py          # pesos (53 MB) + videos de dron de muestra
python download_models.py --no-video   # solo pesos
```

## 2. Ejecutar

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8020
# o doble clic en arrancar.bat
```

Abre <http://localhost:8020>, elige un video, (opcional) dibuja el ROI del
lote, elige el módulo (conteo / malezas / despoblamiento) y pulsa **Procesar**.

### Modo headless (sin servidor)

```bash
python run_video.py videos/plantacion_top.mp4                 # video anotado + CSV en outputs/
python run_video.py videos/plantacion_top.mp4 --max-frames 100 --class-mode cultivo
```

## 3. Módulos (pestañas de la UI)

| Módulo | Qué mide | Modo de clases |
| ------ | -------- | -------------- |
| **01 Conteo de plantas** | Plantas únicas del sobrevuelo + promedio/pico por frame | `cultivo` (toda detección = planta) |
| **02 Malezas** | Presión de maleza (% del total detectado) | `modelo` (crop/weed del modelo) |
| **03 Despoblamiento** | % de celdas sin planta en hileras cultivadas | `cultivo` |

**¿Por qué dos modos de clases?** El modelo distingue `crop`/`weed` según el
cultivo con el que fue entrenado. En cultivos que no conoce (arándano, cítrico,
palto) puede clasificar el cultivo como "weed"; el modo `cultivo` ignora la
clase y cuenta todo como planta, que es lo correcto para censo y huecos.

## 4. Ajustes (`.env`)

| Clave | Descripción |
| ----- | ----------- |
| `DETECTOR` | `agro` (YOLO26 UAV) o `world` (YOLO-World) |
| `DEVICE` | `cuda:0` o `cpu` |
| `DEFAULT_CONF` | Confianza de detección (0.05 — el slider de la UI la sobreescribe) |
| `CLASS_MODE` | `modelo` o `cultivo` (la pestaña de la UI la sobreescribe) |
| `GRID_COLS` | Columnas de la grilla de despoblamiento (14) |
| `ROW_OCCUPIED_FRAC` | % de celdas ocupadas para considerar la hilera cultivada (0.6) |
| `GAP_ALERT_PCT` / `WEED_ALERT_PCT` | Umbrales de alerta (%) |
| `FRAME_STRIDE` | 1 = todos los frames; 2-3 = más rápido |

## 5. Cómo se calculan las métricas

- **Plantas únicas**: cada track de ByteTrack visto ≥ `MIN_TRACK_FRAMES` frames
  cuenta una vez. Con el dron avanzando, es un **estimado** (los re-ID pueden
  duplicar; se mitiga con `TRACK_LOST_BUFFER` corto).
- **Presión de maleza**: `malezas / (plantas + malezas)` por frame, suavizado (EMA).
- **Despoblamiento**: grilla de `GRID_COLS` columnas; una celda es **hueco** si
  está vacía pero su fila o columna de grilla está mayormente cultivada
  (≥ `ROW_OCCUPIED_FRAC`). % suavizado con EMA. Documentado como experimental.

## 6. Videos de prueba

Los de `download_models.py` vienen de Pexels (libres). El mejor para demo es
**plantacion_top.mp4** (vista cenital de huerto en hileras). Para videos ideales
generados con IA, ver `PROMPTS_VIDEOS_IA.md`.

> Regla de oro: el video debe ser **cenital** (cámara mirando hacia abajo),
> 10–40 m de altura, con plantas individuales distinguibles. Tomas oblicuas al
> horizonte o muy altas no funcionan.

## 7. Limitaciones conocidas (MVP)

- El conteo único es estimado (sin georreferencia ni stitching de ortomosaico).
- El modelo UAV cubre bien cultivos en hilera vistos desde arriba; en cultivos
  muy distintos usar el modo `cultivo` y/o el detector `world`.
- Palmeras/árboles muy grandes aún no tienen modelo confiable (se evaluó
  RT-DETR de palmeras y se descartó por falsos positivos).

"""Carga de configuración desde .env — OMNI Agro (conteo de plantas por dron)."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _f(key, default):
    return float(os.getenv(key, default))


def _i(key, default):
    return int(os.getenv(key, default))


def _b(key, default):
    return os.getenv(key, str(default)).strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Config:
    # modelo
    detector: str = os.getenv("DETECTOR", "agro").lower()   # agro | world
    agro_model: str = os.getenv("AGRO_MODEL", "weights/uav_weed_yolo26.pt")
    yolo_world_model: str = os.getenv(
        "YOLO_WORLD_MODEL",
        r"C:/Users/USER/Desktop/ACCESORIO/Pixel-Civik/vision-node/server/shoplifting/yolov8s-world.pt")
    # clases open-vocabulary para YOLO-World (las que contengan "weed"/"maleza"
    # se cuentan como maleza; el resto como planta de cultivo)
    world_classes: list = field(default_factory=lambda: [
        c.strip() for c in os.getenv(
            "WORLD_CLASSES", "green plant,bush,tree,weed").split(",") if c.strip()])
    # cómo interpretar las clases del modelo:
    #   modelo  = respeta crop/weed del modelo (útil para presión de maleza)
    #   cultivo = toda detección cuenta como planta (útil para conteo/despoblamiento
    #             en cultivos que el modelo no conoce y clasifica mal)
    class_mode: str = os.getenv("CLASS_MODE", "modelo").lower()
    device: str = os.getenv("DEVICE", "cuda")
    work_res: int = _i("WORK_RES", 640)       # imgsz de inferencia (múltiplo de 32)
    default_conf: float = _f("DEFAULT_CONF", 0.05)   # el modelo UAV puntúa bajo en video real
    world_conf: float = _f("WORLD_CONF", 0.05)
    nms_iou: float = _f("NMS_IOU", 0.45)      # fusiona cajas dobles de una misma planta

    # tracking (ByteTrack) — dron en movimiento: buffer corto, matching laxo
    track_activation: float = _f("TRACK_ACTIVATION", 0.05)
    track_lost_buffer: int = _i("TRACK_LOST_BUFFER", 30)
    track_min_match: float = _f("TRACK_MIN_MATCH", 0.60)
    # eleva la confianza de las detecciones (ya filtradas por el slider) antes
    # del tracker: ByteTrack exige score alto para INICIAR tracks y el modelo
    # UAV puntúa bajo — sin esto solo ~15% de las plantas se trackean
    track_boost: bool = _b("TRACK_BOOST", True)
    min_track_frames: int = _i("MIN_TRACK_FRAMES", 3)   # frames para confirmar planta única
    min_box_area_frac: float = _f("MIN_BOX_AREA_FRAC", 0.00005)
    max_box_area_frac: float = _f("MAX_BOX_AREA_FRAC", 0.03)  # descarta cajas gigantes falsas

    # procesamiento
    frame_stride: int = _i("FRAME_STRIDE", 1)
    max_width: int = _i("MAX_WIDTH", 1280)
    jpeg_quality: int = _i("JPEG_QUALITY", 80)

    # despoblamiento (grilla sobre el frame / ROI)
    grid_cols: int = _i("GRID_COLS", 14)          # columnas de la grilla de análisis
    row_occupied_frac: float = _f("ROW_OCCUPIED_FRAC", 0.6)  # % de celdas con planta para considerar la hilera "cultivada"
    gap_alert_pct: float = _f("GAP_ALERT_PCT", 15)           # % de huecos que dispara alerta
    gap_alert_sustain_sec: float = _f("GAP_ALERT_SUSTAIN_SEC", 2.0)

    # malezas
    weed_alert_pct: float = _f("WEED_ALERT_PCT", 25)         # presión de maleza (%) que alerta
    weed_alert_sustain_sec: float = _f("WEED_ALERT_SUSTAIN_SEC", 2.0)

    # servidor
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = _i("PORT", 8020)
    videos_dir: str = os.getenv("VIDEOS_DIR", "videos")
    data_dir: str = os.getenv("DATA_DIR", "data")

    @property
    def videos_abs(self) -> Path:
        p = Path(self.videos_dir)
        return p if p.is_absolute() else ROOT / p

    @property
    def data_abs(self) -> Path:
        p = Path(self.data_dir)
        return p if p.is_absolute() else ROOT / p


config = Config()
config.data_abs.mkdir(parents=True, exist_ok=True)
config.videos_abs.mkdir(parents=True, exist_ok=True)

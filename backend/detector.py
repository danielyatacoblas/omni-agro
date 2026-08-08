"""Detectores intercambiables → detecciones Supervision (0=planta, 1=maleza).

Backends (seleccionables en runtime desde la UI):
  - agro  : YOLO26 entrenado en imágenes UAV (clases crop/weed) — DEFAULT.
            Detecta plantas de cultivo y malezas vistas desde dron.
  - world : YOLO-World (open-vocabulary) — detecta vegetación por nombre
            (green plant, bush, tree, weed…). Fallback flexible para cultivos
            que el modelo agro no conozca.

Ambos devuelven class_id normalizado: 0 = planta de cultivo, 1 = maleza.
Ambos aplican NMS class-agnostic (fusiona cajas dobles → menos IDs falsos).
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import supervision as sv

from .config import config

if config.device.lower() == "cpu":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

ROOT = Path(__file__).resolve().parent.parent

KINDS = ("agro", "world")
LABELS = {
    "agro": "AgroUAV · cultivo + maleza (dron)",
    "world": "YOLO-World · vegetación por nombre",
}


def _round_res(x: int, base: int = 32) -> int:
    x = max(base * 7, int(x))
    return int(round(x / base) * base)


def _nms(dets):
    if dets is not None and len(dets):
        try:
            return dets.with_nms(threshold=config.nms_iou, class_agnostic=True)
        except Exception:
            pass
    return dets


def _dev():
    import torch
    return 0 if (config.device.lower().startswith("cuda")
                 and torch.cuda.is_available()) else "cpu"


def _normalize_classes(dets):
    """class_id → 0 (planta) / 1 (maleza) según el nombre de la clase."""
    if dets is None or len(dets) == 0:
        return dets
    names = None
    if dets.data is not None:
        names = dets.data.get("class_name")
    if names is not None:
        dets.class_id = np.array(
            [1 if ("weed" in str(n).lower() or "maleza" in str(n).lower()) else 0
             for n in names], dtype=int)
    return dets


class Detector:
    def __init__(self, kind: str):
        self.kind = kind if kind in KINDS else "agro"
        self.resolution = _round_res(config.work_res)
        if self.kind == "agro":
            self._init_agro()
        else:
            self._init_world()

    # ── YOLO26 UAV cultivo/maleza ──
    def _init_agro(self):
        from ultralytics import YOLO
        p = Path(config.agro_model)
        if not p.is_absolute():
            p = ROOT / config.agro_model
        if not p.exists():
            raise FileNotFoundError(
                f"no se encontró {p} — ejecuta: python download_models.py")
        self.model = YOLO(str(p))
        self.device = _dev()
        self.variant = p.stem

    def _infer_agro(self, frame, conf):
        r = self.model.predict(frame, conf=conf, device=self.device,
                               imgsz=self.resolution, verbose=False)[0]
        return _normalize_classes(_nms(sv.Detections.from_ultralytics(r)))

    # ── YOLO-World vegetación ──
    def _init_world(self):
        from ultralytics import YOLO
        mp = config.yolo_world_model
        p = Path(mp)
        if not p.exists() and not p.is_absolute():
            p = ROOT / mp
        self.model = YOLO(str(p) if p.exists() else "yolov8s-worldv2.pt")
        try:
            self.model.set_classes(list(config.world_classes))
        except Exception as e:
            print(f"[detector] YOLO-World set_classes falló: {e}")
        self.device = _dev()
        self.variant = "yolo-world"

    def _infer_world(self, frame, conf):
        r = self.model.predict(frame, conf=max(conf, config.world_conf),
                               device=self.device, imgsz=self.resolution,
                               verbose=False)[0]
        return _normalize_classes(_nms(sv.Detections.from_ultralytics(r)))

    # ── API común ──
    def infer(self, frame, conf: float):
        if self.kind == "agro":
            return self._infer_agro(frame, conf)
        return self._infer_world(frame, conf)


# ── caché por tipo + estado de "warmed" ──
_cache: dict[str, Detector] = {}
_warmed: set[str] = set()


def get_detector(kind: str | None = None) -> Detector:
    kind = (kind or config.detector or "agro").lower()
    if kind not in KINDS:
        kind = "agro"
    if kind not in _cache:
        _cache[kind] = Detector(kind)
    return _cache[kind]


def mark_warmed(kind: str):
    _warmed.add(kind)


def is_warmed(kind: str | None = None) -> bool:
    kind = (kind or config.detector or "agro").lower()
    return kind in _warmed

"""Persistencia y geometría del ROI (área de análisis) por video.

Las coordenadas se guardan NORMALIZADAS (0..1) para ser independientes de la
resolución. El ROI es opcional: sin ROI se analiza el frame completo.

Archivo: data/zones/<video>.json
{
  "video": "plantacion_top.mp4",
  "zones": [
    {"id":"r1","name":"Lote A","type":"roi","color":"#6FA80C",
     "points": [[x,y],[x,y],...]}   # normalizado
  ]
}
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

from .config import config

ZONE_TYPES = ("roi",)


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name)


def zones_dir() -> Path:
    d = config.data_abs / "zones"
    d.mkdir(parents=True, exist_ok=True)
    return d


def zones_path(video: str) -> Path:
    return zones_dir() / f"{_safe(video)}.json"


def load_config(video: str) -> dict:
    p = zones_path(video)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"video": video, "zones": []}


def save_config(video: str, data: dict) -> dict:
    data = dict(data)
    data["video"] = video
    data.setdefault("zones", [])
    for i, z in enumerate(data["zones"]):
        z.setdefault("id", f"r{i+1}")
        z["type"] = "roi"
        z.setdefault("color", "#6FA80C")
        z.setdefault("name", f"Lote {i+1}")
    zones_path(video).write_text(json.dumps(data, indent=2, ensure_ascii=False),
                                 encoding="utf-8")
    return data


def zone_to_px(zone: dict, w: int, h: int) -> np.ndarray:
    pts = [(float(x) * w, float(y) * h) for x, y in zone["points"]]
    return np.array(pts, dtype=np.int32)

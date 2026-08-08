#!/usr/bin/env python3
"""Descarga los pesos del modelo agro (HuggingFace) y videos de dron de muestra
(Pexels, licencia libre).

Uso:
    python download_models.py            # pesos + videos de muestra
    python download_models.py --no-video # solo pesos
    python download_models.py --only-video
"""
from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
WEIGHTS = ROOT / "weights"
VIDEOS = ROOT / "videos"
WEIGHTS.mkdir(exist_ok=True)
VIDEOS.mkdir(exist_ok=True)

MODEL_URL = ("https://huggingface.co/smAIL-WS/uav_weed_detection/resolve/main/"
             "yolov26_full_dataset.pt")
MODEL_DST = WEIGHTS / "uav_weed_yolo26.pt"

# Videos de dron sobre cultivos (Pexels — libres para pruebas)
VIDEO_URLS = {
    "plantacion_top.mp4":  # cenital de huerto en hileras — el mejor demo
        "https://videos.pexels.com/video-files/8552314/8552314-hd_1920_1080_30fps.mp4",
    "surcos_papa.mp4":     # surcos de papa, vuelo bajo oblicuo
        "https://videos.pexels.com/video-files/26654029/11984836_1080_1920_30fps.mp4",
    "cultivo_hileras.mp4": # maíz emergente en hileras
        "https://videos.pexels.com/video-files/8859915/8859915-uhd_2560_1440_30fps.mp4",
    "cafetal.mp4":         # cafetal desde dron
        "https://videos.pexels.com/video-files/12493599/12493599-uhd_2732_1440_24fps.mp4",
}


def _fetch(url: str, dst: Path):
    if dst.exists() and dst.stat().st_size > 1e6:
        print(f"  · {dst.name} ya existe ({dst.stat().st_size/1e6:.0f} MB) — omitido")
        return
    print(f"  ↓ {dst.name} ...")
    urllib.request.urlretrieve(url, dst)
    print(f"  ✓ {dst.name} ({dst.stat().st_size/1e6:.1f} MB)")


def download_weights():
    print("→ Descargando pesos del modelo agro (YOLO26 UAV crop/weed) ...")
    try:
        _fetch(MODEL_URL, MODEL_DST)
    except Exception as e:
        print(f"  ✗ error: {e}")


def download_videos():
    print("→ Descargando videos de dron de muestra (Pexels) ...")
    for name, url in VIDEO_URLS.items():
        try:
            _fetch(url, VIDEOS / name)
        except Exception as e:
            print(f"  ✗ {name}: {e}")
    print("  (puedes agregar tus propios .mp4 de dron a videos/)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--only-video", action="store_true")
    a = ap.parse_args()
    if not a.only_video:
        download_weights()
    if not a.no_video:
        download_videos()
    print("\nListo. Arranca el servidor con:  uvicorn backend.main:app --port 8020")


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Procesa un video de dron en modo headless (sin servidor) y deja el MP4
anotado + CSV en outputs/.

Uso:
    python run_video.py videos/plantacion_top.mp4
    python run_video.py videos/plantacion_top.mp4 --conf 0.15 --detector agro
    python run_video.py videos/plantacion_top.mp4 --max-frames 100   # prueba rápida
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backend.processor import processor

ROOT = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", help="ruta al .mp4")
    ap.add_argument("--conf", type=float, default=None)
    ap.add_argument("--detector", default=None, choices=["agro", "world"])
    ap.add_argument("--class-mode", default=None, choices=["modelo", "cultivo"])
    ap.add_argument("--max-frames", type=int, default=0)
    ap.add_argument("--out", default="outputs")
    a = ap.parse_args()

    from backend.config import config
    p = Path(a.video)
    if not p.is_absolute():
        p = ROOT / a.video
    if not p.exists():
        raise SystemExit(f"no existe: {p}")
    if a.detector:
        processor.detector_kind = a.detector
    if a.class_mode:
        processor.class_mode = a.class_mode
    conf = a.conf if a.conf is not None else config.default_conf

    print(f"→ Procesando {p.name} (conf={conf}, detector={processor.detector_kind})")
    res = processor.process_to_file(str(p), p.name, conf, ROOT / a.out,
                                    max_frames=a.max_frames)
    print(f"\nResumen: plantas={res['plantas']}  malezas={res['malezas']}  "
          f"despoblamiento={res['gap_pct']:.1f}%")
    print(f"Video anotado: {res['video_out']}")
    print(f"CSV: {res['csv']}")


if __name__ == "__main__":
    main()

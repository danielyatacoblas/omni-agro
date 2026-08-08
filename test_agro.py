#!/usr/bin/env python3
"""Pruebas rápidas del MVP Agro (sin servidor).

    python test_agro.py
"""
from __future__ import annotations

import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
OK = FAIL = 0

# Se puede correr de dos maneras y cada una entiende el fallo de forma distinta:
# como script (`python test_agro.py`) el resultado es el código de salida, y
# como suite (`pytest`) tiene que ser una excepción. Imprimir «✗» y seguir deja
# a pytest en verde con todo roto, que es peor que no tener pruebas.
BAJO_PYTEST = "pytest" in sys.modules


def check(name, cond, detail=""):
    global OK, FAIL
    if cond:
        OK += 1
        print(f"  ✓ {name}")
        return
    FAIL += 1
    print(f"  ✗ {name} {detail}")
    if BAJO_PYTEST:
        raise AssertionError(f"{name} {detail}".strip())


def falta(que: str, como: str):
    """Lo que no está por no venir en el repositorio no es un fallo: se salta."""
    if BAJO_PYTEST:
        import pytest
        pytest.skip(f"falta {que} — {como}")
    check(f"{que} existe", False, f"— {como}")


def test_config():
    print("\n[1] Config")
    from backend.config import config
    check("config carga", config.port == 8020)
    if not (ROOT / config.agro_model).exists():
        return falta(config.agro_model, "corre download_models.py")
    check("modelo agro existe", True)


def test_detector():
    print("\n[2] Detector (inferencia sintética)")
    import numpy as np
    from backend.config import config
    from backend.detector import get_detector
    if not (ROOT / config.agro_model).exists():
        return falta(config.agro_model, "corre download_models.py")
    d = get_detector("agro")
    dets = d.infer(np.zeros((720, 1280, 3), dtype=np.uint8), 0.1)
    check("detector agro infiere", dets is not None)
    check("frame vacío → 0 dets", len(dets) == 0)


def test_analytics():
    print("\n[3] Analítica (gaps sintéticos)")
    import numpy as np
    import supervision as sv
    from backend.analytics import Analytics
    an = Analytics({"zones": []}, 1280, 720, 30.0)

    # hilera completa de plantas en la fila central de la grilla, con 1 hueco
    cy = (an.grows // 2 + 0.5) * an.cell_h
    boxes, skip = [], an.gcols // 2
    for gx in range(an.gcols):
        if gx == skip:
            continue                      # hueco
        cx = (gx + 0.5) * an.cell_w
        boxes.append([cx - 20, cy - 20, cx + 20, cy + 20])
    dets = sv.Detections(
        xyxy=np.array(boxes, dtype=float),
        class_id=np.zeros(len(boxes), dtype=int),
        confidence=np.full(len(boxes), 0.9),
        tracker_id=np.arange(1, len(boxes) + 1),
    )
    for i in range(5):                    # 5 frames para confirmar tracks y subir EMA
        an.update(dets, i / 30.0, 1 / 30.0)
    check("plantas únicas confirmadas", an.plantas_unicas == len(boxes),
          f"— {an.plantas_unicas} != {len(boxes)}")
    check("detecta el hueco", an.gap_cells_n >= 1, f"— {an.gap_cells_n}")
    check("gap_pct > 0", an.gap_pct > 0)
    check("malezas = 0", an.malezas_unicas == 0)

    # ahora todo maleza → presión sube
    dets.class_id = np.ones(len(boxes), dtype=int)
    an2 = Analytics({"zones": []}, 1280, 720, 30.0)
    for i in range(5):
        an2.update(dets, i / 30.0, 1 / 30.0)
    check("presión de maleza ~100%", an2.weed_pressure > 50,
          f"— {an2.weed_pressure:.0f}%")

    # hilera con 1/3 de huecos sostenidos 4 s → debe alertar
    an3 = Analytics({"zones": []}, 1280, 720, 30.0)
    cy = (an3.grows // 2 + 0.5) * an3.cell_h
    boxes3 = []
    for gx in range(an3.gcols):
        if gx % 3 == 0:
            continue
        cx = (gx + 0.5) * an3.cell_w
        boxes3.append([cx - 20, cy - 20, cx + 20, cy + 20])
    dets3 = sv.Detections(
        xyxy=np.array(boxes3, dtype=float),
        class_id=np.zeros(len(boxes3), dtype=int),
        confidence=np.full(len(boxes3), 0.9),
        tracker_id=np.arange(1, len(boxes3) + 1))
    for i in range(120):
        an3.update(dets3, i / 30.0, 1 / 30.0)
    check("alerta de despoblamiento dispara", len(an3.alerts) >= 1,
          f"— gap {an3.gap_pct:.0f}% sin alerta")


def test_video():
    print("\n[4] Video real (60 frames, plantacion_top)")
    vid = ROOT / "videos" / "plantacion_top.mp4"
    if not vid.exists():
        return falta("videos/plantacion_top.mp4", "corre download_models.py")
    from backend.processor import VideoProcessor
    p = VideoProcessor()
    p.class_mode = "cultivo"
    res = p.process_to_file(str(vid), vid.name, 0.05, ROOT / "outputs",
                            log=lambda *a: None, max_frames=60)
    check("procesa sin errores", True)
    check("cuenta plantas", res["plantas"] > 10, f"— {res['plantas']}")
    check("MP4 anotado creado", Path(res["video_out"]).exists())
    check("CSV creado", Path(res["csv"]).exists())
    csv_txt = Path(res["csv"]).read_text(encoding="utf-8")
    check("CSV tiene resumen", "Plantas detectadas" in csv_txt)


def main():
    print("=== Test OMNI Agro MVP ===")
    test_config()
    test_detector()
    test_analytics()
    test_video()
    print(f"\nResultado: {OK} OK · {FAIL} FALLOS")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()

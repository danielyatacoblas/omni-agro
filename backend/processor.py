"""Procesamiento de un video de dron en hilo: detección + ByteTrack + analítica.

Lee el video una vez de principio a fin (archivo, no dron en vivo), detecta
plantas/malezas, las sigue con ByteTrack (para contar únicas sin duplicar),
dibuja cajas, huecos de siembra y ROI, y publica el JPEG anotado (MJPEG) +
un snapshot de estadísticas reales. Mismo patrón que omni-retail.
"""
from __future__ import annotations

import csv
import threading
import time
from pathlib import Path

import cv2
import numpy as np
import supervision as sv

from .analytics import Analytics, _fmt
from .config import config
from .detector import get_detector, mark_warmed
from .zones import load_config

GREEN = (80, 200, 80)      # planta
RED = (60, 60, 235)        # maleza
GAP = (50, 50, 230)        # celda hueca
WHITE = (240, 240, 240)
DARK = (30, 30, 30)


def _resize_max(frame, max_w):
    if max_w and frame.shape[1] > max_w:
        h, w = frame.shape[:2]
        return cv2.resize(frame, (max_w, int(h * max_w / w)))
    return frame


class VideoProcessor:
    def __init__(self):
        self.lock = threading.Lock()
        self.thread = None
        self.running = False
        self.finished = False
        self.latest_jpeg = None
        self.analytics: Analytics | None = None
        self.video = None
        self.cfg_data = None
        self.conf = config.default_conf
        self.progress = 0.0
        self.video_t = 0.0
        self.duration = 0.0
        self.proc_fps = 0.0
        self.detector_kind = config.detector
        self.show_grid = True
        self.class_mode = config.class_mode   # modelo | cultivo

    # ── primer frame para el editor de ROI ──
    def first_frame_jpeg(self, video_path: str) -> bytes | None:
        cap = cv2.VideoCapture(video_path)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            return None
        frame = _resize_max(frame, config.max_width)
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return buf.tobytes() if ok else None

    def video_meta(self, video_path: str) -> dict:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return {"fps": round(fps, 2), "frames": n, "width": w, "height": h,
                "duration_sec": round(n / max(1.0, fps), 1)}

    # ── control ──
    def start(self, video_path: str, video_name: str, conf: float,
              detector_kind: str | None = None, show_grid: bool = True,
              class_mode: str | None = None):
        self.stop()
        self.cfg_data = load_config(video_name)
        self.conf = float(conf)
        self.video = video_name
        self.detector_kind = (detector_kind or config.detector).lower()
        self.show_grid = bool(show_grid)
        self.class_mode = (class_mode or config.class_mode).lower()
        self.finished = False
        self.progress = 0.0
        self.video_t = 0.0
        with self.lock:
            self.latest_jpeg = None
        self.running = True
        self.thread = threading.Thread(target=self._loop, args=(video_path,),
                                       daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.thread = None

    def _make_tracker(self, src_fps: float):
        return sv.ByteTrack(
            track_activation_threshold=config.track_activation,
            lost_track_buffer=config.track_lost_buffer,
            minimum_matching_threshold=config.track_min_match,
            frame_rate=int(round(src_fps)),
        )

    def _loop(self, video_path: str):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            self.running = False
            self.finished = True
            return

        src_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        self.duration = total / src_fps if total else 0.0

        ok, frame = cap.read()
        if not ok:
            cap.release(); self.running = False; self.finished = True; return
        frame = _resize_max(frame, config.max_width)
        h, w = frame.shape[:2]

        try:
            detector = get_detector(self.detector_kind)
        except Exception as e:
            print(f"[processor] no se pudo cargar el detector: {e}")
            self.running = False; self.finished = True; cap.release(); return
        tracker = self._make_tracker(src_fps)
        self.analytics = Analytics(self.cfg_data, w, h, src_fps)
        min_area = config.min_box_area_frac * w * h
        max_area = config.max_box_area_frac * w * h

        stride = max(1, config.frame_stride)
        dt = stride / src_fps
        frame_idx = 0
        t_wall = time.time()
        proc_count = 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        while self.running:
            ok = cap.grab()
            if not ok:
                break
            if frame_idx % stride != 0:
                frame_idx += 1
                continue
            ok, frame = cap.retrieve()
            if not ok:
                break
            frame = _resize_max(frame, config.max_width)

            dets = detector.infer(frame, self.conf)
            dets = self._filter(dets, min_area, max_area)
            dets = tracker.update_with_detections(dets)

            self.video_t = frame_idx / src_fps
            self.analytics.update(dets, self.video_t, dt)
            self._draw(frame, dets)
            mark_warmed(self.detector_kind)

            proc_count += 1
            elapsed = time.time() - t_wall
            self.proc_fps = proc_count / elapsed if elapsed > 0 else 0.0
            self.progress = (frame_idx / total) if total else 0.0

            ok, buf = cv2.imencode(".jpg", frame,
                                   [cv2.IMWRITE_JPEG_QUALITY, config.jpeg_quality])
            if ok:
                with self.lock:
                    self.latest_jpeg = buf.tobytes()
            frame_idx += 1

        cap.release()
        self.running = False
        self.finished = True
        self.progress = 1.0
        try:
            self.export_csv()
        except Exception as e:
            print(f"[processor] export CSV falló: {e}")

    def _filter(self, dets, min_area, max_area):
        if dets is None or len(dets) == 0:
            return dets
        xyxy = dets.xyxy
        areas = (xyxy[:, 2] - xyxy[:, 0]) * (xyxy[:, 3] - xyxy[:, 1])
        dets = dets[(areas >= min_area) & (areas <= max_area)]
        # modo "cultivo": toda detección es planta (el modelo clasifica mal
        # cultivos que no conoce — arándano/cítrico/palto salen como "weed")
        if self.class_mode == "cultivo" and dets is not None and len(dets):
            dets.class_id = np.zeros(len(dets), dtype=int)
        if config.track_boost and dets is not None and len(dets) \
                and dets.confidence is not None:
            dets.confidence = np.maximum(dets.confidence, 0.5)
        return dets

    # ── dibujo ──
    def _draw(self, frame, dets):
        an = self.analytics
        # ROI
        for r in an.roi_polys:
            col = self._hex(r["color"])
            cv2.polylines(frame, [r["poly"]], True, col, 2)
            p0 = r["poly"][0]
            cv2.putText(frame, r["name"], (int(p0[0]), int(p0[1]) - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, col, 2, cv2.LINE_AA)
        # celdas huecas (despoblamiento)
        if self.show_grid and an.gap_cells:
            overlay = frame.copy()
            for gy, gx in an.gap_cells:
                x1 = int(gx * an.cell_w); y1 = int(gy * an.cell_h)
                x2 = int((gx + 1) * an.cell_w); y2 = int((gy + 1) * an.cell_h)
                cv2.rectangle(overlay, (x1, y1), (x2, y2), GAP, -1)
            cv2.addWeighted(overlay, 0.28, frame, 0.72, 0, frame)
            for gy, gx in an.gap_cells:
                x1 = int(gx * an.cell_w); y1 = int(gy * an.cell_h)
                x2 = int((gx + 1) * an.cell_w); y2 = int((gy + 1) * an.cell_h)
                cv2.rectangle(frame, (x1, y1), (x2, y2), GAP, 1)
        # detecciones
        if dets is not None and len(dets):
            tids = dets.tracker_id if dets.tracker_id is not None else [None] * len(dets)
            for box, cid, tid in zip(dets.xyxy, dets.class_id, tids):
                x1, y1, x2, y2 = map(int, box)
                col = RED if cid == 1 else GREEN
                cv2.rectangle(frame, (x1, y1), (x2, y2), col, 2)
                if cid == 1 and tid is not None:
                    lbl = f"M{int(tid)}"
                    (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                    cv2.rectangle(frame, (x1, y1 - th - 5), (x1 + tw + 5, y1), col, -1)
                    cv2.putText(frame, lbl, (x1 + 2, y1 - 3),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, WHITE, 1, cv2.LINE_AA)
        # HUD
        hud = (f"t {_fmt(self.video_t)} / {_fmt(self.duration)}   "
               f"plantas: {an.plantas_frame}   malezas: {an.malezas_frame}   "
               f"huecos: {an.gap_pct:.0f}%   {self.proc_fps:.1f} fps")
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 26), DARK, -1)
        cv2.putText(frame, hud, (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (120, 230, 120), 1, cv2.LINE_AA)

    @staticmethod
    def _hex(h):
        h = h.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (b, g, r)

    # ── salidas ──
    def mjpeg_frames(self):
        while True:
            with self.lock:
                data = self.latest_jpeg
            if data is None:
                time.sleep(0.03)
                continue
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + data + b"\r\n")
            time.sleep(0.04)

    def status(self) -> dict:
        from . import detector as _det
        base = {
            "running": self.running, "finished": self.finished,
            "video": self.video, "progress": round(self.progress, 4),
            "video_time": _fmt(self.video_t), "duration": _fmt(self.duration),
            "proc_fps": round(self.proc_fps, 1),
            "has_frame": self.latest_jpeg is not None,
            "model_ready": _det.is_warmed(self.detector_kind),
            "detector": self.detector_kind,
            "class_mode": self.class_mode,
        }
        if self.analytics:
            base.update(self.analytics.snapshot())
        return base

    def process_to_file(self, video_path: str, video_name: str, conf: float,
                        out_dir: Path, log=print, max_frames: int = 0) -> dict:
        """Modo headless (CLI/test): procesa el video, escribe un MP4 anotado
        y el CSV. No usa hilo ni streaming. Devuelve resumen."""
        self.cfg_data = load_config(video_name)
        self.conf = float(conf)
        self.video = video_name

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"no se pudo abrir {video_path}")
        src_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        self.duration = total / src_fps if total else 0.0

        ok, frame = cap.read()
        if not ok:
            raise RuntimeError("video vacío")
        frame = _resize_max(frame, config.max_width)
        h, w = frame.shape[:2]

        detector = get_detector(self.detector_kind)
        tracker = self._make_tracker(src_fps)
        self.analytics = Analytics(self.cfg_data, w, h, src_fps)
        min_area = config.min_box_area_frac * w * h
        max_area = config.max_box_area_frac * w * h

        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{Path(video_name).stem}_agro.mp4"
        writer = cv2.VideoWriter(str(out_file),
                                 cv2.VideoWriter_fourcc(*"mp4v"), src_fps, (w, h))

        stride = max(1, config.frame_stride)
        dt = stride / src_fps
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        frame_idx = 0
        t0 = time.time()
        while True:
            if max_frames and frame_idx >= max_frames:
                break
            ok = cap.grab()
            if not ok:
                break
            if frame_idx % stride != 0:
                frame_idx += 1
                continue
            ok, frame = cap.retrieve()
            if not ok:
                break
            frame = _resize_max(frame, config.max_width)
            dets = detector.infer(frame, self.conf)
            dets = self._filter(dets, min_area, max_area)
            dets = tracker.update_with_detections(dets)
            self.video_t = frame_idx / src_fps
            self.analytics.update(dets, self.video_t, dt)
            self._draw(frame, dets)
            writer.write(frame)
            if frame_idx % 50 == 0 and total:
                log(f"  frame {frame_idx}/{total} ({100*frame_idx/total:.0f}%)  "
                    f"plantas {self.analytics.plantas_unicas}  "
                    f"malezas {self.analytics.malezas_unicas}  "
                    f"huecos {self.analytics.gap_pct:.0f}%")
            frame_idx += 1
        cap.release()
        writer.release()
        csv_path = self.export_csv()
        snap = self.analytics.snapshot()
        log(f"  ✓ {out_file.name} ({out_file.stat().st_size/1e6:.1f} MB)  "
            f"en {time.time()-t0:.1f}s")
        return {"video_out": str(out_file), "csv": str(csv_path),
                "plantas": snap["plantas_unicas"],
                "malezas": snap["malezas_unicas"],
                "gap_pct": snap["gap_pct"]}

    def export_csv(self) -> Path:
        """Exporta a CSV los datos REALES: resumen, malezas, huecos y alertas."""
        if not self.analytics:
            raise RuntimeError("no hay analítica para exportar")
        snap = self.analytics.snapshot()
        out = config.data_abs / f"reporte_{Path(self.video).stem}.csv"
        with out.open("w", newline="", encoding="utf-8") as f:
            wr = csv.writer(f)
            wr.writerow(["OMNI Agro — Reporte de sobrevuelo", self.video])
            wr.writerow([])
            wr.writerow(["RESUMEN"])
            wr.writerow(["Plantas detectadas (únicas)", snap["plantas_unicas"]])
            wr.writerow(["Malezas detectadas (únicas)", snap["malezas_unicas"]])
            wr.writerow(["Plantas por frame (prom.)", snap["plantas_frame_avg"]])
            wr.writerow(["Plantas por frame (pico)", snap["peak_frame"]])
            wr.writerow(["Presión de maleza final (%)", snap["weed_pressure"]])
            wr.writerow(["Despoblamiento final (%)", snap["gap_pct"]])
            wr.writerow(["Detector", self.detector_kind])
            wr.writerow([])
            wr.writerow(["LÍNEA DE TIEMPO (1 muestra/seg de video)"])
            wr.writerow(["Segundo", "Plantas en frame", "Malezas en frame",
                         "Despoblamiento %"])
            for p in snap["timeline"]:
                wr.writerow([p["t"], p["plantas"], p["malezas"], p["gap"]])
            wr.writerow([])
            wr.writerow(["ALERTAS"])
            wr.writerow(["Tiempo video", "Módulo", "Tipo", "Detalle", "Severidad"])
            for a in snap["alerts"]:
                wr.writerow([a["video_time"], a["modulo"], a["tipo"],
                             a["detalle"], a["severity"]])
        return out


processor = VideoProcessor()

"""Analítica agro real por video de dron: conteo, malezas y despoblamiento.

Todo se calcula sobre el *tiempo del video* (frame / fps), no sobre el reloj de
pared, igual que en los demás MVPs.

- Conteo:         tracks únicos de ByteTrack confirmados (vistos >= N frames).
                  0 = planta de cultivo, 1 = maleza.
- Presión maleza: malezas / (plantas + malezas) del frame, suavizado (EMA).
- Despoblamiento: grilla sobre el frame (o ROI). Una celda es "hueco" si está
                  vacía pero su hilera (fila o columna de la grilla) está
                  mayormente cultivada. % huecos suavizado con EMA.
                  Heurística documentada como *experimental* (sin georreferencia).
"""
from __future__ import annotations

import cv2
import numpy as np

from .config import config
from .zones import zone_to_px


class Analytics:
    def __init__(self, cfg_data: dict, w: int, h: int, fps: float):
        self.w, self.h, self.fps = w, h, max(1.0, fps)

        # ── ROI opcional (se analiza solo lo de adentro) ──
        self.roi_polys = []
        self.roi_mask = None
        for z in cfg_data.get("zones", []):
            poly = zone_to_px(z, w, h)
            if len(poly) >= 3:
                self.roi_polys.append({"name": z.get("name", "Lote"),
                                       "color": z.get("color", "#6FA80C"),
                                       "poly": poly})
        if self.roi_polys:
            m = np.zeros((h, w), dtype=np.uint8)
            for r in self.roi_polys:
                cv2.fillPoly(m, [r["poly"]], 255)
            self.roi_mask = m

        # ── grilla de despoblamiento ──
        self.gcols = max(4, config.grid_cols)
        self.grows = max(3, int(round(self.gcols * h / max(1, w))))
        self.cell_w = w / self.gcols
        self.cell_h = h / self.grows
        # celdas dentro del ROI (o todas si no hay ROI)
        self.cell_active = np.ones((self.grows, self.gcols), dtype=bool)
        if self.roi_mask is not None:
            for gy in range(self.grows):
                for gx in range(self.gcols):
                    cx = int((gx + 0.5) * self.cell_w)
                    cy = int((gy + 0.5) * self.cell_h)
                    self.cell_active[gy, gx] = self.roi_mask[cy, cx] > 0

        # estado
        self.tracks = {}          # tid -> {cls, frames, first, last}
        self.plantas_unicas = 0   # tracks confirmados clase 0
        self.malezas_unicas = 0   # tracks confirmados clase 1
        self.plantas_frame = 0
        self.malezas_frame = 0
        self.plantas_frame_avg = 0.0   # EMA
        self.peak_frame = 0
        self.weed_pressure = 0.0       # EMA %
        self.gap_pct = 0.0             # EMA %
        self.gap_cells = []            # [(gy,gx)] del último frame (para dibujar)
        self.gap_cells_n = 0
        self.row_cells_n = 0
        self.cur_t = 0.0
        self.timeline = []             # [{t, plantas, malezas, gap}] c/1s
        self._last_sample_sec = -1
        self.alerts = []
        self._gap_over_since = None
        self._weed_over_since = None
        self._gap_alerted = False
        self._weed_alerted = False

    # ── helpers ──
    def _add_alert(self, t: float, modulo: str, tipo: str, detalle: str,
                   severity: str):
        self.alerts.append({
            "t": round(t, 1), "video_time": _fmt(t),
            "modulo": modulo, "tipo": tipo, "detalle": detalle,
            "severity": severity,
        })

    def _in_roi(self, cx: float, cy: float) -> bool:
        if self.roi_mask is None:
            return True
        xi = min(self.w - 1, max(0, int(cx)))
        yi = min(self.h - 1, max(0, int(cy)))
        return self.roi_mask[yi, xi] > 0

    # ── actualización por frame (detections ya trackeadas) ──
    def update(self, detections, video_t: float, dt: float):
        self.cur_t = video_t

        centers = []      # (cx, cy, cls, tid)
        if detections is not None and len(detections):
            tids = (detections.tracker_id if detections.tracker_id is not None
                    else [None] * len(detections))
            for box, cid, tid in zip(detections.xyxy, detections.class_id, tids):
                cx = (box[0] + box[2]) / 2.0
                cy = (box[1] + box[3]) / 2.0
                if not self._in_roi(cx, cy):
                    continue
                centers.append((cx, cy, int(cid), tid))

        # CONTEO por tracks únicos confirmados
        p_frame = m_frame = 0
        for cx, cy, cid, tid in centers:
            if cid == 1:
                m_frame += 1
            else:
                p_frame += 1
            if tid is None:
                continue
            tid = int(tid)
            tr = self.tracks.get(tid)
            if tr is None:
                self.tracks[tid] = {"cls": cid, "frames": 1, "first": video_t,
                                    "last": video_t, "confirmed": False}
            else:
                tr["frames"] += 1
                tr["last"] = video_t
                # la clase mayoritaria manda (una maleza puede parpadear como planta)
                if cid == 1 and tr["cls"] == 0 and tr["frames"] <= 3:
                    tr["cls"] = 1
                if not tr["confirmed"] and tr["frames"] >= config.min_track_frames:
                    tr["confirmed"] = True
                    if tr["cls"] == 1:
                        self.malezas_unicas += 1
                    else:
                        self.plantas_unicas += 1

        self.plantas_frame = p_frame
        self.malezas_frame = m_frame
        self.peak_frame = max(self.peak_frame, p_frame)
        self.plantas_frame_avg = (0.9 * self.plantas_frame_avg + 0.1 * p_frame
                                  if self.plantas_frame_avg else float(p_frame))

        # PRESIÓN DE MALEZA (EMA sobre el % del frame)
        tot = p_frame + m_frame
        wp_now = 100.0 * m_frame / tot if tot else 0.0
        self.weed_pressure = 0.8 * self.weed_pressure + 0.2 * wp_now

        # DESPOBLAMIENTO por grilla
        occ = np.zeros((self.grows, self.gcols), dtype=bool)
        for cx, cy, cid, _ in centers:
            if cid != 0:
                continue
            gx = min(self.gcols - 1, int(cx / self.cell_w))
            gy = min(self.grows - 1, int(cy / self.cell_h))
            occ[gy, gx] = True

        gap_cells = []
        row_cells = 0
        if occ.any():
            frac_need = config.row_occupied_frac
            # filas y columnas "cultivadas" (mayoría de celdas activas ocupadas)
            for gy in range(self.grows):
                act = self.cell_active[gy]
                n_act = int(act.sum())
                if n_act and occ[gy][act].sum() >= frac_need * n_act:
                    for gx in range(self.gcols):
                        if act[gx]:
                            row_cells += 1
                            if not occ[gy, gx]:
                                gap_cells.append((gy, gx))
            for gx in range(self.gcols):
                act = self.cell_active[:, gx]
                n_act = int(act.sum())
                if n_act and occ[:, gx][act].sum() >= frac_need * n_act:
                    for gy in range(self.grows):
                        if act[gy] and (gy, gx) not in gap_cells:
                            row_cells += 1
                            if not occ[gy, gx]:
                                gap_cells.append((gy, gx))
        self.gap_cells = gap_cells
        self.gap_cells_n = len(gap_cells)
        self.row_cells_n = row_cells
        gap_now = 100.0 * len(gap_cells) / row_cells if row_cells else 0.0
        self.gap_pct = 0.8 * self.gap_pct + 0.2 * gap_now

        # ALERTAS sostenidas (evitan falsos por un frame malo)
        self._sustained_alert(
            video_t, self.gap_pct, config.gap_alert_pct,
            config.gap_alert_sustain_sec, "gap",
            "Despoblamiento", "Huecos de siembra",
            lambda: f"{self.gap_pct:.0f}% de celdas sin planta en hileras cultivadas")
        self._sustained_alert(
            video_t, self.weed_pressure, config.weed_alert_pct,
            config.weed_alert_sustain_sec, "weed",
            "Malezas", "Presión de maleza alta",
            lambda: f"{self.weed_pressure:.0f}% de lo detectado es maleza")

        # timeline (1 muestra por segundo de video)
        sec = int(video_t)
        if sec != self._last_sample_sec:
            self._last_sample_sec = sec
            self.timeline.append({"t": sec, "plantas": p_frame,
                                  "malezas": m_frame,
                                  "gap": round(self.gap_pct, 1)})

    def _sustained_alert(self, t, value, threshold, sustain, key,
                         modulo, tipo, detalle_fn):
        over_attr = f"_{key}_over_since"
        alerted_attr = f"_{key}_alerted"
        if value >= threshold:
            since = getattr(self, over_attr)
            if since is None:
                setattr(self, over_attr, t)
            elif (t - since) >= sustain and not getattr(self, alerted_attr):
                setattr(self, alerted_attr, True)
                sev = "critical" if value >= threshold * 1.5 else "warning"
                self._add_alert(t, modulo, tipo, detalle_fn(), sev)
        else:
            setattr(self, over_attr, None)
            if value < threshold * 0.7:
                setattr(self, alerted_attr, False)

    # ── snapshot para el dashboard ──
    def snapshot(self) -> dict:
        # tracks activos (vistos en el último ~segundo) para el panel inferior
        active = []
        for tid, tr in self.tracks.items():
            if self.cur_t - tr["last"] > 1.0 or not tr["confirmed"]:
                continue
            active.append({"id": tid,
                           "tipo": "maleza" if tr["cls"] == 1 else "planta",
                           "seen": _fmt(tr["last"] - tr["first"]),
                           "seen_sec": round(tr["last"] - tr["first"], 1)})
        active.sort(key=lambda x: -x["seen_sec"])

        return {
            "plantas_unicas": self.plantas_unicas,
            "malezas_unicas": self.malezas_unicas,
            "plantas_frame": self.plantas_frame,
            "malezas_frame": self.malezas_frame,
            "plantas_frame_avg": round(self.plantas_frame_avg, 1),
            "peak_frame": self.peak_frame,
            "weed_pressure": round(self.weed_pressure, 1),
            "gap_pct": round(self.gap_pct, 1),
            "gap_cells": self.gap_cells_n,
            "row_cells": self.row_cells_n,
            "roi_count": len(self.roi_polys),
            "active_tracks": active[:40],
            "active_count": len(active),
            "timeline": self.timeline[-600:],
            "alerts": self.alerts[-100:],
        }


def _fmt(sec: float) -> str:
    sec = int(round(sec))
    m, s = divmod(sec, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}h {m:02d}m"
    return f"{m}m {s:02d}s" if m else f"{s}s"

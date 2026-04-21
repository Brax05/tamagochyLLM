#!/usr/bin/env python3
"""
gui_mochi.py - Interfaz grafica para Mochi (MascotaLM)
Usa tkinter estandar - sin dependencias externas.
Cerdito OLED inspirado en TamaPI (version canvas pixel-art).
 
Ejecutar:
    python gui_mochi.py
"""
 
import tkinter as tk
import sys
import os
import threading
import re
import math
 
# ======================================================
#  RUTAS DEL MODELO
# ======================================================
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
LLM_DIR    = BASE_DIR
CHECKPOINT = os.path.join(BASE_DIR, "checkpoints", "best_model.pt")
TOKENIZER  = os.path.join(BASE_DIR, "data", "tokenizer.json")
 
sys.path.insert(0, BASE_DIR)
 
# ======================================================
#  AUTO-DETECCION DEL ENTORNO VIRTUAL
# ======================================================
def _add_venv_if_needed():
    try:
        import importlib
        importlib.import_module("tokenizers")
    except ImportError:
        import glob
        venv_dir = os.path.join(BASE_DIR, ".venv")
        pattern  = os.path.join(venv_dir, "Lib", "site-packages")
        matches  = glob.glob(pattern)
        if matches:
            sys.path.insert(0, matches[0])
        else:
            for sp in glob.glob(os.path.join(venv_dir, "lib", "python*", "site-packages")):
                sys.path.insert(0, sp)
 
_add_venv_if_needed()
 
# ======================================================
#  DETECTOR DE EMOCIONES
# ======================================================
 
_TAG_RE = re.compile(r"^\s*\[(\w+)\]\s*", re.IGNORECASE)
 
KEYWORD_MAP = {
    "FELIZ": [
        "alegr", "feliz", "encanta", "genial", "perfecto",
        "divertid", "emocion", "contenta", "adoro", "amor",
        "quiero", "lindo", "me alegra", "me gusta", "bien",
        "delicioso", "emocionad", "cachetes", "saltito",
        "vibrand", "pancita", "orejas",
    ],
    "TRISTE": [
        "triste", "tristeza", "pesado", "me siento mal",
        "necesito un mimo", "bajo", "llor", "soledad", "me duele",
    ],
    "ENOJADO": [
        "molest", "enojad", "fastidi", "no me gusta",
        "harto", "basta", "irritad", "furioso",
    ],
}
 
EMOTION_LABELS = {
    "FELIZ":      "HAPPY!",
    "TRISTE":     "SAD...",
    "ENOJADO":    "ANGRY!",
    "NEUTRAL":    "MEH.",
    "DORMIDO":    "ZZZ...",
    "HAMBRIENTO": "HUNGRY!",
    "LLORANDO":   "SOB!",
    "ASUSTADO":   "SCARED!",
    "ABURRIDO":   "BORED.",
    "CARGANDO":   "...",
    "PENSATIVO":  "HMM...",
    "VERGUENZA":  "UWU~",
}
 
VALID_STATES = set(EMOTION_LABELS.keys())
 
 
def detect_emotion(text):
    m = _TAG_RE.match(text)
    if m:
        tag   = m.group(1).upper()
        clean = text[m.end():].strip()
        return (tag if tag in VALID_STATES else "NEUTRAL"), clean
    lower = text.lower()
    for emotion, keywords in KEYWORD_MAP.items():
        if any(kw in lower for kw in keywords):
            return emotion, text
    return "NEUTRAL", text
 
# ======================================================
#  PUENTE CON EL LLM
# ======================================================
 
_engine      = None
_engine_lock = threading.Lock()
_history     = []
 
 
def load_engine():
    global _engine
    try:
        from mascotalm.inference import MascotaInference
        eng = MascotaInference(CHECKPOINT, TOKENIZER, device="cpu")
        with _engine_lock:
            _engine = eng
        return True, None
    except Exception as exc:
        return False, str(exc)
 
 
def ask_mochi(user_text):
    global _history
    _history.append({"role": "user", "content": user_text})
    try:
        with _engine_lock:
            if _engine is None:
                return "TRISTE", "Todavia me estoy despertando... espera un momento."
            result = _engine.chat_completion(
                _history[-4:], temperature=0.65, top_k=35, max_tokens=80
            )
        raw = result["choices"][0]["message"].get("content", "").strip()
        if not raw:
            return "NEUTRAL", "..."
        emotion, clean = detect_emotion(raw)
        _history.append({"role": "assistant", "content": clean})
        if len(_history) > 10:
            _history[:] = _history[-10:]
        return emotion, clean
    except Exception as exc:
        return "TRISTE", f"Algo salio mal: {exc}"
 
# ======================================================
#  COLORES
# ======================================================
BG_MAIN   = "#0d0d0d"
BG_PANEL  = "#111111"
BG_INPUT  = "#1a1a1a"
FG_GREEN  = "#39ff14"
FG_CYAN   = "#00bfff"
FG_GRAY   = "#888888"
FG_WHITE  = "#ffffff"
 
# Paleta OLED del cerdito
C_BODY    = "#003d55"
C_BODY_S  = "#005577"
C_EAR_IN  = "#0077aa"
C_STROKE  = "#00cfff"
C_SNOUT   = "#002a3d"
C_SNOUT_S = "#0099cc"
C_NOSE    = "#00cfff"
C_FACE    = "#00eeff"
C_FLOOR   = "#003344"
C_FLOOR_B = "#005566"
 
FONT_MONO  = ("Courier New", 11)
FONT_TITLE = ("Courier New", 12, "bold")
FONT_SMALL = ("Courier New", 9)
 
TYPEWRITER_DELAY_MS = 20
 
# ======================================================
#  CANVAS PIG RENDERER
# ======================================================
 
def _oval(c, x, y, rx, ry, **kw):
    """Helper: draw ellipse given center and radii."""
    c.create_oval(x - rx, y - ry, x + rx, y + ry, **kw)
 
def _line(c, x1, y1, x2, y2, **kw):
    c.create_line(x1, y1, x2, y2, **kw)
 
def _arc_smile(canvas, cx, cy, rx, ry, start, extent, **kw):
    """Draw an arc (smile/frown) via create_arc in chord mode outline only."""
    canvas.create_arc(
        cx - rx, cy - ry, cx + rx, cy + ry,
        start=start, extent=extent,
        style=tk.ARC, **kw
    )
 
 
class PigCanvas(tk.Canvas):
    """
    Canvas that draws the OLED-style pig from TamaPI.
    Scale is relative to a 130x118 SVG viewport mapped onto W x H pixels.
    Emotion expressions mirror the SVG FACES dict from the HTML.
    """
 
    def __init__(self, parent, width=260, height=236, **kw):
        super().__init__(
            parent,
            width=width, height=height,
            bg=BG_MAIN, highlightthickness=0,
            **kw
        )
        self.W = width
        self.H = height
        # SVG viewport: 130 x 118
        self.sx = width  / 130
        self.sy = height / 118
        self._bounce_offset = 0
        self._bounce_dir    = 1
        self._bounce_job    = None
        self._blink_job     = None
        self._dots_phase    = 0
        self._dots_job      = None
        self._current_mood  = "FELIZ"
        self._draw("FELIZ")
        self._start_bounce()
 
    # --------------------------------------------------
    def _s(self, x, y=None):
        """Scale SVG coords to canvas coords."""
        if y is None:
            return x * self.sx
        return x * self.sx, y * self.sy + self._bounce_offset
 
    def _sr(self, rx, ry=None):
        """Scale radii."""
        if ry is None:
            return rx * self.sx
        return rx * self.sx, ry * self.sy
 
    # --------------------------------------------------
    def _draw(self, mood):
        self._current_mood = mood
        self.delete("all")
        self._draw_floor()
        self._draw_body()
        self._draw_face(mood)
 
    def _draw_floor(self):
        y0 = self._s(0, 108)[1]
        self.create_rectangle(0, y0, self.W, self.H,
                               fill=C_FLOOR, outline="")
        self.create_line(0, y0, self.W, y0,
                         fill=C_FLOOR_B, width=max(1, int(2 * self.sy)))
 
    def _draw_body(self):
        sx, sy = self.sx, self.sy
        bo = self._bounce_offset
 
        def ov(cx, cy, rx, ry, **kw):
            self.create_oval(
                cx * sx - rx * sx, cy * sy - ry * sy + bo,
                cx * sx + rx * sx, cy * sy + ry * sy + bo,
                **kw
            )
 
        lw = max(1, int(2 * min(sx, sy)))
 
        # Left ear outer
        ov(28, 24, 18, 20, fill=C_BODY_S, outline=C_STROKE, width=lw)
        # Left ear inner
        ov(28, 24, 10, 12, fill=C_EAR_IN, outline="")
        # Right ear outer
        ov(102, 24, 18, 20, fill=C_BODY_S, outline=C_STROKE, width=lw)
        # Right ear inner
        ov(102, 24, 10, 12, fill=C_EAR_IN, outline="")
        # Head
        ov(65, 68, 48, 44, fill=C_BODY, outline=C_STROKE, width=max(2, int(2.5 * min(sx, sy))))
        # Snout
        ov(65, 82, 20, 13, fill=C_SNOUT, outline=C_SNOUT_S, width=lw)
        # Nostrils
        ov(57, 83, 4, 4, fill=C_NOSE, outline="")
        ov(73, 83, 4, 4, fill=C_NOSE, outline="")
 
    # --------------------------------------------------
    def _draw_face(self, mood):
        sx, sy = self.sx, self.sy
        bo = self._bounce_offset
        lw_eye  = max(2, int(4.5 * min(sx, sy)))
        lw_mth  = max(2, int(3.5 * min(sx, sy)))
        lw_brow = max(2, int(4.5 * min(sx, sy)))
        col_e   = C_FACE
        col_f   = C_FACE
 
        def pt(x, y):
            return x * sx, y * sy + bo
 
        def eye_arc(cx, cy, rx, ry, start, extent):
            x1, y1 = cx * sx - rx * sx, cy * sy - ry * sy + bo
            x2, y2 = cx * sx + rx * sx, cy * sy + ry * sy + bo
            self.create_arc(x1, y1, x2, y2,
                            start=start, extent=extent,
                            style=tk.ARC,
                            outline=col_e, width=lw_eye)
 
        def mouth_arc(cx, cy, rx, ry, start, extent):
            x1, y1 = cx * sx - rx * sx, cy * sy - ry * sy + bo
            x2, y2 = cx * sx + rx * sx, cy * sy + ry * sy + bo
            self.create_arc(x1, y1, x2, y2,
                            start=start, extent=extent,
                            style=tk.ARC,
                            outline=col_f, width=lw_mth)
 
        def dot(cx, cy, r=5.5):
            self.create_oval(
                cx * sx - r * sx, cy * sy - r * sy + bo,
                cx * sx + r * sx, cy * sy + r * sy + bo,
                fill=C_NOSE, outline=""
            )
 
        def line(x1, y1, x2, y2, w=None, col=None):
            self.create_line(
                *pt(x1, y1), *pt(x2, y2),
                fill=col or col_e,
                width=w or lw_brow,
                capstyle=tk.ROUND
            )
 
        # ---- FELIZ ----
        if mood == "FELIZ":
            eye_arc(46, 58, 10, 6, 0, 180)    # left eye smile
            eye_arc(84, 58, 10, 6, 0, 180)    # right eye smile
            mouth_arc(65, 98, 18, 8, 180, 180) # big smile
 
        # ---- TRISTE ----
        elif mood == "TRISTE":
            eye_arc(46, 52, 10, 6, 180, 180)   # left eye sad
            eye_arc(84, 52, 10, 6, 180, 180)   # right eye sad
            mouth_arc(65, 104, 16, 6, 0, 180)  # frown
 
        # ---- ENOJADO ----
        elif mood == "ENOJADO":
            line(34, 38, 56, 48)               # left brow
            line(96, 38, 74, 48)               # right brow
            line(36, 56, 56, 56, w=lw_eye)    # left flat eye
            line(74, 56, 94, 56, w=lw_eye)    # right flat eye
            line(49, 98, 81, 98, w=lw_mth)    # flat mouth
 
        # ---- NEUTRAL ----
        elif mood == "NEUTRAL":
            dot(46, 54)
            dot(84, 54)
            line(49, 98, 81, 98, w=lw_mth)
 
        # ---- DORMIDO ----
        elif mood == "DORMIDO":
            eye_arc(46, 62, 10, 6, 180, 180)
            eye_arc(84, 62, 10, 6, 180, 180)
            mouth_arc(65, 98, 16, 7, 0, 180)
            # ZZZ
            for zx, zy, fs in [(96, 46, 11), (107, 34, 14), (117, 21, 18)]:
                self.create_text(
                    zx * sx, zy * sy + bo,
                    text="Z" if fs >= 18 else "z",
                    fill=C_NOSE,
                    font=("Courier New", max(8, int(fs * min(sx, sy)))),
                    anchor="nw"
                )
 
        # ---- HAMBRIENTO ----
        elif mood == "HAMBRIENTO":
            # X eyes
            for ex, ey in [(38, 46), (76, 46)]:
                line(ex, ey,     ex + 16, ey + 16)
                line(ex + 16, ey, ex,     ey + 16)
            mouth_arc(65, 97, 18, 8, 180, 180)
            # drool dot
            dot(65, 117, r=3)
 
        # ---- LLORANDO ----
        elif mood == "LLORANDO":
            eye_arc(46, 52, 10, 6, 180, 180)
            eye_arc(84, 52, 10, 6, 180, 180)
            # tears
            line(42, 62, 42, 84, col=C_NOSE, w=max(1, int(3 * min(sx, sy))))
            line(88, 62, 88, 84, col=C_NOSE, w=max(1, int(3 * min(sx, sy))))
            mouth_arc(65, 104, 16, 6, 0, 180)
 
        # ---- ASUSTADO ----
        elif mood == "ASUSTADO":
            # wide circle eyes
            for ex, ey in [(46, 52), (84, 52)]:
                r = 10 * sx
                self.create_oval(
                    ex * sx - r, ey * sy - r + bo,
                    ex * sx + r, ey * sy + r + bo,
                    outline=col_e, width=lw_eye, fill=""
                )
                dot(ex, ey, r=4)
            # wavy mouth
            pts = [
                pt(47, 95), pt(54, 90), pt(61, 95),
                pt(68, 100), pt(75, 95), pt(79, 91), pt(81, 95)
            ]
            self.create_line(*[c for p in pts for c in p],
                             fill=col_f, width=lw_mth,
                             smooth=True, capstyle=tk.ROUND)
 
        # ---- ABURRIDO ----
        elif mood == "ABURRIDO":
            # half-open eyes (line on top + small arc)
            for ex in [36, 74]:
                line(ex, 52, ex + 20, 52, w=lw_eye)
                eye_arc(ex // 1 + 10, 52, 10, 6, 180, 180)
            line(49, 98, 81, 98, w=lw_mth)
 
        # ---- CARGANDO ----
        elif mood == "CARGANDO":
            # animated dots drawn by _tick_dots
            self._draw_cargando_dots()
            line(49, 98, 81, 98, w=lw_mth)
 
        # ---- PENSATIVO ----
        elif mood == "PENSATIVO":
            dot(50, 50)
            dot(87, 47)
            # thought bubbles
            dot(100, 36, r=2.5)
            dot(110, 25, r=3.5)
            dot(121, 13, r=5)
            mouth_arc(65, 98, 14, 5, 0, 180)
 
        # ---- VERGUENZA ----
        elif mood == "VERGUENZA":
            # blush
            for bx, by in [(22, 68), (108, 68)]:
                self.create_oval(
                    bx * sx - 13 * sx, by * sy - 8 * sy + bo,
                    bx * sx + 13 * sx, by * sy + 8 * sy + bo,
                    fill=C_BODY_S, outline="", stipple=""
                )
            # eyes: line + dot
            for ex, ey in [(38, 50, 54, 50, 46, 55), (76, 50, 92, 50, 84, 55)]:
                line(ex, ey, ex + 1, ey, w=lw_eye)   # tiny line above
            line(38, 50, 54, 50, w=lw_eye)
            dot(46, 55, r=4.5)
            line(76, 50, 92, 50, w=lw_eye)
            dot(84, 55, r=4.5)
            mouth_arc(65, 98, 14, 5, 0, 180)
 
        else:
            # fallback = neutral
            dot(46, 54)
            dot(84, 54)
            line(49, 98, 81, 98, w=lw_mth)
 
    def _draw_cargando_dots(self):
        """Draw 3 pulsing dots. Phase 0,1,2 controls which is bright."""
        sx, sy = self.sx, self.sy
        bo = self._bounce_offset
        phase = self._dots_phase
        for i, (cx, cy) in enumerate([(40, 56), (65, 56), (90, 56)]):
            alpha = 1.0 if i == phase else 0.15
            r = 5 * sx
            bright = C_NOSE
            dim    = "#003344"
            col = bright if i == phase else dim
            self.create_oval(
                cx * sx - r, cy * sy - r + bo,
                cx * sx + r, cy * sy + r + bo,
                fill=col, outline=""
            )
 
    # --------------------------------------------------
    #  BOUNCE ANIMATION
    # --------------------------------------------------
    def _start_bounce(self):
        self._bounce_step()
 
    def _bounce_step(self):
        self._bounce_offset += self._bounce_dir * 1.5
        if self._bounce_offset >= 6:
            self._bounce_dir = -1
        elif self._bounce_offset <= 0:
            self._bounce_dir = 1
        self._draw(self._current_mood)
        self._bounce_job = self.after(40, self._bounce_step)
 
    # --------------------------------------------------
    #  CARGANDO DOT ANIMATION
    # --------------------------------------------------
    def _start_dots(self):
        self._tick_dots()
 
    def _tick_dots(self):
        self._dots_phase = (self._dots_phase + 1) % 3
        if self._current_mood == "CARGANDO":
            self._draw("CARGANDO")
            self._dots_job = self.after(300, self._tick_dots)
 
    def stop(self):
        if self._bounce_job:
            self.after_cancel(self._bounce_job)
        if self._dots_job:
            self.after_cancel(self._dots_job)
 
    # --------------------------------------------------
    #  PUBLIC API
    # --------------------------------------------------
    def set_mood(self, mood):
        was_cargando = self._current_mood == "CARGANDO"
        self._current_mood = mood
        if mood == "CARGANDO":
            self._dots_phase = 0
            self._start_dots()
        self._draw(mood)
 
 
# ======================================================
#  INTERFAZ GRAFICA
# ======================================================
 
class MochiGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("[ MOCHI — OLED PET ]")
        self.geometry("700x760")
        self.resizable(False, False)
        self.configure(bg=BG_MAIN)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
 
        self._tw_job       = None
        self._engine_ready = False
        self._blink_job    = None
        self._blink_state  = True
 
        self._build_ui()
        self._start_load_engine()
        self._start_blink()
 
    # --------------------------------------------------
    def _build_ui(self):
        # Title
        tk.Label(
            self, text="✦  MOCHI · OLED PET  ✦",
            font=FONT_TITLE, bg=BG_MAIN, fg=C_STROKE,
        ).pack(pady=(10, 4))
 
        # ---- OLED screen bezel ----
        bezel = tk.Frame(self, bg="#0a0a0a", padx=5, pady=5)
        bezel.pack(padx=30, pady=(0, 2))
 
        screen = tk.Frame(bezel, bg=BG_MAIN)
        screen.pack()
 
        # Clock (top-left)
        self.clock_lbl = tk.Label(
            screen, text="00:00",
            font=("Courier New", 14, "bold"),
            bg=BG_MAIN, fg="#00ffee",
        )
        self.clock_lbl.grid(row=0, column=0, sticky="w", padx=(4, 0), pady=(2, 0))
 
        # Stats (top-right)
        stats_frame = tk.Frame(screen, bg=BG_MAIN)
        stats_frame.grid(row=0, column=1, sticky="ne", padx=(0, 4), pady=(2, 0))
        self._stat_bars = []
        for label in ("A", "H", "E"):
            f = tk.Frame(stats_frame, bg=BG_MAIN)
            f.pack(anchor="e")
            tk.Label(f, text=label, font=("Courier New", 8),
                     bg=BG_MAIN, fg=C_STROKE, width=1).pack(side="left")
            bar_bg = tk.Frame(f, bg="#001122", width=60, height=5)
            bar_bg.pack(side="left", padx=(2, 0))
            bar_bg.pack_propagate(False)
            fill = tk.Frame(bar_bg, bg=C_STROKE, height=5)
            fill.place(x=0, y=0, width=42, height=5)
            self._stat_bars.append(fill)
 
        # Pig canvas
        self.pig = PigCanvas(screen, width=260, height=200)
        self.pig.grid(row=1, column=0, columnspan=2, pady=(0, 2))
 
        # Mood label (bottom-right, blinking)
        self.mood_lbl = tk.Label(
            screen, text="HAPPY!",
            font=("Courier New", 13, "bold"),
            bg=BG_MAIN, fg=C_STROKE,
        )
        self.mood_lbl.grid(row=2, column=1, sticky="se", padx=(0, 6), pady=(0, 4))
 
        # ---- Chat log ----
        log_frame = tk.Frame(self, bg="#111111")
        log_frame.pack(padx=16, pady=(4, 4), fill="both", expand=True)
 
        self.chat_log = tk.Text(
            log_frame,
            font=FONT_MONO,
            bg="#111111", fg=FG_GREEN,
            insertbackground=FG_GREEN,
            wrap="word",
            state="disabled",
            relief="flat",
            padx=6, pady=6,
            cursor="arrow",
            height=10,
        )
        sb = tk.Scrollbar(log_frame, command=self.chat_log.yview,
                          bg="#111111", troughcolor=BG_MAIN,
                          activebackground=FG_GRAY)
        self.chat_log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.chat_log.pack(side="left", fill="both", expand=True)
 
        self.chat_log.tag_configure("user",   foreground=FG_CYAN)
        self.chat_log.tag_configure("mochi",  foreground=FG_GREEN)
        self.chat_log.tag_configure("system", foreground=FG_GRAY)
 
        # ---- Input ----
        bottom = tk.Frame(self, bg=BG_MAIN)
        bottom.pack(padx=16, pady=(0, 12), fill="x")
 
        self.input_var = tk.StringVar()
        self.input_field = tk.Entry(
            bottom,
            textvariable=self.input_var,
            font=FONT_MONO,
            bg=BG_INPUT, fg=FG_WHITE,
            insertbackground=FG_WHITE,
            relief="flat",
        )
        self.input_field.pack(side="left", fill="x", expand=True,
                               ipady=6, padx=(0, 8))
        self.input_field.bind("<Return>", self._on_send)
 
        self.send_btn = tk.Button(
            bottom,
            text="ENVIAR",
            font=("Courier New", 11, "bold"),
            bg=FG_GREEN, fg=BG_MAIN,
            activebackground="#22cc00",
            relief="flat",
            cursor="hand2",
            command=self._on_send,
        )
        self.send_btn.pack(side="right", ipady=6, ipadx=10)
 
        # Start clock
        self._tick_clock()
 
    # --------------------------------------------------
    def _tick_clock(self):
        import time
        t = time.localtime()
        self.clock_lbl.configure(
            text=f"{t.tm_hour:02d}:{t.tm_min:02d}"
        )
        self.after(10000, self._tick_clock)
 
    def _start_blink(self):
        def _blink():
            self._blink_state = not self._blink_state
            self.mood_lbl.configure(
                fg=C_STROKE if self._blink_state else BG_MAIN
            )
            self._blink_job = self.after(800, _blink)
        self._blink_job = self.after(800, _blink)
 
    # --------------------------------------------------
    def _start_load_engine(self):
        self.pig.set_mood("CARGANDO")
        self.mood_lbl.configure(text="...")
        self._log("system", ">> Cargando MascotaLM...\n")
        self.send_btn.configure(state="disabled")
 
        def _load():
            ok, err = load_engine()
            self.after(0, lambda: self._on_engine_loaded(ok, err))
 
        threading.Thread(target=_load, daemon=True).start()
 
    def _on_engine_loaded(self, ok, err):
        if ok:
            self._engine_ready = True
            self._set_mood("FELIZ")
            self._log("system", ">> Mochi lista!\n")
            self._typewrite("hola. te estaba esperando.", emotion="FELIZ")
            self.send_btn.configure(state="normal")
            self.input_field.focus()
        else:
            self._set_mood("TRISTE")
            self._log("system", f"[ERROR] No se pudo cargar el modelo:\n  {err}\n")
            self._log("system", "  Verifica CHECKPOINT y TOKENIZER en gui_mochi.py\n")
 
    # --------------------------------------------------
    def _on_send(self, event=None):
        if not self._engine_ready:
            return
        text = self.input_var.get().strip()
        if not text:
            return
 
        self.input_var.set("")
        self.send_btn.configure(state="disabled")
        self.input_field.configure(state="disabled")
        self._log("user", f"Tu > {text}\n")
        self._set_mood("CARGANDO")
 
        def _query():
            emotion, reply = ask_mochi(text)
            self.after(0, lambda: self._on_reply(emotion, reply))
 
        threading.Thread(target=_query, daemon=True).start()
 
    def _on_reply(self, emotion, reply):
        self._set_mood(emotion)
        self._typewrite(reply, emotion=emotion, callback=self._unlock_input)
 
    def _unlock_input(self):
        self.send_btn.configure(state="normal")
        self.input_field.configure(state="normal")
        self.input_field.focus()
 
    def _set_mood(self, state):
        mood = state.upper()
        self.pig.set_mood(mood)
        label = EMOTION_LABELS.get(mood, mood)
        self.mood_lbl.configure(text=label)
 
    # --------------------------------------------------
    def _log(self, tag, text):
        self.chat_log.configure(state="normal")
        self.chat_log.insert("end", text, tag)
        self.chat_log.see("end")
        self.chat_log.configure(state="disabled")
 
    def _typewrite(self, full_text, emotion=None, callback=None):
        if self._tw_job is not None:
            self.after_cancel(self._tw_job)
            self._tw_job = None
 
        if emotion and emotion != "CARGANDO":
            self._log("system", f"[{emotion}] ")
 
        self._log("mochi", "Mochi > ")
 
        chars = list(full_text)
        idx   = [0]
 
        def _tick():
            if idx[0] < len(chars):
                self._log("mochi", chars[idx[0]])
                idx[0] += 1
                self._tw_job = self.after(TYPEWRITER_DELAY_MS, _tick)
            else:
                self._log("mochi", "\n")
                self._tw_job = None
                if callback:
                    callback()
 
        _tick()
 
    def _on_close(self):
        if self._tw_job:
            self.after_cancel(self._tw_job)
        if self._blink_job:
            self.after_cancel(self._blink_job)
        self.pig.stop()
        self.destroy()
 
 
# ======================================================
#  PUNTO DE ENTRADA
# ======================================================
 
if __name__ == "__main__":
    import signal
 
    app = MochiGUI()
    signal.signal(signal.SIGINT, signal.SIG_IGN)
 
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app._on_close()
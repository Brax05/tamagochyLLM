#!/usr/bin/env python3
"""
gui_mochi.py - Interfaz grafica para Mochi (MascotaLM)
Usa tkinter estandar - sin dependencias externas.

Ejecutar:
    python gui_mochi.py
"""

import tkinter as tk
import sys
import os
import threading
import re

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
#  Si 'tokenizers' no esta disponible, agrega el .venv
#  del proyecto a sys.path automaticamente.
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
            # Python 3.x en Linux/Mac
            for sp in glob.glob(os.path.join(venv_dir, "lib", "python*", "site-packages")):
                sys.path.insert(0, sp)

_add_venv_if_needed()

# ======================================================
#  ARTE ASCII  (puedes editar estos strings libremente)
# ======================================================

MOCHI_NEUTRAL = r"""
  .-~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~-.
  |    /\_____/\       ~ ~ ~ ~ ~       |
  |   /  -     -  \                    |
  |  ( ==  \-/  == )                   |
  |   \    ___    /                    |
  |    '-_______-'                     |
  |      ||     ||                     |
  |    (__)     (__)                   |
  '-~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~-'"""

MOCHI_FELIZ = r"""
  .-~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~-.
  |    /\_____/\       ~ ~ ~ ~ ~       |
  |   /  ^     ^  \                    |
  |  ( ==  \^/  == )    (^o^)/         |
  |   \    ___    /                    |
  |    '-_______-'    ~ Feliz!! ~      |
  |      ||     ||                     |
  |    (__)     (__)                   |
  '-~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~-'"""

MOCHI_TRISTE = r"""
  .-~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~-.
  |    /\_____/\                       |
  |   /  T     T  \   . . .            |
  |  ( ==   v   == )   ( T_T )         |
  |   \    _____   /                   |
  |    '-_________-'  ~ Triste... ~    |
  |      ||     ||                     |
  |    (__)     (__)                   |
  '-~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~-'"""

MOCHI_ENOJADO = r"""
  .-~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~-.
  |    /\_____/\       !! !! !!        |
  |   /  >     <  \                    |
  |  ( == ~~~~~ == )    (>_<)          |
  |   \    _____   /                   |
  |    '-_________-'  ~ Enojada! ~     |
  |      ||     ||                     |
  |    (__)     (__)                   |
  '-~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~-'"""

MOCHI_CARGANDO = r"""
  .-~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~-.
  |    /\_____/\                       |
  |   /  .     .  \                    |
  |  ( ==  ...  == )   pensando...     |
  |   \    _____   /                   |
  |    '-_________-'                   |
  |      ||     ||                     |
  |    (__)     (__)                   |
  '-~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~-'"""

ASCII_STATES = {
    "FELIZ":    MOCHI_FELIZ,
    "TRISTE":   MOCHI_TRISTE,
    "ENOJADO":  MOCHI_ENOJADO,
    "NEUTRAL":  MOCHI_NEUTRAL,
    "CARGANDO": MOCHI_CARGANDO,
}

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


def detect_emotion(text):
    m = _TAG_RE.match(text)
    if m:
        tag   = m.group(1).upper()
        clean = text[m.end():].strip()
        return (tag if tag in ASCII_STATES else "NEUTRAL"), clean
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
#  COLORES Y FUENTES
# ======================================================
BG_MAIN  = "#0d0d0d"
BG_PANEL = "#111111"
BG_INPUT = "#1a1a1a"
FG_GREEN = "#39ff14"
FG_CYAN  = "#00bfff"
FG_GRAY  = "#888888"
FG_WHITE = "#ffffff"

FONT_MONO  = ("Courier New", 11)
FONT_ART   = ("Courier New", 10)
FONT_TITLE = ("Courier New", 12, "bold")

TYPEWRITER_DELAY_MS = 20

# ======================================================
#  INTERFAZ GRAFICA
# ======================================================

class MochiGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("[ MOCHI - Mascota Virtual ]")
        self.geometry("700x720")
        self.resizable(False, False)
        self.configure(bg=BG_MAIN)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._tw_job       = None
        self._engine_ready = False

        self._build_ui()
        self._start_load_engine()

    def _build_ui(self):
        tk.Label(
            self, text="[ MOCHI - MASCOTA VIRTUAL ]",
            font=FONT_TITLE, bg=BG_MAIN, fg=FG_GREEN,
        ).pack(pady=(10, 4))

        art_frame = tk.Frame(self, bg=BG_PANEL)
        art_frame.pack(padx=16, pady=(0, 2), fill="x")

        self.art_label = tk.Label(
            art_frame, text=MOCHI_NEUTRAL,
            font=FONT_ART, bg=BG_PANEL, fg=FG_GREEN,
            justify="left", anchor="w",
        )
        self.art_label.pack(padx=8, pady=4, fill="x")

        self.state_label = tk.Label(
            self, text="[ NEUTRAL ]",
            font=("Courier New", 10),
            bg=BG_MAIN, fg=FG_GRAY,
        )
        self.state_label.pack(pady=(0, 2))

        log_frame = tk.Frame(self, bg=BG_PANEL)
        log_frame.pack(padx=16, pady=(2, 4), fill="both", expand=True)

        self.chat_log = tk.Text(
            log_frame,
            font=FONT_MONO,
            bg=BG_PANEL, fg=FG_GREEN,
            insertbackground=FG_GREEN,
            wrap="word",
            state="disabled",
            relief="flat",
            padx=6, pady=6,
            cursor="arrow",
        )
        sb = tk.Scrollbar(
            log_frame, command=self.chat_log.yview,
            bg=BG_PANEL, troughcolor=BG_MAIN,
            activebackground=FG_GRAY,
        )
        self.chat_log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.chat_log.pack(side="left", fill="both", expand=True)

        self.chat_log.tag_configure("user",   foreground=FG_CYAN)
        self.chat_log.tag_configure("mochi",  foreground=FG_GREEN)
        self.chat_log.tag_configure("system", foreground=FG_GRAY)

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

    def _start_load_engine(self):
        self._set_ascii("CARGANDO")
        self._log("system", ">> Cargando MascotaLM...\n")
        self.send_btn.configure(state="disabled")

        def _load():
            ok, err = load_engine()
            self.after(0, lambda: self._on_engine_loaded(ok, err))

        threading.Thread(target=_load, daemon=True).start()

    def _on_engine_loaded(self, ok, err):
        if ok:
            self._engine_ready = True
            self._set_ascii("FELIZ")
            self._log("system", ">> Mochi lista!\n")
            self._typewrite("hola. te estaba esperando.", emotion="FELIZ")
            self.send_btn.configure(state="normal")
            self.input_field.focus()
        else:
            self._set_ascii("TRISTE")
            self._log("system", f"[ERROR] No se pudo cargar el modelo:\n  {err}\n")
            self._log("system", "  Verifica CHECKPOINT y TOKENIZER en gui_mochi.py\n")

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
        self._set_ascii("CARGANDO")

        def _query():
            emotion, reply = ask_mochi(text)
            self.after(0, lambda: self._on_reply(emotion, reply))

        threading.Thread(target=_query, daemon=True).start()

    def _on_reply(self, emotion, reply):
        self._set_ascii(emotion)
        self._typewrite(reply, emotion=emotion, callback=self._unlock_input)

    def _unlock_input(self):
        self.send_btn.configure(state="normal")
        self.input_field.configure(state="normal")
        self.input_field.focus()

    def _set_ascii(self, state):
        art = ASCII_STATES.get(state, MOCHI_NEUTRAL)
        self.art_label.configure(text=art)
        self.state_label.configure(text=f"[ {state} ]")

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
        if self._tw_job is not None:
            self.after_cancel(self._tw_job)
        self.destroy()


# ======================================================
#  PUNTO DE ENTRADA
# ======================================================

if __name__ == "__main__":
    import signal

    app = MochiGUI()

    # Ignorar Ctrl+C / SIGINT del sistema operativo.
    # El cierre correcto es el boton X de la ventana.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    try:
        app.mainloop()
    except KeyboardInterrupt:
        app._on_close()

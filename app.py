"""
Archivo principal de la aplicación.

Responsable de:
- Crear la ventana (tkinter)
- Mostrar chat e interfaz
- Conectar la UI con el motor de IA
- Actualizar la mascota según la emoción

Orquesta toda la aplicación.
"""

import threading
import tkinter as tk

from core.mochi_engine import MochiEngine
from core.emotion_mapper import map_emotion_to_sprite
from ui.cat_sprite import CatAnimator, SURFACE_WIDTH, SURFACE_HEIGHT, WINDOW_SCALE
from PIL import Image, ImageTk

import pygame


BG_MAIN = "#0d0d0d"
BG_PANEL = "#111111"
BG_INPUT = "#1a1a1a"
FG_GREEN = "#39ff14"
FG_CYAN = "#00bfff"
FG_GRAY = "#888888"
FG_WHITE = "#ffffff"

FONT_MONO = ("Courier New", 11)
FONT_TITLE = ("Courier New", 12, "bold")
TYPEWRITER_DELAY_MS = 20


class MochiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("[ MOCHI - Mascota Virtual ]")
        self.geometry("760x900")
        self.resizable(True, True)
        self.configure(bg=BG_MAIN)

        self.engine = MochiEngine()
        self.cat = CatAnimator()

        self._tw_job = None
        self._engine_ready = False
        self._pygame_initialized = False

        self._build_ui()
        self._init_pygame_surface()
        self._start_load_engine()
        self._animation_loop()

    def _build_ui(self):
        tk.Label(
            self,
            text="[ MOCHI - MASCOTA VIRTUAL ]",
            font=FONT_TITLE,
            bg=BG_MAIN,
            fg=FG_GREEN,
        ).pack(pady=(10, 4))

        visual_frame = tk.Frame(self, bg=BG_PANEL)
        visual_frame.pack(padx=16, pady=(0, 6), fill="x")

        self.cat_canvas = tk.Canvas(
            visual_frame,
            width=SURFACE_WIDTH,
            height=SURFACE_HEIGHT,
            bg="black",
            highlightthickness=0,
        )
        self.cat_canvas.pack(padx=8, pady=8)

        self.state_label = tk.Label(
            self,
            text="[ NEUTRAL ]",
            font=("Courier New", 10),
            bg=BG_MAIN,
            fg=FG_GRAY,
        )
        self.state_label.pack(pady=(0, 4))

        log_frame = tk.Frame(self, bg=BG_PANEL)
        log_frame.pack(padx=16, pady=(2, 4), fill="both", expand=False)

        self.chat_log = tk.Text(
            log_frame,
            font=FONT_MONO,
            bg=BG_PANEL,
            fg=FG_GREEN,
            insertbackground=FG_GREEN,
            wrap="word",
            state="disabled",
            relief="flat",
            padx=6,
            pady=6,
            cursor="arrow",
        )

        sb = tk.Scrollbar(log_frame, command=self.chat_log.yview)
        self.chat_log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.chat_log.pack(side="left", fill="both", expand=True)

        self.chat_log.tag_configure("user", foreground=FG_CYAN)
        self.chat_log.tag_configure("mochi", foreground=FG_GREEN)
        self.chat_log.tag_configure("system", foreground=FG_GRAY)

        bottom = tk.Frame(self, bg=BG_MAIN)
        bottom.pack(padx=16, pady=(0, 12), fill="x")

        self.input_var = tk.StringVar()
        self.input_field = tk.Entry(
            bottom,
            textvariable=self.input_var,
            font=FONT_MONO,
            bg=BG_INPUT,
            fg=FG_WHITE,
            insertbackground=FG_WHITE,
            relief="flat",
        )
        self.input_field.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        self.input_field.bind("<Return>", self._on_send)

        self.send_btn = tk.Button(
            bottom,
            text="ENVIAR",
            font=("Courier New", 11, "bold"),
            bg=FG_GREEN,
            fg=BG_MAIN,
            relief="flat",
            cursor="hand2",
            command=self._on_send,
        )
        self.send_btn.pack(side="right", ipady=6, ipadx=10)

    def _init_pygame_surface(self):
        if not self._pygame_initialized:
            pygame.init()
            self._pygame_initialized = True

    def _draw_cat(self):
        surface = self.cat.get_surface()

        # Convertir superficie pygame a imagen PIL
        raw_str = pygame.image.tostring(surface, "RGB")
        img = Image.frombytes("RGB", (SURFACE_WIDTH, SURFACE_HEIGHT), raw_str)

        # Offset flotante puro para subpixel rendering
        offset_y = self.cat.breath_offset * WINDOW_SCALE

        offset_int = int(offset_y)
        frac = offset_y - offset_int

        # Frame A: desplazado al píxel entero más cercano
        final_img = Image.new("RGB", (SURFACE_WIDTH, SURFACE_HEIGHT), (0, 0, 0))
        final_img.paste(img, (0, offset_int))

        # Frame B: desplazado un píxel más, mezclado por la fracción
        if abs(frac) > 0.001:
            shifted = Image.new("RGB", (SURFACE_WIDTH, SURFACE_HEIGHT), (0, 0, 0))
            shifted.paste(img, (0, offset_int + (1 if frac > 0 else -1)))
            final_img = Image.blend(final_img, shifted, abs(frac))

        self._cat_img = ImageTk.PhotoImage(final_img)
        self.cat_canvas.delete("all")
        self.cat_canvas.create_image(0, 0, anchor="nw", image=self._cat_img)

    def _animation_loop(self):
        self.cat.update()
        self._draw_cat()
        self.after(16, self._animation_loop)  # ~60 FPS

    def _start_load_engine(self):
        self._set_emotion("CARGANDO")
        self._log("system", ">> Cargando MascotaLM...\n")
        self.send_btn.configure(state="disabled")

        def _load():
            ok, err = self.engine.load()
            self.after(0, lambda: self._on_engine_loaded(ok, err))

        threading.Thread(target=_load, daemon=True).start()

    def _on_engine_loaded(self, ok, err):
        if ok:
            self._engine_ready = True
            self._set_emotion("FELIZ")
            self._log("system", ">> Mochi lista!\n")
            self._typewrite("hola. te estaba esperando.", emotion="FELIZ")
            self.send_btn.configure(state="normal")
            self.input_field.focus()
        else:
            self._set_emotion("TRISTE")
            self._log("system", f"[ERROR] No se pudo cargar el modelo:\n  {err}\n")

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
        self._set_emotion("CARGANDO")

        def _query():
            emotion, reply = self.engine.ask(text)
            self.after(0, lambda: self._on_reply(emotion, reply))

        threading.Thread(target=_query, daemon=True).start()

    def _on_reply(self, emotion, reply):
        self._set_emotion(emotion)
        self._typewrite(reply, emotion=emotion, callback=self._unlock_input)

    def _unlock_input(self):
        self.send_btn.configure(state="normal")
        self.input_field.configure(state="normal")
        self.input_field.focus()

    def _set_emotion(self, emotion):
        self.state_label.configure(text=f"[ {emotion} ]")
        sprite_mode = map_emotion_to_sprite(emotion)
        self.cat.set_mode(sprite_mode)

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
        idx = [0]

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


if __name__ == "__main__":
    app = MochiApp()
    app.mainloop()
"""
Motor de inteligencia artificial.

Responsable de:
- Cargar el modelo entrenado (.pt)
- Manejar historial de conversación
- Generar respuestas con la LLM
- Detectar emoción en las respuestas

Es la capa lógica de la IA.
"""

import os
import re
import threading

# ======================================================
# RUTAS
# ======================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKPOINT = os.path.join(BASE_DIR, "checkpoints", "best_model.pt")
TOKENIZER = os.path.join(BASE_DIR, "data", "tokenizer.json")

# ======================================================
# DETECTOR DE EMOCIONES
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


def detect_emotion(text: str):
    m = _TAG_RE.match(text)
    if m:
        tag = m.group(1).upper()
        clean = text[m.end():].strip()
        if tag in ("FELIZ", "TRISTE", "ENOJADO", "NEUTRAL", "CARGANDO"):
            return tag, clean
        return "NEUTRAL", clean

    lower = text.lower()
    for emotion, keywords in KEYWORD_MAP.items():
        if any(kw in lower for kw in keywords):
            return emotion, text

    return "NEUTRAL", text


class MochiEngine:
    def __init__(self):
        self._engine = None
        self._engine_lock = threading.Lock()
        self._history = []

    def load(self):
        try:
            from mascotalm.inference import MascotaInference
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
            engine = MascotaInference(CHECKPOINT, TOKENIZER, device=device)

            with self._engine_lock:
                self._engine = engine

            return True, None
        except Exception as exc:
            return False, str(exc)

    def ask(self, user_text: str):
        self._history.append({"role": "user", "content": user_text})

        try:
            with self._engine_lock:
                if self._engine is None:
                    return "TRISTE", "Todavía me estoy despertando... espera un momento."

                result = self._engine.chat_completion(
                    self._history[-4:],
                    temperature=0.65,
                    top_k=35,
                    max_tokens=80,
                )

            raw = result["choices"][0]["message"].get("content", "").strip()
            if not raw:
                return "NEUTRAL", "..."

            emotion, clean = detect_emotion(raw)
            self._history.append({"role": "assistant", "content": clean})

            if len(self._history) > 10:
                self._history[:] = self._history[-10:]

            return emotion, clean

        except Exception as exc:
            return "TRISTE", f"Algo salió mal: {exc}"
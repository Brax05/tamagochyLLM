"""
Mapeador de emociones.

Responsable de:
- Traducir emociones del modelo (FELIZ, TRISTE, etc.)
- Convertirlas en estados visuales del gato (happy, sad, etc.)

Actúa como puente entre IA y UI.
"""

EMOTION_TO_SPRITE = {
    "FELIZ":        "happy",
    "TRISTE":       "sad",
    "ENOJADO":      "angry",
    "NEUTRAL":      "neutral",
    "CARGANDO":     "neutral",
    "AMOR":         "love",
    "CONFUNDIDO":   "confused",
    "NERVIOSO":     "nervous",
    "EMOCIONADO":   "excited",
    "AVERGONZADO":  "embarrassed",
    "ENFERMO":      "sick",
    "DORMIDO":        "sleep",   
    "PRESUMIDO":         "smug",     
    "GUINO":         "wink",     
    "SORPENDIDO":         "surprised", 
}

def map_emotion_to_sprite(emotion: str) -> str:
    return EMOTION_TO_SPRITE.get(emotion.upper(), "neutral")
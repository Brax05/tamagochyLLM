"""Test rápido de MascotaLM (Mochi) — no interactivo."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from mascotalm.inference import MascotaInference

CHECKPOINT = "mascotalm/checkpoints/best_model.pt"
TOKENIZER  = "mascotalm/data/tokenizer.json"

TESTS = [
    ("saludo",     "hola mochi"),
    ("sentimiento","¿cómo estás?"),
    ("comida",     "aquí tienes una pizza"),
    ("hambre",     "¿tienes hambre?"),
    ("jugar",      "¿jugamos?"),
    ("identidad",  "¿quién eres?"),
    ("elogio",     "eres muy linda"),
    ("cariño",     "te quiero mochi"),
    ("chiste",     "cuéntame un chiste"),
    ("noche",      "buenas noches"),
    ("confundida", "¿qué opinas de los impuestos?"),
    ("multi-turno","ya volví, te extrañé"),
]

def main():
    engine = MascotaInference(CHECKPOINT, TOKENIZER, device="cpu")
    print("\n" + "="*60)
    print("  PRUEBA DE MOCHI")
    print("="*60)

    passed = 0
    for category, prompt in TESTS:
        messages = [{"role": "user", "content": prompt}]
        result = engine.chat_completion(messages, temperature=0.6, top_k=30, max_tokens=64)
        reply = result["choices"][0]["message"]["content"]
        ok = len(reply.strip()) > 0
        status = "OK" if ok else "VACIO"
        if ok:
            passed += 1
        print(f"\n[{status}] {category}")
        print(f"  Vos>   {prompt}")
        print(f"  Mochi> {reply}")

    print("\n" + "="*60)
    print(f"Resultado: {passed}/{len(TESTS)} respuestas no vacías")
    print("="*60)

if __name__ == "__main__":
    main()

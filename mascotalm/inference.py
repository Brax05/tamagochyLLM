"""MascotaLM — inferencia / chat con Mochi."""

import json
import os

import torch
from tokenizers import Tokenizer

from .config import MascotaConfig
from .model import MascotaLM


class MascotaInference:
    def __init__(self, checkpoint_path, tokenizer_path, device="cpu"):
        self.device = torch.device(device)
        self.tokenizer = Tokenizer.from_file(tokenizer_path)

        ckpt = torch.load(checkpoint_path, map_location=self.device, weights_only=False)

        config_dir = os.path.dirname(os.path.abspath(checkpoint_path))
        config_path = os.path.join(config_dir, "config.json")

        if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
            state_dict = ckpt["model_state_dict"]
        else:
            state_dict = ckpt

        if os.path.exists(config_path):
            with open(config_path, encoding="utf-8") as f:
                cfg = json.load(f)
            model_cfg = cfg.get("model", cfg)
            self.config = MascotaConfig(
                vocab_size=model_cfg.get("vocab_size", 4096),
                max_seq_len=model_cfg.get("max_seq_len", 128),
                d_model=model_cfg.get("d_model", 384),
                n_layers=model_cfg.get("n_layers", 6),
                n_heads=model_cfg.get("n_heads", 6),
                ffn_hidden=model_cfg.get("ffn_hidden", 768),
                dropout=model_cfg.get("dropout", 0.1),
            )
        elif isinstance(ckpt, dict) and "config" in ckpt:
            valid = set(MascotaConfig.__dataclass_fields__.keys())
            self.config = MascotaConfig(**{k: v for k, v in ckpt["config"].items() if k in valid})
        else:
            print("Advertencia: sin config, usando valores por defecto")
            self.config = MascotaConfig()

        self.model = MascotaLM(self.config).to(self.device)
        filtered = {k: v for k, v in state_dict.items() if k in self.model.state_dict()}
        self.model.load_state_dict(filtered)
        self.model.eval()

        total, _ = self.model.param_count()
        print(f"MascotaLM cargado: {total/1e6:.1f}M params")

    def chat_completion(self, messages, temperature=0.7, max_tokens=64, top_k=50, **kwargs):
        prompt = self._format_prompt(messages)
        input_ids = self.tokenizer.encode(prompt).ids
        prompt_tokens = len(input_ids)
        input_t = torch.tensor([input_ids], dtype=torch.long, device=self.device)

        output_t, _ = self.model.generate(input_t, max_tokens, temperature, top_k)
        output_text = self.tokenizer.decode(output_t[0].tolist()[prompt_tokens:])

        if "<|im_end|>" in output_text:
            output_text = output_text.split("<|im_end|>")[0]
        if "<|im_start|>" in output_text:
            output_text = output_text.split("<|im_start|>")[0]

        return {
            "choices": [{
                "message": {"role": "assistant", "content": output_text.strip()},
            }],
        }

    def _format_prompt(self, messages):
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content") or ""
            if role == "system":
                continue
            parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")
        parts.append("<|im_start|>assistant\n")
        return "\n".join(parts)


def main():
    import argparse
    p = argparse.ArgumentParser(description="Chatear con Mochi")
    p.add_argument("--checkpoint", default="checkpoints/best_model.pt")
    p.add_argument("--tokenizer", default="data/tokenizer.json")
    p.add_argument("--device", default="cpu")
    args = p.parse_args()

    engine = MascotaInference(args.checkpoint, args.tokenizer, args.device)
    print("\nMochi Chat (escribí 'chau' para salir)")
    history = []  # guarda el historial de la conversación
    while True:
        try:
            inp = input("\nVos> ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not inp:
            continue
        if inp.lower() in ("chau", "salir", "exit", "q"):
            print("Mochi> bueno. chau. volvé pronto.")
            break

        history.append({"role": "user", "content": inp})

        # Pasar los últimos 3 turnos (6 mensajes) para no exceder seq_len
        context = history[-4:]
        result = engine.chat_completion(
            context,
            temperature=0.6,
            top_k=30,
            max_tokens=64,
        )
        msg = result["choices"][0]["message"]
        reply = msg.get("content", "")
        if reply:
            print(f"Mochi> {reply}")
            history.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()

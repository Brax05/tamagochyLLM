"""
Exportar datos de entrenamiento de MascotaLM a HuggingFace.

Uso:
    # Configurar .env con HF_TOKEN y HF_REPO
    python tools/export_dataset.py

    # O pasar directamente
    python tools/export_dataset.py --repo Brax055/Mascota_virtual --token hf_xxx
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())


def generate_data(n_samples=60000, eval_ratio=0.05):
    import random
    random.seed(42)

    from mascotalm.generate_data import (
        gen_greeting, gen_feeling, gen_food, gen_hungry, gen_play,
        gen_bored, gen_bye, gen_about, gen_praise, gen_hug,
        gen_sad, gen_happy, gen_confused, gen_night, gen_morning,
        gen_sick, gen_tired, gen_levelup, gen_affection, gen_ignore,
        gen_dream, gen_weather, gen_curious, gen_gift, gen_care,
        gen_colors, gen_music, gen_friends, gen_size, gen_joke,
        gen_future, gen_memory, gen_adventure,
    )

    topics = [
        gen_greeting, gen_feeling, gen_food, gen_hungry, gen_play,
        gen_bored, gen_bye, gen_about, gen_praise, gen_hug,
        gen_sad, gen_happy, gen_confused, gen_night, gen_morning,
        gen_sick, gen_tired, gen_levelup, gen_affection, gen_ignore,
        gen_dream, gen_weather, gen_curious, gen_gift, gen_care,
        gen_colors, gen_music, gen_friends, gen_size, gen_joke,
        gen_future, gen_memory, gen_adventure,
    ]

    per_topic = max(1, n_samples // len(topics))
    samples = []
    for gen in topics:
        for _ in range(per_topic):
            try:
                s = gen()
                samples.append({
                    "input": s["input"],
                    "output": s["output"],
                    "category": s["category"],
                })
            except Exception:
                pass

    random.shuffle(samples)
    n_eval = int(len(samples) * eval_ratio)
    return samples[n_eval:], samples[:n_eval]


def push_to_hub(train_data, test_data, repo_id, token):
    from datasets import Dataset, DatasetDict
    from huggingface_hub import HfApi

    ds = DatasetDict({
        "train": Dataset.from_list(train_data),
        "test": Dataset.from_list(test_data),
    })

    print(f"\nDataset:")
    print(f"  Train: {len(train_data):,} samples")
    print(f"  Test:  {len(test_data):,} samples")
    print(f"  Columns: {list(ds['train'].column_names)}")
    print(f"  Categories: {len(set(r['category'] for r in train_data))}")
    print()

    print(f"Subiendo a {repo_id}...")
    ds.push_to_hub(repo_id, token=token)

    card_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset_card.md")
    if os.path.exists(card_path):
        api = HfApi(token=token)
        api.upload_file(
            path_or_fileobj=card_path,
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="dataset",
        )
        print("README.md subido")

    print(f"Listo! https://huggingface.co/datasets/{repo_id}")


def save_local(train_data, test_data, output_dir="dataset"):
    os.makedirs(output_dir, exist_ok=True)
    for name, data in [("train.jsonl", train_data), ("test.jsonl", test_data)]:
        path = os.path.join(output_dir, name)
        with open(path, "w") as f:
            for row in data:
                f.write(json.dumps(row) + "\n")
        print(f"Guardado {path} ({len(data):,} samples)")


def main():
    parser = argparse.ArgumentParser(description="Exportar dataset MascotaLM a HuggingFace")
    parser.add_argument("--repo", default="Brax055/Mascota_virtual",
                        help="HuggingFace repo (default: Brax055/Mascota_virtual)")
    parser.add_argument("--token", default=None, help="HuggingFace token")
    parser.add_argument("--samples", type=int, default=60000, help="Cantidad de samples")
    parser.add_argument("--local-only", action="store_true", help="Solo guardar local sin subir a HF")
    parser.add_argument("--output-dir", default="dataset", help="Directorio local de salida")
    args = parser.parse_args()

    load_env()

    token = args.token or os.environ.get("HF_TOKEN")
    repo = args.repo or os.environ.get("HF_DATASET", "Brax055/Mascota_virtual")

    if not args.local_only and not token:
        print("Error: Sin token HF. Configurá HF_TOKEN en .env o pasá --token")
        sys.exit(1)

    print(f"Generando {args.samples:,} samples...")
    train_data, test_data = generate_data(args.samples)

    save_local(train_data, test_data, args.output_dir)

    if not args.local_only:
        push_to_hub(train_data, test_data, repo, token)


if __name__ == "__main__":
    main()

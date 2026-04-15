"""MascotaLM — configuración del modelo."""

from dataclasses import dataclass


@dataclass
class MascotaConfig:
    vocab_size: int = 4096
    max_seq_len: int = 256    # era 128 — más contexto para multi-turno
    d_model: int = 384
    n_layers: int = 6
    n_heads: int = 6
    ffn_hidden: int = 768
    dropout: float = 0.1

    # Tokens especiales
    pad_id: int = 0
    bos_id: int = 1           # <|im_start|>
    eos_id: int = 2           # <|im_end|>


@dataclass
class TrainConfig:
    batch_size: int = 16                  # era 32 — reducido porque seq_len duplicó
    learning_rate: float = 3e-4
    min_lr: float = 3e-5
    weight_decay: float = 0.1
    warmup_steps: int = 400     # era 200 — más warmup para dataset más complejo
    max_steps: int = 20000      # era 15000 — más pasos para separar bien las 36 categorías
    eval_interval: int = 200
    save_interval: int = 500
    grad_clip: float = 1.0
    device: str = "auto"
    seed: int = 42
    data_dir: str = "data"
    output_dir: str = "checkpoints"

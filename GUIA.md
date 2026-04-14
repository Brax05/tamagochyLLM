# Guía técnica — MascotaLM (Mochi)

Esta guía explica cómo funciona el LLM internamente y qué archivos tocar para cambiar el comportamiento de Mochi.

---

## Índice

1. [Cómo funciona este LLM](#1-cómo-funciona-este-llm)
2. [Flujo completo de datos](#2-flujo-completo-de-datos)
3. [Archivos clave y qué cambiar en cada uno](#3-archivos-clave-y-qué-cambiar-en-cada-uno)
   - [generate_data.py — Personalidad y respuestas](#31-generate_datapy--personalidad-y-respuestas)
   - [config.py — Tamaño del modelo y entrenamiento](#32-configpy--tamaño-del-modelo-y-entrenamiento)
   - [inference.py — Comportamiento en tiempo real](#33-inferencepy--comportamiento-en-tiempo-real)
   - [model.py — Arquitectura del transformer](#34-modelpy--arquitectura-del-transformer)
   - [prepare_data.py — Tokenizer](#35-prepare_datapy--tokenizer)
4. [Reglas de oro para no romper el modelo](#4-reglas-de-oro-para-no-romper-el-modelo)
5. [Recetas rápidas](#5-recetas-rápidas)

---

## 1. Cómo funciona este LLM

### Visión general

```
Usuario escribe texto
        ↓
  Tokenizador BPE        → convierte texto a números (tokens)
        ↓
  Transformer Decoder    → predice el siguiente token, uno por uno
        ↓
  Detokenizador          → convierte números de vuelta a texto
        ↓
    Mochi responde
```

Este es un **transformer decoder-only** (como GPT pero mucho más pequeño). No "entiende" el texto — aprende patrones estadísticos de cuál token sigue a cuál, dado el contexto de entrenamiento.

### El tokenizador BPE

BPE (Byte Pair Encoding) divide el texto en subpalabras frecuentes. Con `vocab_size=4096`, el modelo conoce ~2000 tokens reales (el resto son especiales o poco usados).

```
"hola mochi" → [305, 1847]           # cada número es un token
"buenas noches" → [892, 1203]
"<|im_start|>" → [1]                 # token especial de inicio de turno
"<|im_end|>"   → [2]                 # token especial de fin de turno
```

### Formato de conversación en el dataset

Cada ejemplo de entrenamiento tiene este formato exacto:

```
<|im_start|>user
hola mochi<|im_end|>
<|im_start|>assistant
hola. te estaba esperando.<|im_end|>
```

El modelo aprende a, dado `<|im_start|>assistant\n`, continuar con la respuesta correcta.

### Generación (inferencia)

El modelo genera token por token hasta encontrar `<|im_end|>`:

```
Input:  [1, "user", "\n", "hola", " mochi", 2, "\n", 1, "assistant", "\n"]
                                                                           ↑
                                                              el modelo genera desde aquí
Output: ["hola", ".", " te", " estaba", " esperando", ".", 2]
                                                             ↑ para aquí
```

Dos parámetros controlan cómo genera:
- **`temperature`**: valores altos (>0.8) = más creativo/impredecible, bajos (<0.5) = más repetitivo/seguro
- **`top_k`**: solo considera los K tokens más probables en cada paso. Menos K = más conservador

---

## 2. Flujo completo de datos

```
generate_data.py          prepare_data.py           train.py
      │                         │                       │
      │  genera 60K              │  entrena tokenizer    │  loop de entrenamiento
      │  conversaciones          │  BPE sobre el         │  con AdamW + cosine LR
      │  sintéticas              │  dataset              │
      ↓                         ↓                       ↓
data/train.jsonl  →   data/tokenizer.json  →  checkpoints/best_model.pt
data/eval.jsonl
```

Para re-entrenar desde cero tras cambios:
```bash
python -m mascotalm prepare   # regenera dataset + tokenizer
python -m mascotalm train     # entrena el modelo
python -m mascotalm chat      # prueba con Mochi
```

---

## 3. Archivos clave y qué cambiar en cada uno

---

### 3.1 `generate_data.py` — Personalidad y respuestas

**Este es el archivo más importante para cambiar el comportamiento de Mochi.**

El modelo aprende a hablar directamente de este archivo. Si quieres que Mochi diga algo diferente, lo cambias aquí.

#### Estructura

El archivo tiene tres secciones:

**A) Listas de vocabulario** (líneas 17–67)
```python
COMIDAS = ["dulces", "pizza", "tacos", ...]   # lo que Mochi menciona cuando habla de comida
SENTIMIENTOS = ["feliz", "aburrida", ...]      # cómo se describe
ACTIVIDADES = ["dando vueltas", ...]           # qué hace cuando está sola
COSAS_HUMANAS = ["impuestos", "wifi", ...]     # conceptos que no entiende
```

**B) Funciones de respuesta** `r_*()` (líneas 74–501)

Cada función devuelve una respuesta aleatoria de Mochi para una situación:

```python
def r_saludo():          # cuando el usuario saluda
def r_sentimiento():     # cuando preguntan cómo está
def r_hambrienta():      # cuando tiene hambre
def r_llena():           # cuando le dan comida
def r_aburrida():        # cuando está aburrida
def r_jugar():           # cuando quieren jugar
def r_triste():          # cuando está triste
def r_contenta():        # cuando está feliz
def r_cariño():          # cuando le dicen que la quieren
def r_confundida(cosa):  # cuando no entiende algo humano
def r_noche():           # buenas noches
def r_mañana():          # buenos días
def r_quien():           # cuando preguntan quién es
def r_elogio():          # cuando la elogian
def r_abrazo():          # cuando le dan un abrazo
def r_chiste():          # cuando piden un chiste
# ... y más
```

**C) Conversaciones multi-turno** `conv_*()` (líneas 508–716)

Secuencias de 2-3 turnos que enseñan contexto:

```python
def conv_hambre_comida():     # usuario pregunta si tiene hambre → le da comida → pregunta si estuvo rico
def conv_juego():             # quieren jugar → juegan → comentan cómo estuvo
def conv_tristeza_apoyo():    # Mochi está triste → usuario la acompaña → mejora
# ... etc
```

**D) `SINGLE_TURN`** (líneas 742–792)

Lista de pares (input del usuario → función de respuesta):
```python
("saludo",  lambda: (pick(["hola mochi", "hey", ...]), r_saludo())),
("comida",  lambda: (pick(["aquí tienes pizza", ...]), r_llena())),
```

**E) `MULTI_TURN_CONVS`** (líneas 725–740)

Lista de las funciones `conv_*` que se usan para generar el 60% multi-turno del dataset.

#### Cómo agregar un tópico nuevo

**Paso 1** — Crear la función de respuesta:
```python
def r_nuevo_topico():
    return pick([
        "respuesta 1 de mochi.",
        f"respuesta con {pick(COMIDAS)} para variedad.",
        "respuesta 3.",
    ])
```

**Paso 2** — Agregarla a `SINGLE_TURN`:
```python
("nuevo_topico", lambda: (pick(["input 1", "input 2"]), r_nuevo_topico())),
```

**Paso 3** — Opcional: crear una conversación multi-turno:
```python
def conv_nuevo_topico():
    return [
        ("input turno 1", r_respuesta_1()),
        ("input turno 2", r_nuevo_topico()),
    ]
```
Y agregarla a `MULTI_TURN_CONVS`.

**Paso 4** — Re-entrenar:
```bash
python -m mascotalm prepare && python -m mascotalm train
```

#### Regla crítica sobre respuestas

Las respuestas de Mochi **NO** deben contener frases que el usuario usaría como input. Por ejemplo:
- Mal: `r_aburrida()` tenía `"¿jugamos?"` — el modelo aprendía a decirlo como respuesta en contextos incorrectos
- Bien: las respuestas de Mochi deben ser claramente del "lado de Mochi", nunca preguntas que el usuario haría

---

### 3.2 `config.py` — Tamaño del modelo y entrenamiento

Dos dataclasses que controlan todo:

#### `MascotaConfig` — arquitectura del transformer

```python
@dataclass
class MascotaConfig:
    vocab_size: int = 4096    # cuántas palabras/subpalabras conoce
    max_seq_len: int = 256    # longitud máxima de contexto (en tokens)
    d_model: int = 384        # dimensión interna del transformer
    n_layers: int = 6         # número de capas del transformer
    n_heads: int = 6          # cabezas de atención por capa
    ffn_hidden: int = 768     # neuronas en la capa feed-forward (= d_model * 2)
    dropout: float = 0.1      # regularización
```

Relación entre parámetros y tamaño del modelo:
- `d_model` y `n_layers` son los más impactantes. Doblar `d_model` cuadruplica params.
- Modelo actual: ~8.8M params

Si quieres un modelo más capaz (pero más lento de entrenar):
```python
d_model: int = 512    # era 384
n_layers: int = 8     # era 6
ffn_hidden: int = 1024  # era 768
```

Si quieres un modelo más rápido (para pruebas):
```python
d_model: int = 256
n_layers: int = 4
ffn_hidden: int = 512
```

> **IMPORTANTE**: si cambias `MascotaConfig`, el checkpoint guardado ya no es compatible — hay que re-entrenar desde cero.

#### `TrainConfig` — hiperparámetros de entrenamiento

```python
@dataclass
class TrainConfig:
    batch_size: int = 16        # samples por paso de gradiente
    learning_rate: float = 3e-4 # tasa de aprendizaje inicial (Adam)
    min_lr: float = 3e-5        # tasa mínima al final del cosine decay
    weight_decay: float = 0.1   # regularización L2
    warmup_steps: int = 400     # pasos donde el LR sube gradualmente
    max_steps: int = 20000      # pasos totales de entrenamiento
    eval_interval: int = 200    # cada cuántos pasos evalúa en eval set
    save_interval: int = 500    # cada cuántos pasos guarda checkpoint
    grad_clip: float = 1.0      # clip de gradiente (estabilidad)
```

Los más útiles para tocar:
- `max_steps` — más pasos = mejor calidad, más tiempo
- `learning_rate` — si el modelo no converge, bajar a `1e-4`
- `batch_size` — bajar si hay out-of-memory en GPU

---

### 3.3 `inference.py` — Comportamiento en tiempo real

Este archivo controla cómo Mochi genera respuestas y cómo funciona el chat.

#### `MascotaInference` — el motor de inferencia

```python
class MascotaInference:
    def __init__(self, checkpoint_path, tokenizer_path, device="cpu"):
        # carga el modelo y el tokenizer
```

#### `chat_completion()` — genera una respuesta

```python
def chat_completion(self, messages, temperature=0.7, max_tokens=64, top_k=50):
    prompt = self._format_prompt(messages)  # convierte historial a texto del formato entrenado
    input_ids = self.tokenizer.encode(prompt).ids
    output_t, _ = self.model.generate(input_t, max_tokens, temperature, top_k)
    # recorta en <|im_end|> y devuelve el texto
```

Parámetros que controlan la calidad de respuesta:
| Parámetro | Valor actual | Efecto |
|---|---|---|
| `temperature` | 0.6 | Más bajo = más predecible, más alto = más creativo |
| `top_k` | 30 | Menos = más conservador, más = más variado |
| `max_tokens` | 64 | Longitud máxima de respuesta en tokens |

#### `_format_prompt()` — cómo se construye el input al modelo

```python
def _format_prompt(self, messages):
    parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content") or ""
        parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")
    parts.append("<|im_start|>assistant\n")   # ← el modelo genera a partir de aquí
    return "\n".join(parts)
```

#### `main()` — el loop del chat

```python
history = []    # guarda el historial de la conversación
context = history[-4:]   # solo pasa los últimos 4 mensajes (evita exceder seq_len)
result = engine.chat_completion(context, temperature=0.6, top_k=30, max_tokens=64)
```

Para cambiar cuánto contexto recuerda Mochi, cambiar `-4` por otro número (mayor = más memoria, más tokens usados).

---

### 3.4 `model.py` — Arquitectura del transformer

Este archivo define la red neuronal. **No necesitás tocarlo para cambiar el comportamiento** — los cambios de arquitectura van en `config.py`.

#### Estructura del transformer

```
Input tokens
     ↓
tok_emb + pos_emb     ← embedding: convierte token IDs a vectores
     ↓
Block × n_layers:
    LayerNorm
    Multi-Head Attention (causal mask)   ← "lee" todo el contexto previo
    LayerNorm
    FFN (up → ReLU → down)              ← "procesa" lo que leyó
     ↓
LayerNorm final
     ↓
lm_head (linear)      ← proyecta a vocab_size → probabilidades del próximo token
```

#### `generate()` — el loop de generación token a token

```python
@torch.no_grad()
def generate(self, idx, max_new_tokens=64, temperature=0.7, top_k=50):
    for _ in range(max_new_tokens):
        idx_cond = idx[:, -self.config.max_seq_len:]  # recorta si es muy largo
        logits, _ = self(idx_cond)
        logits = logits[:, -1, :] / temperature       # aplica temperatura
        # top-k filtering: descarta tokens poco probables
        v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
        logits[logits < v[:, [-1]]] = float("-inf")
        probs = F.softmax(logits, dim=-1)
        next_id = torch.multinomial(probs, num_samples=1)  # samplea
        idx = torch.cat([idx, next_id], dim=1)
        if next_id.item() == self.config.eos_id:   # para en <|im_end|>
            break
    return idx, []
```

---

### 3.5 `prepare_data.py` — Tokenizer

Entrena el tokenizador BPE sobre el dataset. Se llama automáticamente con `python -m mascotalm prepare`.

Lo único que se puede querer cambiar:
```python
VOCAB_SIZE = 4096   # vocabulario — más grande = mejor pero más params en tok_emb
```

El tokenizer se guarda en `data/tokenizer.json` y se reutiliza en inferencia.

---

## 4. Reglas de oro para no romper el modelo

1. **Después de cambiar `generate_data.py`** siempre hay que hacer `prepare` + `train`. Los cambios en el dataset solo tienen efecto después de re-entrenar.

2. **Después de cambiar `MascotaConfig`** hay que re-entrenar desde cero. El checkpoint viejo es incompatible.

3. **No mezclar tokens de usuario en respuestas de Mochi.** Las respuestas en las funciones `r_*()` no deben contener frases que normalmente dice el usuario (ej: `"¿jugamos?"`, `"hola"`, `"gracias"`).

4. **Las respuestas de Mochi deben ser cortas.** El modelo tiene `max_seq_len=256` tokens. Respuestas largas en el dataset empujan al modelo fuera de esa ventana.

5. **`inference.py` y `config.py` se pueden cambiar sin re-entrenar** (salvo que cambies la arquitectura del modelo).

---

## 5. Recetas rápidas

### Agregar una nueva respuesta a un tópico existente

Abrir `generate_data.py`, encontrar la función `r_*()` del tópico y agregar una línea al `pick([...])`:

```python
def r_saludo():
    return pick([
        # ... respuestas existentes ...
        "nueva respuesta que quiero que diga mochi.",   # ← agregar aquí
    ])
```

Luego: `python -m mascotalm prepare && python -m mascotalm train`

### Cambiar la temperatura sin re-entrenar

En `inference.py`, línea de `chat_completion` dentro de `main()`:
```python
result = engine.chat_completion(
    context,
    temperature=0.6,   # ← cambiar aquí (0.3–0.9)
    top_k=30,
    max_tokens=64,
)
```

Este cambio es inmediato, sin re-entrenar.

### Hacer que Mochi recuerde más contexto

En `inference.py`, cambiar cuántos mensajes pasan al modelo:
```python
context = history[-4:]   # ← cambiar -4 por -6, -8, etc.
```

Asegurarse que `max_seq_len` en `config.py` sea suficientemente grande.

### Entrenar más pasos si el modelo confunde categorías

En `config.py`:
```python
max_steps: int = 25000   # era 20000
```

Luego: `python -m mascotalm train`

### Ver qué tan bien está aprendiendo

El output de `train` muestra `Eval` cada 200 pasos. Una eval loss por debajo de `0.30` indica buen aprendizaje. Si se estanca, el modelo llegó a su límite para este tamaño/dataset.

### Probar Mochi sin chat interactivo

```bash
cd mascotaLLM
python test_mochi.py
```

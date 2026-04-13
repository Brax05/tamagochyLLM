<p align="center">
  <img src="assets/dog.png" alt="MascotaLM" width="400"/>
</p>

<h1 align="center">MascotaLM — Mochi</h1>
<p align="center"><em>Un LLM de ~9M parámetros que habla como una mascota virtual tipo Tamagotchi.</em></p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License"/>
  <br/>
  <a href="https://colab.research.google.com/github/Brax055/mascotaLLM/blob/main/train_mascotalm.ipynb"><img src="https://img.shields.io/badge/Entrenar_en-Colab-F9AB00?logo=googlecolab" alt="Train"/></a>&nbsp;
  <a href="https://colab.research.google.com/github/Brax055/mascotaLLM/blob/main/use_mascotalm.ipynb"><img src="https://img.shields.io/badge/Chatear_en-Colab-F9AB00?logo=googlecolab" alt="Chat"/></a>
</p>

---

> **Este proyecto existe para demostrar que entrenar tu propio modelo de lenguaje no es magia.**
> Sin doctorado. Sin cluster de GPUs. Un notebook de Colab, unos minutos, y tienes un LLM funcionando que construiste desde cero — generación de datos, tokenizer, arquitectura, loop de entrenamiento e inferencia. Si puedes correr un notebook, puedes entrenar un modelo de lenguaje.
>
> No va a producir un modelo de mil millones de parámetros que escriba ensayos. Pero te va a mostrar exactamente cómo funciona cada pieza — desde texto crudo hasta pesos entrenados hasta output generado.

---
Tú>     hola mochi
Mochi>  hola! estaba pensando en pizza y apareciste. qué bueno que estás aquí.
Tú>     ¿tienes hambre?
Mochi>  tengo MUCHA hambre. necesito chocolate ya.
Tú>     aquí tienes pastel
Mochi>  perfecta la comida. justo lo que necesitaba.
Tú>     ¿qué soñaste?
Mochi>  soñé contigo. y con tacos. las dos mejores cosas.
Tú>     cuéntame un chiste
Mochi>  ¿cómo se llama una mascota con hambre? yo.
Tú>     te quiero mochi
Mochi>  te quiero casi tanto como a los churros. casi.
Tú>     buenas noches
Mochi>  buenas noches. mañana quiero hot cakes de desayuno. avisado.

---

## ¿Qué es MascotaLM?

MascotaLM es un modelo de lenguaje pequeño que simula ser una mascota virtual llamada Mochi. Habla en frases cortas y minúsculas sobre comida, juegos, cariño y su mundo digital. No entiende conceptos humanos complejos como impuestos, el trabajo o las redes sociales — y no lo intenta.

Está entrenado desde cero en 60K conversaciones sintéticas en español latinoamericano neutro, con conversaciones de hasta 3 turnos para mantener coherencia de contexto.

---

## Arquitectura

| | |
|---|---|
| **Parámetros** | 8.8M |
| **Capas** | 6 |
| **Dimensión hidden** | 384 |
| **Cabezas de atención** | 6 |
| **FFN** | 768 (ReLU) |
| **Vocabulario** | 4,096 (BPE) |
| **Contexto máximo** | 256 tokens |
| **Normalización** | LayerNorm |
| **Posición** | Embeddings aprendidos |
| **LM head** | Weight-tied con embeddings |

Transformer vanilla. Sin GQA, sin RoPE, sin SwiGLU. Lo más simple posible.

---

## Personalidad de Mochi

- Habla en frases cortas y minúsculas
- Español latinoamericano neutro
- Muy motivada por la comida
- Dulce y un poco dramática
- Siente hambre, felicidad, aburrimiento y cariño
- No entiende conceptos humanos complejos
- Guarda contexto de los últimos 4 mensajes

**33 tópicos:** saludos, sentimiento, comida, hambre, jugar, aburrida, despedida, identidad, elogios, abrazos, tristeza, alegría, confusión con cosas humanas, noche, mañana, enferma, cansada, nivel/evolución, cariño, regreso tras ausencia, sueños, clima, curiosidad, aventura, regalos, cuidado, futuro, memoria, amigos, colores, música, tamaño, chistes.

---

## Inicio rápido

### Entrenar desde cero en Colab

[![Open in Colab](https://img.shields.io/badge/Entrenar_en-Colab-F9AB00?logo=googlecolab)](https://colab.research.google.com/github/Brax055/mascotaLLM/blob/main/train_mascotalm.ipynb)

1. Selecciona runtime **T4 GPU**
2. **Ejecuta todas las celdas** — genera dataset, entrena tokenizer, entrena modelo, lo prueba
3. Descarga el modelo localmente al terminar

### Ejecutar localmente

```bash
pip install -r requirements.txt
pip install -e .

python -m mascotalm prepare   # genera 60K samples + tokenizer (~1 min)
python -m mascotalm train     # entrena ~15000 pasos (~5 min GPU)
python -m mascotalm chat      # habla con Mochi
```

---

## Dataset

60,000 conversaciones sintéticas generadas localmente con `mascotalm/generate_data.py`.

| | |
|---|---|
| Samples | 60,000 (57K train / 3K test) |
| Formato | `{"text": "...", "category": "..."}` |
| Categorías | 33 |
| Estructura | 60% multi-turno (2-3 turnos), 40% single-turno |
| Generación | Composición de templates con componentes aleatorios |
| Unicidad | ~95% de samples únicos |

---

## Estructura del proyecto
mascotaLLM/
├── mascotalm/
│   ├── config.py          # Hiperparámetros (MascotaConfig, TrainConfig)
│   ├── model.py           # Transformer (MascotaLM)
│   ├── dataset.py         # Carga de datos y batching
│   ├── train.py           # Loop de entrenamiento
│   ├── inference.py       # Chat con Mochi (MascotaInference)
│   ├── generate_data.py   # Generador del dataset sintético
│   ├── prepare_data.py    # Genera datos + entrena tokenizer BPE
│   └── main.py        # Punto de entrada CLI
├── tools/
│   ├── export_dataset.py  # Sube dataset a HuggingFace
│   ├── export_model.py    # Exporta modelo a HuggingFace
│   └── export_onnx.py     # Exporta a ONNX cuantizado uint8
├── train_mascotalm.ipynb  # Notebook para entrenar en Colab
├── use_mascotalm.ipynb    # Notebook para chatear en Colab
├── requirements.txt
└── setup.py

---

## Decisiones de diseño

**¿Por qué multi-turno?** A diferencia del proyecto original que usaba single-turn, Mochi entrena con conversaciones de 2-3 turnos donde el tercer turno referencia lo anterior. Esto le da coherencia de contexto dentro de una conversación corta.

**¿Por qué contexto limitado a 4 mensajes?** Con `max_seq_len=256` y un modelo de 9M params, pasar más de 4 mensajes degrada la calidad. Mochi recuerda lo suficiente para ser coherente sin perder el hilo.

**¿Por qué transformer vanilla?** GQA, SwiGLU, RoPE añaden complejidad que no ayuda a 9M params. Atención estándar + ReLU FFN + LayerNorm produce la misma calidad con código más simple.

**¿Por qué datos sintéticos?** Una mascota con personalidad consistente necesita datos consistentes. La composición de templates con componentes aleatorios (30 comidas, 20 actividades, 11 partes del cuerpo) genera ~95% de outputs únicos.

**¿Por qué español latinoamericano neutro?** Para que Mochi sea accesible en toda Latinoamérica sin regionalismos que confundan al modelo.

---

## Archivos clave para modificar

- **Agregar tópicos o respuestas** → `mascotalm/generate_data.py`
- **Cambiar tamaño del modelo o pasos de entrenamiento** → `mascotalm/config.py`
- **Cambiar temperatura o contexto del chat** → `mascotalm/inference.py`
- **Cambiar cómo se tokeniza** → `mascotalm/prepare_data.py`

---

## Licencia

MIT

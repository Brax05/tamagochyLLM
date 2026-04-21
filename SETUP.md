### 1. Crear entorno virtual

**Windows**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / Mac**
```bash
python3 -m venv .venv
source .venv/bin/activate
```
---

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```
---

### 3. Ejecutar la aplicación

```bash
python app.py
```
---

## Notas

- El modelo ya está entrenado (checkpoints/best_model.pt)
- No es necesario ejecutar train ni prepare

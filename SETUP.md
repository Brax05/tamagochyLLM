### 1. Crear entorno virtual

Windows:
python -m venv .venv
.venv\Scripts\activate

Linux / Mac:
python3 -m venv .venv
source .venv/bin/activate

---

### 2. Instalar dependencias

pip install -r requirements.txt

---

### 3. Ejecutar la aplicación

python app.py

---

## Notas

- El modelo ya está entrenado (checkpoints/best_model.pt)
- No es necesario ejecutar train ni prepare
- Asegúrate de tener el entorno virtual activado

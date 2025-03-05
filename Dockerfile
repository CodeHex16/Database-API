FROM python:3.9-slim

WORKDIR /app

# Installa le dipendenze necessarie
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install "fastapi[all]" uvicorn

# Copia il codice dell'applicazione
COPY . .

# Esponi la porta su cui l'applicazione sarà in ascolto
EXPOSE 8000

# Variabili d'ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Avvia l'applicazione quando il container viene eseguito
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

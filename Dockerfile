FROM python:3.10.13-slim

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y     libglib2.0-0 libsm6 libxrender1 libxext6 tesseract-ocr     && apt-get clean

# Copier les fichiers
WORKDIR /app
COPY . .

# Installer les dépendances Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Lancer le bot
CMD ["python", "main.py"]
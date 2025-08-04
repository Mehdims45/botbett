FROM python:3.10.13-slim

# Installer les dépendances système nécessaires, y compris git et les certificats
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libsm6 libxrender1 libxext6 tesseract-ocr \
    ca-certificates git \
    && apt-get clean

# Mettre à jour les certificats
RUN update-ca-certificates

# Copier les fichiers
WORKDIR /app
COPY . .

# Installer les dépendances Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Lancer le bot
CMD ["python", "main.py"]

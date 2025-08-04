#!/usr/bin/env bash
# exit on error
set -o errexit

# Installer les paquets systeme
apt-get update
apt-get install -y tesseract-ocr tesseract-ocr-fra

# Installer les dépendances Python
pip install -r requirements.txt



import os
import time
import threading
import logging
import requests
import io
from flask import Flask
import snscrape.modules.twitter as sntwitter
from PIL import Image
import pytesseract
import telegram

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Charger les secrets depuis les variables d'environnement
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Vérifier que les variables d'environnement sont bien définies
if not TELEGRAM_TOKEN or not CHAT_ID:
    logging.error("Erreur : Les variables d'environnement TELEGRAM_TOKEN et CHAT_ID doivent être définies.")
    exit()

# Comptes Twitter à surveiller
TWITTER_ACCOUNTS = ["kapakpronostic", "exempleparieur", "parieurfootvip"]

# Initialiser le bot Telegram
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# Utiliser un set pour stocker les IDs des tweets déjà traités et éviter les doublons
processed_tweet_ids = set()

# --- Serveur Flask ---
# Crée un serveur web simple pour répondre aux contrôles de santé de Render
app = Flask(__name__)

@app.route('/')
def index():
    return "Le bot est actif et fonctionne."

# --- Fonctions du bot ---

def get_text_from_image(image_url):
    """Télécharge une image et en extrait le texte via OCR."""
    try:
        response = requests.get(image_url, timeout=15)
        response.raise_for_status()  # Lève une exception pour les codes d'erreur HTTP
        image = Image.open(io.BytesIO(response.content))
        # Langue française pour l'OCR, vous pouvez ajouter d'autres langues ex: 'fra+eng'
        text = pytesseract.image_to_string(image, lang='fra')
        return text.strip()
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur de téléchargement de l'image {image_url}: {e}")
    except Exception as e:
        logging.error(f"Erreur OCR pour l'image {image_url}: {e}")
    return ""

def scrape_and_send_tweets():
    """Scrape les derniers tweets, les analyse et les envoie sur Telegram."""
    logging.info("Démarrage du cycle de scraping...")
    for account in TWITTER_ACCOUNTS:
        logging.info(f"Scraping du compte : {account}")
        try:
            # On ne prend que les 5 derniers tweets pour ne pas surcharger l'API
            scraper = sntwitter.TwitterUserScraper(account)
            for i, tweet in enumerate(scraper.get_items()):
                if i >= 5:
                    break

                if tweet.id in processed_tweet_ids:
                    continue # On ignore les tweets déjà traités

                logging.info(f"Nouveau tweet trouvé : {tweet.url}")

                # 1. Extraire le texte du tweet
                tweet_text = tweet.rawContent

                # 2. Extraire le texte des images (OCR)
                ocr_results = []
                if tweet.media:
                    for media_item in tweet.media:
                        if isinstance(media_item, sntwitter.Photo):
                            logging.info(f"Analyse de l'image : {media_item.fullUrl}")
                            ocr_text = get_text_from_image(media_item.fullUrl)
                            if ocr_text:
                                ocr_results.append(ocr_text)

                # 3. Construire et envoyer le message
                message = f"🐦 **Nouveau Tweet de {account}** 🐦\n\n"
                message += f"**Contenu :**\n{tweet_text}\n\n"

                if ocr_results:
                    message += "**Texte détecté dans l'image (OCR) :**\n"
                    message += "---\n"
                    message += "\n\n---\n".join(ocr_results)
                    message += "\n\n"

                message += f"🔗 **Lien vers le tweet :** {tweet.url}"

                try:
                    bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=telegram.ParseMode.MARKDOWN)
                    processed_tweet_ids.add(tweet.id) # Marquer comme traité
                    logging.info(f"Tweet {tweet.id} envoyé avec succès sur Telegram.")
                except telegram.error.TelegramError as e:
                    logging.error(f"Erreur lors de l'envoi sur Telegram : {e}")

                time.sleep(1) # Petite pause pour ne pas spammer

        except Exception as e:
            logging.error(f"Erreur lors du scraping de {account}: {e}")
        
        time.sleep(5) # Pause entre chaque compte

    logging.info("Cycle de scraping terminé.")


def run_scraper_periodically():
    """Lance le scraping toutes les 60 secondes."""
    while True:
        scrape_and_send_tweets()
        time.sleep(60)

# --- Démarrage ---
if __name__ == "__main__":
    # Lancer le scraper dans un thread séparé pour ne pas bloquer le serveur web
    scraper_thread = threading.Thread(target=run_scraper_periodically, daemon=True)
    scraper_thread.start()

    # Démarrer le serveur Flask
    # Render fournit la variable PORT, on utilise 8080 par défaut si elle n'existe pas
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)


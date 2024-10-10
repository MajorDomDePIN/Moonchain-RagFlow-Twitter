# twitter_poster.py

import os
import json
import tweepy
import time
from datetime import datetime
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Twitter API-Schlüssel und Zugangsdaten (ersetzen Sie diese durch Ihre eigenen)
api_key = os.getenv("TWITTER_API_KEY")
api_key_secret = os.getenv("TWITTER_API_SECRET")
access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# Funktion zum Lesen der Antwort aus einer JSON-Datei
def read_response_from_json(file_path):
    """Liest die Antwort aus einer JSON-Datei."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Die Datei {file_path} wurde nicht gefunden.")

    with open(file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        response = data.get("answer", "")

    return response.strip()

# Angepasste Funktion zum Aufteilen der Nachricht in Tweets
def split_into_tweets(message, max_length=280):
    """Teilt die Nachricht in Tweets auf, die als Thread gepostet werden sollen."""
    post_list = []
    post_content = ''
    
    # Aufteilen der Nachricht in Zeilen
    msg_lines = message.splitlines()

    for line in msg_lines:
        line = line.strip()
        if line == '---':
            continue
        
        # Wenn die Zeile selbst zu lang ist, teile sie in Wörter
        if len(line) > max_length:
            words = line.split(' ')
            for word in words:
                # Überprüfe, ob das aktuelle Wort hinzugefügt werden kann
                if len(post_content) + len(word) + 1 > max_length:  # +1 für das Leerzeichen
                    if post_content:  # Wenn post_content nicht leer ist
                        post_list.append(post_content.strip())  # Speichere den aktuellen Tweet
                    post_content = word  # Starte einen neuen Tweet mit dem aktuellen Wort
                else:
                    post_content += ' ' + word if post_content else word  # Füge das Wort hinzu
            continue  # gehe zur nächsten Zeile

        # Überprüfe, ob die neue Zeile hinzugefügt werden kann
        if len(post_content) + len(line) > max_length:
            post_list.append(post_content.strip())  # Speichere den aktuellen Tweet
            post_content = line  # Starte einen neuen Tweet mit der aktuellen Zeile
        else:
            post_content += '\n' + line if post_content else line  # Füge die Zeile hinzu

    # Füge den letzten Tweet hinzu, wenn vorhanden
    if post_content:
        post_list.append(post_content.strip())

    return post_list

# Funktion zum Senden von Tweets
def send_to_twitter(api, messages):
    try:
        if len(messages) == 1:
            # Ein einzelner Tweet, wenn die Nachricht kürzer als 280 Zeichen ist
            tweet = api.create_tweet(text=messages[0])
            print(f"Erster Tweet erfolgreich gepostet. Tweet ID: {tweet.data['id']}")

        else:
            # Ein Tweet-Thread
            print(f"Teile die Nachricht in {len(messages)} Tweets für den Thread auf.")
            previous_tweet_id = None

            for index, message in enumerate(messages):
                if previous_tweet_id is None:
                    # Der erste Tweet im Thread
                    tweet = api.create_tweet(text=message)
                    print(f"Tweet erfolgreich gepostet. Tweet ID: {tweet.data['id']}")
                    previous_tweet_id = tweet.data['id']  # ID für den nächsten Tweet speichern
                else:
                    # Nachfolgende Tweets im Thread
                    tweet = api.create_tweet(text=message, in_reply_to_tweet_id=previous_tweet_id)
                    print(f"Tweet erfolgreich gepostet. Tweet ID: {tweet.data['id']}")
                    previous_tweet_id = tweet.data['id']  # ID für den nächsten Tweet speichern

                # Vermeidung der Ratenbeschränkungen
                time.sleep(10)

    except Exception as e:
        print(f"Fehler beim Posten des Tweets: {e}")

# Funktion, die die gesamte Logik ausführt
def post_report_to_twitter(json_file_path):
    print("API Key:", api_key)
    print("API Key Secret:", api_key_secret)
    print("Access Token:", access_token)
    print("Access Token Secret:", access_token_secret)

    try:
        # Die Antwort aus der JSON-Datei lesen
        response = read_response_from_json(json_file_path)

        # Die Antwort in Tweets aufteilen
        tweet_list = split_into_tweets(response)

        # Twitter-Client initialisieren
        api = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_key_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )

        # Tweets senden
        send_to_twitter(api, tweet_list)

    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")

        
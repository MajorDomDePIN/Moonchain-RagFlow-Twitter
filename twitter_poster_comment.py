# Importiere die notwendigen Bibliotheken
import os  # Zum Arbeiten mit dem Dateisystem und Umgebungsvariablen
import json  # Zum Arbeiten mit JSON-Daten
import tweepy  # Twitter-API-Bibliothek
import time  # Für Zeitverzögerungen
from datetime import datetime  # Um mit Datum und Zeit zu arbeiten
from dotenv import load_dotenv  # Um Umgebungsvariablen aus einer .env-Datei zu laden

# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv()

# Twitter API-Schlüssel und Zugangsdaten werden aus der .env-Datei geladen
api_key = os.getenv("TWITTER_API_KEY")  # Twitter API Key
api_key_secret = os.getenv("TWITTER_API_SECRET")  # Twitter API Secret Key
access_token = os.getenv("TWITTER_ACCESS_TOKEN")  # Twitter Access Token
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")  # Twitter Access Token Secret

# Funktion zum Lesen der Antwort aus einer JSON-Datei
def read_response_from_json(file_path):
    """Liest die Antwort aus einer JSON-Datei."""
    # Prüfen, ob die Datei existiert, andernfalls Fehler ausgeben
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Die Datei {file_path} wurde nicht gefunden.")

    # Öffne die Datei und lese den Inhalt
    with open(file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        # Extrahiere die Antwort (falls vorhanden)
        response = data.get("answer", "")

    return response.strip()  # Rückgabe der Antwort ohne überflüssige Leerzeichen

# Funktion zum Aufteilen der Nachricht in Tweets, die als Thread gepostet werden sollen
def split_into_tweets(message, max_length=280):
    """Teilt die Nachricht in Tweets auf, die als Thread gepostet werden sollen."""
    post_list = []  # Liste für Tweets
    post_content = ''  # Variable für den aktuellen Tweet-Inhalt
    
    # Nachricht in Zeilen aufteilen
    msg_lines = message.splitlines()

    for line in msg_lines:
        line = line.strip()  # Entfernt führende und nachfolgende Leerzeichen
        if line == '---':  # Überspringt Linien, die nur '---' enthalten
            continue
        
        # Wenn eine einzelne Zeile länger als ein Tweet ist, wird sie in Wörter zerlegt
        if len(line) > max_length:
            words = line.split(' ')  # Zerlege die Zeile in Wörter
            for word in words:
                # Überprüfe, ob das aktuelle Wort zum Tweet hinzugefügt werden kann
                if len(post_content) + len(word) + 1 > max_length:  # +1 für das Leerzeichen
                    if post_content:  # Wenn post_content nicht leer ist
                        post_list.append(post_content.strip())  # Speichere den aktuellen Tweet
                    post_content = word  # Starte einen neuen Tweet mit dem aktuellen Wort
                else:
                    # Füge das Wort zum aktuellen Tweet hinzu
                    post_content += ' ' + word if post_content else word  
            continue  # Fahre mit der nächsten Zeile fort

        # Überprüfe, ob die aktuelle Zeile zum Tweet hinzugefügt werden kann
        if len(post_content) + len(line) > max_length:
            post_list.append(post_content.strip())  # Speichere den aktuellen Tweet
            post_content = line  # Starte einen neuen Tweet mit der aktuellen Zeile
        else:
            # Füge die Zeile zum aktuellen Tweet hinzu
            post_content += '\n' + line if post_content else line  

    # Speichere den letzten Tweet, wenn noch Inhalt übrig ist
    if post_content:
        post_list.append(post_content.strip())

    return post_list  # Rückgabe der Liste mit Tweets

# Funktion zum Senden von Tweets an Twitter
def send_to_twitter(api, messages):
    try:
        if len(messages) == 1:
            # Wenn die Nachricht kürzer als 280 Zeichen ist, wird sie als einzelner Tweet gepostet
            tweet = api.create_tweet(text=messages[0])
            print(f"Erster Tweet erfolgreich gepostet. Tweet ID: {tweet.data['id']}")

        else:
            # Wenn die Nachricht länger ist, wird sie in mehreren Tweets als Thread gepostet
            print(f"Teile die Nachricht in {len(messages)} Tweets für den Thread auf.")
            previous_tweet_id = None  # Speichert die ID des letzten Tweets im Thread

            for index, message in enumerate(messages):
                if previous_tweet_id is None:
                    # Poste den ersten Tweet im Thread
                    tweet = api.create_tweet(text=message)
                    print(f"Tweet erfolgreich gepostet. Tweet ID: {tweet.data['id']}")
                    previous_tweet_id = tweet.data['id']  # Speichere die Tweet-ID
                else:
                    # Poste nachfolgende Tweets im Thread, indem sie mit dem vorherigen Tweet verknüpft werden
                    tweet = api.create_tweet(text=message, in_reply_to_tweet_id=previous_tweet_id)
                    print(f"Tweet erfolgreich gepostet. Tweet ID: {tweet.data['id']}")
                    previous_tweet_id = tweet.data['id']  # Aktualisiere die Tweet-ID

                # Warte 10 Sekunden, um Ratenbegrenzungen zu vermeiden
                time.sleep(10)

    except Exception as e:
        # Fehler beim Posten eines Tweets abfangen und ausgeben
        print(f"Fehler beim Posten des Tweets: {e}")

# Hauptfunktion, die die gesamte Logik ausführt
def post_report_to_twitter(json_file_path):
    try:
        # Lese die Antwort aus der JSON-Datei
        response = read_response_from_json(json_file_path)

        # Teile die Antwort in Tweets auf
        tweet_list = split_into_tweets(response)

        # Twitter-API-Client initialisieren
        api = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_key_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )

        # Sende die Tweets an Twitter
        send_to_twitter(api, tweet_list)

    except FileNotFoundError as e:
        # Datei nicht gefunden
        print(e)
    except Exception as e:
        # Allgemeiner Fehler
        print(f"Ein Fehler ist aufgetreten: {e}")

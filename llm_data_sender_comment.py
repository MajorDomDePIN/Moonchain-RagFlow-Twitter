# Importiere notwendige Bibliotheken für HTTP-Anfragen, Dateihandhabung und JSON-Verarbeitung
import requests
import os
import json
import csv
from datetime import datetime  # Für die Handhabung von Datums- und Zeitangaben
import strip_markdown  # Zum Entfernen von Markdown-Formatierungen aus Text
from dotenv import load_dotenv  # Um Umgebungsvariablen aus einer .env-Datei zu laden

# Lade die Umgebungsvariablen aus der .env-Datei
load_dotenv()

# Setze die API-URL und den Benutzer-ID für die Kommunikation mit RagFlow
gRagApiUrl = "http://demo.ragflow.io/v1/api/"
gRagUserId = "PythonClientUser"  # Benutzer-ID für RagFlow
# Lade den API-Schlüssel aus den Umgebungsvariablen
gRagApiToken = os.getenv("RAGFLOW_API_KEY")

# Funktion zum Kombinieren aller CSV-Dateien in einem Ordner zu einer einzigen Datei
def combine_csv_files(input_directory="output", output_file="combined_report.csv"):
    combined_data = []  # Liste zum Speichern aller CSV-Daten

    # Header (Spaltennamen) wird aus der ersten Datei genommen
    header = None

    # Iteriere über alle Dateien im angegebenen Verzeichnis
    for filename in os.listdir(input_directory):
        if filename.endswith(".csv"):  # Verarbeite nur CSV-Dateien
            file_path = os.path.join(input_directory, filename)
            with open(file_path, 'r') as csvfile:
                csv_reader = csv.reader(csvfile, delimiter='\t')
                if header is None:  # Wenn der Header noch nicht festgelegt wurde
                    header = next(csv_reader)  # Nimm die erste Zeile als Header
                    combined_data.append(header)  # Füge den Header zu den kombinierten Daten hinzu
                else:
                    next(csv_reader)  # Überspringe den Header in den anderen Dateien

                # Füge alle Zeilen aus der Datei den kombinierten Daten hinzu
                for row in csv_reader:
                    combined_data.append(row)

    # Speichere die kombinierten Daten in einer neuen CSV-Datei
    output_path = os.path.join(input_directory, output_file)
    with open(output_path, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter='\t')
        csv_writer.writerows(combined_data)  # Schreibe alle kombinierten Daten in die neue Datei

    # Ausgabe, um zu bestätigen, dass die Datei erstellt wurde
    print(f"Kombinierte CSV-Dateien gespeichert in {output_path}")
    return output_path  # Rückgabe des Dateipfads der kombinierten Datei

# Funktion zum Senden der kombinierten CSV-Daten an RagFlow
def send_to_ragflow(csv_directory="output"):
    # Kombiniere die CSV-Dateien in einer Datei
    combined_file = combine_csv_files(csv_directory)

    # Sende die erstellte CSV-Datei an RagFlow
    send_file(combined_file)

# Funktion zum Senden einer Datei und einer Anfrage an RagFlow
def send_file(file_path):
    # Erstelle eine Frage für RagFlow, die auf dem aktuellen Datum basiert
    today = datetime.today().strftime("%Y-%b-%d")  # Holen des aktuellen Datums
    # Beispiel einer Frage an RagFlow, basierend auf einer bestimmten Datengrundlage
    question = (
    f"You are a journalist, and today is {today}. Using the Moonchain data, please write an English daily report on Moonchain. "
    "The report should be written in a positive tone. Limit the report to a maximum of 800 words.\n"
    )

    # Lese die CSV-Datei und erstelle eine Übersicht der Daten
    all_info = ""

    # Öffne die CSV-Datei und lese jede Zeile
    with open(file_path, 'r') as csvfile:
        csv_reader = csv.DictReader(csvfile, delimiter='\t')
        for row in csv_reader:
            # Erstelle für jede Zeile eine Formatierung für die Ausgabe
            line = f"On {row['date']}, the item '{row['item']}' has the value of {row['value']}."
            all_info += line + " "

    # Debug-Ausgabe der Frage, um sicherzustellen, dass sie korrekt ist
    print(f"Question: {question}")

    # URL zum Erstellen einer neuen RagFlow-Konversation
    url_new = f"{gRagApiUrl}/new_conversation?user_id={gRagUserId}"
    # Setze den Authorization-Header mit dem API-Token
    headers = {"Authorization": f"Bearer {gRagApiToken}"}

    try:
        # Sende eine GET-Anfrage an RagFlow, um eine neue Konversation zu starten
        response = requests.get(url_new, headers=headers)
        response.raise_for_status()  # Falls die Anfrage fehlschlägt, wird eine Ausnahme ausgelöst

        # Extrahiere die Antwortdaten
        response_data = response.json()
        if "data" in response_data and isinstance(response_data["data"], dict) and "id" in response_data["data"]:
            # Extrahiere die Konversations-ID
            conversation_id = response_data["data"]["id"]
            url_completion = f"{gRagApiUrl}/completion"

            # Die Nachricht, die an RagFlow gesendet werden soll
            post_data = {
                "conversation_id": conversation_id,
                "messages": [{"role": "user", "content": question}],  # Die Frage wird gesendet
                "quote": False,
                "stream": False  # Streaming deaktivieren
            }

            # Sende eine POST-Anfrage an RagFlow mit den gesammelten Daten
            response = requests.post(url_completion, headers=headers, json=post_data)

            # Debug-Ausgabe der Antwort (Rohdaten)
            print(f"Response von der Nachricht (POST) für {file_path}: {response.text}")

            response.raise_for_status()  # Überprüfe, ob die Anfrage erfolgreich war

            # Verarbeite die Antwort, falls sie gültig ist
            response_data = response.json()
            if "retcode" in response_data and response_data["retcode"] == 0 and "data" in response_data:
                # Extrahiere die Antwort als Markdown und entferne das Markdown
                answer_md = response_data["data"].get("answer", "")
                print("Antwort von Ragflow als Markdown:", answer_md)
                answer = strip_markdown.strip_markdown(answer_md)
                print("Antwort von Ragflow:", answer)
                
                # Speichere die Antwort in einer JSON-Datei
                output_file = "output/combined_report.json"
                with open(output_file, 'w') as outfile:
                    json.dump({"answer": answer}, outfile, indent=4)
                print(f"Response gespeichert in {output_file}")

            else:
                print(f"Failed to get a valid response for {file_path}")

        else:
            print(f"Failed to create a new conversation for {file_path}")
    except requests.RequestException as e:
        # Fehlerbehandlung bei HTTP-Anfragen
        print(f"Error sending file {file_path}: {e}")

# Hauptprogrammstart, wenn das Skript direkt ausgeführt wird
if __name__ == "__main__":
    send_to_ragflow()  # Starte den Prozess, um CSV-Dateien zu kombinieren und an RagFlow zu senden

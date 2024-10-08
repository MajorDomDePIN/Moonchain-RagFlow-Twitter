# llm_data_sender.py

import requests
import os
import json
import csv
from datetime import datetime
import strip_markdown
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv()


gRagApiUrl = "http://demo.ragflow.io/v1/api/"
gRagUserId = "PythonClientUser"
gRagApiToken = os.getenv("RAGFLOW_API_KEY")

def combine_csv_files(input_directory="output", output_file="combined_report.csv"):
    combined_data = []

    # Header wird aus der ersten Datei genommen
    header = None

    for filename in os.listdir(input_directory):
        if filename.endswith(".csv"):
            file_path = os.path.join(input_directory, filename)
            with open(file_path, 'r') as csvfile:
                csv_reader = csv.reader(csvfile, delimiter='\t')
                if header is None:
                    header = next(csv_reader)  # Nimm die Header-Zeile
                    combined_data.append(header)
                else:
                    next(csv_reader)  # Überspringe die Header-Zeile

                for row in csv_reader:
                    combined_data.append(row)

    # Schreibe die kombinierten Daten in eine neue Datei
    output_path = os.path.join(input_directory, output_file)
    with open(output_path, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter='\t')
        csv_writer.writerows(combined_data)

    print(f"Kombinierte CSV-Dateien gespeichert in {output_path}")
    return output_path

def send_to_ragflow(csv_directory="output"):
    # Kombinierte CSV-Datei erstellen
    combined_file = combine_csv_files(csv_directory)

    # Sende die wöchentliche CSV-Datei an Ragflow
    send_file(combined_file)

def send_file(file_path):
    # Erstelle die Frage basierend auf allen Daten in der CSV-Datei
    today = datetime.today().strftime("%Y-%b-%d")
    #question = (f"You are a journalist, and today is {today}. Using the Moonchain data, "
    #            f"please write an English daily report on Moonchain. The report should be written in a positive tone. Only report on the variables that you can find in the information between 'data info start' and 'data info end'. The report should not exceed 1000 signs.\n")


    question = (
    "You are a journalist, and today is 2024-Oct-07. Using the Moonchain data, please write an English daily report on Moonchain. "
    "The report should be written in a positive tone.\n"
    "06-October-2024 Moonchain Data info begin.\n"
    "'Active accounts' has the value of 421.\n"
    "'Average transaction fee' has the value of 2.247460462557913 MXC.\n"
    "'Number of new transactions' has the value of 2930 Txn.\n"
    "'Number of new blocks' has the value of 1362.\n"
    "'Average size of blocks' has the value of 1441 bytes.\n"
    "'Average amount of reward' has the value of 0.08810875097847262 MXC.\n"
    "'Average gas price' has the value of 14229.104286258942 Gwei.\n"
    "'Number of new contracts' has the value of 7.\n"
    "06-October-2024 Data info end.\n\n"
    "05-October-2024 Moonchain Data info begin.\n"
    "'Active accounts' has the value of 439.\n"
    "'Average transaction fee' has the value of 2.7251766384381777 MXC.\n"
    "'Number of new transactions' has the value of 2463 Txn.\n"
    "'Number of new blocks' has the value of 1157.\n"
    "'Average size of blocks' has the value of 1339 bytes.\n"
    "'Average amount of reward' has the value of 0.0702911272750491 MXC.\n"
    "'Average gas price' has the value of 21741.112736579213 Gwei.\n"
    "'Number of new contracts' has the value of 11.\n"
    "06-October-2024 Data info end."
    )
    # Lese den Inhalt der CSV-Datei, um die Daten für die Frage zu sammeln
    all_info = ""

    with open(file_path, 'r') as csvfile:
        csv_reader = csv.DictReader(csvfile, delimiter='\t')
        for row in csv_reader:
            line = f"On {row['date']}, the item '{row['item']}' has the value of {row['value']}."
            all_info += line + " "

    # Füge die gesammelten Informationen zur Frage hinzu
    #question += f"Data info begin. {all_info.strip()} Data info end.\n"

    # Debug: Frage anzeigen
    print(f"Question: {question}")

    # Senden der Frage an Ragflow
    url_new = f"{gRagApiUrl}/new_conversation?user_id={gRagUserId}"
    headers = {"Authorization": f"Bearer {gRagApiToken}"}

    try:
        # Erstellt eine neue Konversation
        response = requests.get(url_new, headers=headers)
        response.raise_for_status()

        # Prüfen, ob die Antwort gültig ist
        response_data = response.json()
        if "data" in response_data and isinstance(response_data["data"], dict) and "id" in response_data["data"]:
            conversation_id = response_data["data"]["id"]
            url_completion = f"{gRagApiUrl}/completion"

            # Die Nachricht, die an Ragflow gesendet werden soll
            post_data = {
                "conversation_id": conversation_id,
                "messages": [{"role": "user", "content": question}],
                "quote": False,
                "stream": False  # Das Deaktivieren des Streamings
            }

            # Sende die Nachricht an Ragflow
            response = requests.post(url_completion, headers=headers, json=post_data)

            # Debug: Ausgabe der Antwort (Rohformat)
            print(f"Response von der Nachricht (POST) für {file_path}: {response.text}")

            response.raise_for_status()

            # Die Antwort aus dem JSON-Format lesen
            response_data = response.json()
            if "retcode" in response_data and response_data["retcode"] == 0 and "data" in response_data:
                answer_md = response_data["data"].get("answer", "")
                print("Antwort von Ragflow als Markdown:", answer_md)
                answer = strip_markdown.strip_markdown(answer_md)
                print("Antwort von Ragflow:", answer)
                # Speichern des Response in einer Datei
                output_file = "output/combined_report.json"
                with open(output_file, 'w') as outfile:
                    json.dump({"answer": answer}, outfile, indent=4)
                print(f"Response gespeichert in {output_file}")

            else:
                print(f"Failed to get a valid response for {file_path}")

        else:
            print(f"Failed to create a new conversation for {file_path}")
    except requests.RequestException as e:
        print(f"Error sending file {file_path}: {e}")

if __name__ == "__main__":
    send_to_ragflow()

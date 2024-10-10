# Importiere die notwendigen Bibliotheken
import os  # Für Dateisystemoperationen (z.B. Verzeichnisse erstellen)
import requests  # Für HTTP-Anfragen (z.B. um Daten von einer API abzurufen)
import csv  # Zum Erstellen und Verarbeiten von CSV-Dateien
import json  # Zum Verarbeiten von JSON-Daten (z.B. API-Antworten)
from datetime import datetime, timedelta  # Zum Arbeiten mit Datum und Zeit

# Globale Variable für Debugging und die Basis-URL für die API
gVerbose = True  # Diese Variable wird genutzt, um festzulegen, ob ausführliche Logmeldungen ausgegeben werden sollen.
gStatBaseUrl = "https://stats.moonchain.com/api/v1"  # Basis-URL für die Moonchain-API

# Funktion zum Ausgeben von Lognachrichten
def logPrint(aMsg):
    print(F"{aMsg}", flush=True)  # Druckt die Nachricht und erzwingt das sofortige Schreiben des Outputs in die Konsole.

# Funktion zum Sammeln von Daten
def collect_data(target_dir="output"):
    # Erstelle das Zielverzeichnis, falls es noch nicht existiert
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)  # Erstellt ein Verzeichnis mit dem Namen "output", wenn es nicht existiert.

    # Schleife über die letzten zwei Tage, um Daten zu sammeln
    for i in range(1, 3):
        target_date = datetime.today() - timedelta(days=i)  # Bestimmt das Datum von gestern und vorgestern.
        generate_daily_report(target_dir, target_date)  # Ruft die Funktion auf, um den täglichen Bericht zu erstellen.

# Funktion zur Erstellung des täglichen Berichts
def generate_daily_report(target_dir, target_date):
    # Konvertiere das Datum in ein kurzes String-Format (YYYY-MM-DD)
    date_string_short = target_date.strftime("%Y-%m-%d")
    logPrint(f"Generate Daily Report for {date_string_short}")  # Loggt, dass ein Bericht für das Datum erstellt wird.

    # Erstelle den Dateinamen für den Bericht
    output_filename = os.path.join(target_dir, f"MoonchainDailyReport_{date_string_short}.csv")
    
    # Lösche die Datei, falls sie bereits existiert
    if os.path.exists(output_filename):
        os.remove(output_filename)
    
    logPrint(f"Output file: {output_filename}")  # Loggt den Namen der Ausgabedatei.

    # Öffne die CSV-Datei zum Schreiben
    with open(output_filename, 'w', newline='') as csvfile:
        outfile = csv.writer(csvfile, delimiter='\t')  # Initialisiert den CSV-Schreiber mit Tabulator als Trennzeichen.
        outfile.writerow(['type', 'date', 'item', 'value'])  # Schreibt die Kopfzeilen in die CSV-Datei.

        # Rufe verschiedene Daten von der API ab und schreibe sie in die CSV-Datei
        get_lines_data(outfile, target_date, "activeAccounts", "Active accounts", "")
        get_lines_data(outfile, target_date, "newAccounts", "Number of new accounts", "")
        get_lines_data(outfile, target_date, "averageTxnFee", "Average transaction fee", "MXC")
        get_lines_data(outfile, target_date, "newTxns", "Number of new transactions", "")
        get_lines_data(outfile, target_date, "newBlocks", "Number of new blocks", "")
        get_lines_data(outfile, target_date, "averageBlockSize", "Average size of blocks", "bytes")
        get_lines_data(outfile, target_date, "averageBlockRewards", "Average amount of reward", "MXC")
        get_lines_data(outfile, target_date, "gasUsedGrowth", "Cumulative gas used", "")
        get_lines_data(outfile, target_date, "averageGasPrice", "Average gas price", "Gwei")
        get_lines_data(outfile, target_date, "newContracts", "Number of new contracts", "")

# Hilfsfunktion, um zu überprüfen, ob ein Objekt eine Liste oder ein Array ist
def isArray(aObject):
    # Überprüft, ob das Objekt eine "length"-Eigenschaft hat, um festzustellen, ob es sich um ein Array handelt
    if not hasattr(aObject, "__len__"):
        return False

    return True

# Funktion zum Abrufen und Verarbeiten der Daten von der API
def get_lines_data(outfile, target_date, aId, aTitle, aUnit):
    # Formatiere das Datum für die API-Anfrage
    target_date_str = target_date.strftime("%Y-%m-%d")
    
    # Erstelle die URL für die API-Anfrage, um die spezifischen Daten abzurufen
    url = f"{gStatBaseUrl}/lines/{aId}?from={target_date_str}&to={target_date_str}"
    logPrint(f"GET {url}")  # Loggt die URL der API-Anfrage.

    # Sende eine GET-Anfrage an die API und warte maximal 10 Sekunden
    response = requests.get(url, timeout=10)
    
    # Überprüfe, ob die Antwort erfolgreich war
    if response.status_code == 200:
        j_resp = json.loads(response.content)  # Lade die Antwort als JSON-Objekt.
        logPrint(f"    Resp: {json.dumps(j_resp)}")  # Loggt die JSON-Antwort.

        # Überprüfe, ob das JSON die erwartete Struktur enthält
        if not "chart" in j_resp:
            raise Exception(f"Invalid responses from {url}, missing 'chart'.")
        if not isArray(j_resp["chart"]):
            raise Exception(f"Invalid responses from {url}, 'chart' is not an array.")
        if len(j_resp["chart"]) == 0:
            logPrint("    WARNING. No data, skipped.")
        else:
            # Iteriere über die erhaltenen Daten und schreibe sie in die CSV-Datei
            for chart_data in j_resp["chart"]:
                if not "date" in chart_data:
                    raise Exception(f"Invalid responses from {url}, missing 'date'.")
                if not "value" in chart_data:
                    raise Exception(f"Invalid responses from {url}, missing 'value'.")

                # Konvertiere das Datum in ein lesbares Format und schreibe die Daten in die CSV-Datei
                str_date = datetime.strptime(chart_data["date"], "%Y-%m-%d").strftime("%d-%B-%Y")
                str_value = chart_data["value"]
                str_value = f"{str_value} {aUnit}".strip()  # Hänge die Einheit an, falls vorhanden.
                
                # Schreibe die Zeile in die CSV-Datei
                outfile.writerow(["Moonchain Daily Report", str_date, aTitle, str_value])



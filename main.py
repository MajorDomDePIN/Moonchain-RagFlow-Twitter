# main.py

import data_collector_comments
import llm_data_sender_comment
import twitter_poster_comment
def main():
    # Schritt 1: Daten sammeln
    print("Schritt 1: Sammle Daten...")
    data_collector_comments.collect_data()  # Diese Funktion sammelt die Daten.

    # Schritt 2: Sende die CSV-Dateien an Ragflow
    print("Schritt 2: Sende CSV-Dateien an Ragflow...")
    llm_data_sender_comment.send_to_ragflow()  # Diese Funktion sendet die CSV-Dateien.

    # Schritt 3: Twitter-Publishing
    print("Schritt 3: Posten auf Twitter...")
    json_file_path = "output/combined_report.json"
    twitter_poster_comment.post_report_to_twitter(json_file_path)  # Diese Funktion veröffentlicht die Tweets.

if __name__ == "__main__":
    main()

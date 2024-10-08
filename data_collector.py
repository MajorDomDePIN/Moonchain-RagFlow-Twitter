# data_collector.py

import os
import requests
import csv
import json
from datetime import datetime, timedelta

gVerbose = True
gStatBaseUrl = "https://stats.moonchain.com/api/v1"

def logPrint(aMsg):
    print(F"{aMsg}", flush=True)

def collect_data(target_dir="output"):
    # erzeuge das Zielverzeichnis falls es nicht existiert
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)

    for i in range(1,3):
        target_date = datetime.today() - timedelta(days=i)
        generate_daily_report(target_dir, target_date)

def generate_daily_report(target_dir, target_date):
    date_string_short = target_date.strftime("%Y-%m-%d")
    logPrint(f"Generate Daily Report for {date_string_short}")

    output_filename = os.path.join(target_dir, f"MoonchainDailyReport_{date_string_short}.csv")
    if os.path.exists(output_filename):
        os.remove(output_filename)
    
    logPrint(f"Output file: {output_filename}")

    with open(output_filename, 'w', newline='') as csvfile:
        outfile = csv.writer(csvfile, delimiter='\t')
        outfile.writerow(['type', 'date', 'item', 'value'])

        # Daten abrufen und in die Datei schreiben
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

def isArray(aObject):
    # type: (any) -> bool
    if not hasattr(aObject, "__len__"):
        return False

    return True

def get_lines_data(outfile, target_date, aId, aTitle, aUnit):
    target_date_str = target_date.strftime("%Y-%m-%d")
    url = f"{gStatBaseUrl}/lines/{aId}?from={target_date_str}&to={target_date_str}"
    logPrint(f"GET {url}")

    response = requests.get(url, timeout= 10)
    if response.status_code == 200:
        j_resp = json.loads(response.content)
        logPrint(f"    Resp: {json.dumps(j_resp)}")
        if not "chart" in j_resp:
            raise Exception(f"Invalid responses from {url}, missing 'chart'.")
        if not isArray(j_resp["chart"]):
            raise Exception(
                f"Invalid responses from {url}, 'chart' is not a array.")
        if len(j_resp["chart"]) == 0:
            logPrint("    WARNING. No data, skipped.")
        else:
            # aOutFile.write(f"  {aTitle}:\n")
            for chart_data in j_resp["chart"]:
                if not "date" in chart_data:
                    raise Exception(
                        f"Invalid responses from {url}, missing 'date'.")
                if not "value" in chart_data:
                    raise Exception(
                        f"Invalid responses from {url}, missing 'value'.")

                str_date = datetime.strptime(chart_data["date"], "%Y-%m-%d").strftime("%d-%B-%Y")
                str_value = chart_data["value"]
                str_value = f"{str_value} {aUnit}"
                str_value = str_value.strip()
                # line = f"{str_date} is {str_value} {aUnit}"
                # line = f"{aTitle} is {str_value} {aUnit}"
                # aOutFile.write(f"    {line.strip()}\n")
                outfile.writerow(["Moonchain Daily Report",str_date, aTitle, str_value])


import csv
import json

def export_to_csv(data, filename):
    # データをCSV形式でエクスポートする
    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

def export_to_json(data, filename):
    # データをJSON形式でエクスポートする
    with open(filename, "w") as jsonfile:
        json.dump(data, jsonfile, indent=4)

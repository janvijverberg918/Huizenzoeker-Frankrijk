import csv
import os


def nieuwe_woningen(resultaten, csv_bestand="woningen.csv"):
    """
    Geeft alleen woningen terug die nog niet in het CSV-bestand staan.
    """

    oude_links = set()

    if os.path.exists(csv_bestand):
        with open(csv_bestand, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for rij in reader:
                oude_links.add(rij["link"])

    nieuw = []

    for woning in resultaten:
        if woning["link"] not in oude_links:
            nieuw.append(woning)

    return nieuw
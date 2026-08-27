import csv

from config import CSV_BESTAND
from logger import logger


def opslaan_csv(resultaten, bestandsnaam=CSV_BESTAND):
    """
    Slaat de gevonden woningen op in een CSV-bestand.

    De velden 'perceeloppervlakte' en 'foto' zijn optioneel.
    Voor bronnen die deze velden niet leveren, wordt een lege
    waarde opgeslagen.
    """

    if not resultaten:
        logger.info("Geen woningen om op te slaan")
        print("Geen woningen om op te slaan.")
        return

    veldnamen = [
        "titel",
        "prijs",
        "slaapkamers",
        "oppervlakte",
        "perceeloppervlakte",
        "plaats",
        "link",
        "foto",
        "bron",
    ]

    veilige_resultaten = []

    for woning in resultaten:
        veilige_woning = {
            "titel": woning.get("titel", ""),
            "prijs": woning.get("prijs", ""),
            "slaapkamers": woning.get("slaapkamers", ""),
            "oppervlakte": woning.get("oppervlakte", ""),
            "perceeloppervlakte": woning.get(
                "perceeloppervlakte",
                "",
            ),
            "plaats": woning.get("plaats", ""),
            "link": woning.get("link", ""),
            "foto": woning.get("foto", ""),
            "bron": woning.get("bron", ""),
        }

        veilige_resultaten.append(
            veilige_woning
        )

    try:
        with open(
            bestandsnaam,
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as csvbestand:
            schrijver = csv.DictWriter(
                csvbestand,
                fieldnames=veldnamen,
            )

            schrijver.writeheader()
            schrijver.writerows(
                veilige_resultaten
            )

    except PermissionError:
        logger.exception(
            "CSV-bestand '%s' kon niet worden bijgewerkt",
            bestandsnaam,
        )

        print(
            f"\nKan '{bestandsnaam}' niet bijwerken."
        )

        print(
            "Sluit het bestand in Excel en probeer opnieuw."
        )

        raise

    logger.info(
        "%s woningen opgeslagen in '%s'",
        len(veilige_resultaten),
        bestandsnaam,
    )

    print(
        f"\n{len(veilige_resultaten)} woningen opgeslagen in "
        f"'{bestandsnaam}'"
    )
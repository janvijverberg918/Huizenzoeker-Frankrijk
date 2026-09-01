"""
test_bienici_bron.py

Test van de productie-module bienici.py.

Doel:
- zoek_bienici() testen voor 08600 Givet;
- controleren of 8 woningen binnen de prijsrange worden gevonden;
- CSV/historie testen;
- zoekrecords tonen;
- daarna één detailpagina testen via haal_bienici_advertentie_op().

Nog GEEN:
- integratie in huizenzoeker.py
- AI
- e-mail
"""

from pathlib import Path

from bienici import (
    haal_bienici_advertentie_op,
    zoek_bienici,
)


POSTCODE = "08600"
WONINGTYPE = "huis"
MIN_PRIJS = 80_000
MAX_PRIJS = 220_000

CSV_BESTAND = "test_bienici.csv"


def nette_prijs(waarde):
    if waarde in (
        None,
        "",
    ):
        return "Onbekend"

    return str(
        waarde
    )


def toon_zoekresultaten(
    woningen,
):
    print()
    print("=" * 72)
    print("RESULTAAT TEST BIEN'ICI BRONMODULE")
    print("=" * 72)

    print()
    print(
        f"Nieuwe woningen: "
        f"{len(woningen)}"
    )

    for nummer, woning in enumerate(
        woningen,
        start=1,
    ):

        print()
        print(
            f"[{nummer}] "
            f"{woning.get('titel')}"
        )

        print(
            f"    Prijs       : "
            f"{woning.get('prijs')}"
        )

        print(
            f"    Plaats      : "
            f"{woning.get('plaats')}"
        )

        print(
            f"    Slaapkamers : "
            f"{woning.get('slaapkamers')}"
        )

        print(
            f"    Oppervlakte : "
            f"{woning.get('oppervlakte')} m²"
        )

        print(
            f"    Perceel     : "
            f"{woning.get('perceeloppervlakte')} m²"
        )

        print(
            f"    Link        : "
            f"{woning.get('link')}"
        )

        print(
            f"    Foto        : "
            f"{woning.get('foto')}"
        )

        print(
            f"    Bron        : "
            f"{woning.get('bron')}"
        )

        print(
            f"    Bron sleutel: "
            f"{woning.get('bron_sleutel')}"
        )

    print()
    print("=" * 72)


def toon_detail(
    advertentie,
):
    print()
    print("=" * 72)
    print("DETAILTEST BIEN'ICI")
    print("=" * 72)

    velden = [
        ("Titel", "titel"),
        ("Prijs", "prijs"),
        ("Plaats", "plaats"),
        ("Postcode", "postcode"),
        ("Woonoppervlakte", "woonoppervlakte"),
        ("Perceeloppervlakte", "perceeloppervlakte"),
        ("Kamers", "kamers"),
        ("Slaapkamers", "slaapkamers"),
        ("Badkamers", "badkamers"),
        ("WC", "wc"),
        ("Bouwjaar", "bouwjaar"),
        ("Staat", "staat"),
        ("Verwarming", "verwarming"),
        ("DPE klasse", "dpe_klasse"),
        ("DPE verbruik", "dpe_verbruik"),
        ("GES klasse", "ges_klasse"),
        ("GES uitstoot", "ges_uitstoot"),
        ("Garage", "garage"),
        ("Schuur", "schuur"),
        ("Dependances", "dependances"),
        ("Assainissement", "assainissement"),
        ("Tuin", "tuin"),
        ("Terras", "terras"),
        ("Parking", "parking"),
        ("Aantal foto's", "fotos"),
    ]

    for label, sleutel in velden:

        waarde = advertentie.get(
            sleutel
        )

        if sleutel == "fotos":

            waarde = len(
                waarde or []
            )

        print(
            f"{label:<22}: "
            f"{waarde}"
        )

    print()
    print("-" * 72)
    print("OMSCHRIJVING")
    print("-" * 72)

    print(
        advertentie.get(
            "omschrijving",
            "",
        )
    )

    print()
    print("=" * 72)


def main():
    print("=" * 72)
    print("TEST BIEN'ICI PRODUCTIE-MODULE")
    print("=" * 72)

    print()
    print(
        f"Postcode       : {POSTCODE}"
    )

    print(
        f"Woningtype     : {WONINGTYPE}"
    )

    print(
        f"Minimumprijs   : €{MIN_PRIJS:,}".replace(",", ".")
    )

    print(
        f"Maximumprijs   : €{MAX_PRIJS:,}".replace(",", ".")
    )

    print(
        f"CSV-bestand    : {CSV_BESTAND}"
    )

    # ========================================================
    # ZOEKTEST
    # ========================================================

    woningen = zoek_bienici(
        POSTCODE,
        WONINGTYPE,
        MIN_PRIJS,
        MAX_PRIJS,
        CSV_BESTAND,
    )

    toon_zoekresultaten(
        woningen
    )

    # ========================================================
    # CONTROLE CSV
    # ========================================================

    csv_pad = Path(
        CSV_BESTAND
    )

    print()
    print("=" * 72)
    print("CSV CONTROLE")
    print("=" * 72)

    print()
    print(
        f"CSV bestaat     : "
        f"{csv_pad.exists()}"
    )

    if csv_pad.exists():

        print(
            f"CSV grootte     : "
            f"{csv_pad.stat().st_size:,} bytes"
        )

    # ========================================================
    # DETAILTEST
    # ========================================================

    if not woningen:

        print()
        print(
            "Geen nieuwe woningen teruggekregen."
        )

        print(
            "Detailtest wordt daarom overgeslagen."
        )

        print()
        print(
            "LET OP:"
        )

        print(
            "Dit kan normaal zijn als test_bienici.csv "
            "al bestond en alle woningen daarin staan."
        )

        return

    # Neem eerste woning.
    eerste_woning = woningen[
        0
    ]

    detail_url = eerste_woning.get(
        "link"
    )

    if not detail_url:

        print()
        print(
            "Eerste woning heeft geen detail-URL."
        )

        return

    print()
    print("=" * 72)
    print("DETAILPAGINA OPHALEN")
    print("=" * 72)

    print()
    print(
        detail_url
    )

    advertentie = (
        haal_bienici_advertentie_op(
            detail_url
        )
    )

    toon_detail(
        advertentie
    )

    print()
    print("=" * 72)
    print("SAMENVATTING")
    print("=" * 72)

    print()
    print(
        f"Nieuwe woningen          : "
        f"{len(woningen)}"
    )

    print(
        f"CSV aangemaakt           : "
        f"{csv_pad.exists()}"
    )

    print(
        f"Detailparser uitgevoerd  : "
        f"{advertentie is not None}"
    )

    print(
        f"Detail DPE               : "
        f"{advertentie.get('dpe_klasse')}"
    )

    print(
        f"Detail terrein           : "
        f"{advertentie.get('perceeloppervlakte')}"
    )

    print(
        f"Detail garage            : "
        f"{advertentie.get('garage')}"
    )

    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
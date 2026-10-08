from leboncoin_alerts import combineer_alert_en_detail


def main():

    print("=" * 72)
    print("LEBONCOIN - ALERT + DETAIL COMBINEREN")
    print("=" * 72)

    # --------------------------------------------------------
    # Gegevens uit alertmail
    # --------------------------------------------------------

    alert = {
        "advertentie_id": 3198592008,
        "prijs": 210000,
        "woonoppervlakte": 131,
        "perceeloppervlakte": 670,
        "plaats": "Givet",
        "postcode": "08600",
        "url": (
            "https://www.leboncoin.fr/vi/3198592008.htm"
            "#at_medium=email"
        ),
    }

    # --------------------------------------------------------
    # Voorbeeld detailresultaat
    #
    # Dit komt overeen met wat onze detailparser voor deze
    # advertentie opleverde.
    # --------------------------------------------------------

    detail = {
        "bron": "Leboncoin",
        "advertentie_id": 3198592008,
        "titel": "Maison 5 pièces",
        "prijs": 210000,
        "plaats": "Givet",
        "postcode": "08600",
        "woonoppervlakte": 131,

        # Detailpagina had deze waarde niet:
        "perceeloppervlakte": None,

        "kamers": 5,
        "slaapkamers": 3,
        "badkamers": 2,
        "verwarming": "Fioul",
        "dpe": "G",
        "ges": "F",
        "staat": "À rafraichir",
        "garage": True,
        "tuin": True,
        "aantal_fotos": 3,
        "foto_url": "TEST_FOTO_URL",

        # Canonical URL uit detailpagina
        "url": (
            "https://www.leboncoin.fr/"
            "ad/ventes_immobilieres/3198592008"
        ),
    }

    woning = combineer_alert_en_detail(
        alert,
        detail,
    )

    print("\nGECOMBINEERD WONINGRECORD")
    print("-" * 72)

    for key, value in woning.items():
        print(f"{key:22} : {value}")

    # --------------------------------------------------------
    # Controles
    # --------------------------------------------------------

    print("\nCONTROLES")
    print("-" * 72)

    controles = {
        "perceel uit alert": (
            woning.get("perceeloppervlakte") == 670
        ),

        "slaapkamers uit detail": (
            woning.get("slaapkamers") == 3
        ),

        "verwarming uit detail": (
            woning.get("verwarming") == "Fioul"
        ),

        "DPE uit detail": (
            woning.get("dpe") == "G"
        ),

        "prijs correct": (
            woning.get("prijs") == 210000
        ),
    }

    alles_ok = True

    for naam, resultaat in controles.items():

        status = "OK" if resultaat else "FOUT"

        print(f"{naam:30} : {status}")

        if not resultaat:
            alles_ok = False

    print("\n" + "=" * 72)

    if alles_ok:
        print("ALLE CONTROLES OK")
    else:
        print("ER ZIJN FOUTEN GEVONDEN")

    print("=" * 72)


if __name__ == "__main__":
    main()
from config import maak_csv_bestandsnaam
from immovlan import zoek_immovlan
from immoweb import zoek_immoweb


TESTGEBIEDEN = [
    {
        "naam": "Vielsalm",
        "postcode": "6690",
        "slug": "vielsalm",
    },
    {
        "naam": "Bastogne",
        "postcode": "6600",
        "slug": "bastogne",
    },
    {
        "naam": "Spa",
        "postcode": "4900",
        "slug": "spa",
    },
]


WONINGTYPE = "huis"
MIN_PRIJS = 100000
MAX_PRIJS = 250000


def main():
    totaal = 0
    geslaagd = 0
    mislukt = 0

    print("=" * 60)
    print("TEST ZOEKGEBIEDEN")
    print("=" * 60)

    for gebied in TESTGEBIEDEN:
        naam = gebied["naam"]
        postcode = gebied["postcode"]

        print()
        print("=" * 60)
        print(f"{naam} ({postcode})")
        print("=" * 60)

        # -------------------------------------------------
        # Immoweb
        # -------------------------------------------------
        totaal += 1

        try:
            csv_bestand = maak_csv_bestandsnaam(
                gebied,
                "immoweb",
            )

            resultaten = zoek_immoweb(
                postcode,
                WONINGTYPE,
                MIN_PRIJS,
                MAX_PRIJS,
                csv_bestand,
            )

            print(
                f"IMMOWEB  : OK "
                f"({len(resultaten)} nieuwe woning(en))"
            )

            geslaagd += 1

        except Exception as fout:
            print(
                f"IMMOWEB  : MISLUKT - {fout}"
            )

            mislukt += 1

        # -------------------------------------------------
        # Immovlan
        # -------------------------------------------------
        totaal += 1

        try:
            csv_bestand = maak_csv_bestandsnaam(
                gebied,
                "immovlan",
            )

            resultaten = zoek_immovlan(
                postcode,
                WONINGTYPE,
                MIN_PRIJS,
                MAX_PRIJS,
                csv_bestand,
            )

            print(
                f"IMMOVLAN : OK "
                f"({len(resultaten)} nieuwe woning(en))"
            )

            geslaagd += 1

        except Exception as fout:
            print(
                f"IMMOVLAN : MISLUKT - {fout}"
            )

            mislukt += 1

    print()
    print("=" * 60)
    print("RESULTAAT")
    print("=" * 60)

    print(
        f"Zoekopdrachten totaal   : {totaal}"
    )

    print(
        f"Zoekopdrachten geslaagd : {geslaagd}"
    )

    print(
        f"Zoekopdrachten mislukt  : {mislukt}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()
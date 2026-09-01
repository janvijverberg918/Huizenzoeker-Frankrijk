from pathlib import Path

from bienici import zoek_bienici
from config import ZOEKGEBIEDEN


WONINGTYPE = "huis"
MIN_PRIJS = 80_000
MAX_PRIJS = 220_000


def main():
    print("=" * 72)
    print("BIEN'ICI BULKVALIDATIE - ALLE POSTCODES")
    print("=" * 72)

    totaal_postcodes = len(ZOEKGEBIEDEN)
    geslaagd = 0
    mislukt = 0
    totaal_woningen = 0

    fouten = []

    for nummer, gebied in enumerate(
        ZOEKGEBIEDEN,
        start=1,
    ):
        postcode = gebied["postcode"]
        departement = gebied.get(
            "departement",
            "",
        )

        csv_bestand = (
            f"test_bienici_bulk_{postcode}.csv"
        )

        print()
        print("#" * 72)
        print(
            f"[{nummer}/{totaal_postcodes}] "
            f"POSTCODE {postcode} - {departement}"
        )
        print("#" * 72)

        try:
            woningen = zoek_bienici(
                postcode,
                WONINGTYPE,
                MIN_PRIJS,
                MAX_PRIJS,
                csv_bestand,
            )

            aantal = len(
                woningen
            )

            totaal_woningen += aantal
            geslaagd += 1

            print(
                f"Resultaat         : GESLAAGD"
            )
            print(
                f"Nieuwe woningen   : {aantal}"
            )

            csv_pad = Path(
                csv_bestand
            )

            print(
                f"CSV bestaat       : "
                f"{csv_pad.exists()}"
            )

            if csv_pad.exists():
                print(
                    f"CSV grootte       : "
                    f"{csv_pad.stat().st_size:,} bytes"
                )

        except Exception as fout:
            mislukt += 1

            fouten.append(
                {
                    "postcode": postcode,
                    "departement": departement,
                    "fout": str(fout),
                }
            )

            print(
                "Resultaat         : MISLUKT"
            )
            print(
                f"Fout              : {fout}"
            )

    print()
    print()
    print("=" * 72)
    print("EINDSAMENVATTING")
    print("=" * 72)

    print(
        f"Postcodes totaal   : {totaal_postcodes}"
    )
    print(
        f"Geslaagd           : {geslaagd}"
    )
    print(
        f"Mislukt            : {mislukt}"
    )
    print(
        f"Totaal nieuw       : {totaal_woningen}"
    )

    if fouten:
        print()
        print("-" * 72)
        print("MISLUKTE POSTCODES")
        print("-" * 72)

        for fout in fouten:
            print(
                f"{fout['postcode']} "
                f"({fout['departement']}): "
                f"{fout['fout']}"
            )

    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
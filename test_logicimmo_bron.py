from logicimmo import zoek_logicimmo


POSTCODE = "08600"
WONINGTYPE = "huis"
MIN_PRIJS = 80_000
MAX_PRIJS = 220_000
CSV_BESTAND = "test_logicimmo.csv"


def main():

    woningen = zoek_logicimmo(
        POSTCODE,
        WONINGTYPE,
        MIN_PRIJS,
        MAX_PRIJS,
        CSV_BESTAND,
    )

    print()
    print("=" * 70)
    print("RESULTAAT TEST LOGIC-IMMO BRONMODULE")
    print("=" * 70)

    print(
        f"Nieuwe woningen: {len(woningen)}"
    )

    for nummer, woning in enumerate(
        woningen,
        start=1,
    ):

        print()
        print(
            f"[{nummer}] {woning['titel']}"
        )

        print(
            f"    Prijs       : {woning['prijs']}"
        )

        print(
            f"    Plaats      : {woning['plaats']}"
        )

        print(
            f"    Slaapkamers : {woning['slaapkamers']}"
        )

        print(
            f"    Oppervlakte : {woning['oppervlakte']} m²"
        )

        print(
            f"    Link        : {woning['link']}"
        )

        print(
            f"    Foto        : {woning['foto']}"
        )

        print(
            f"    Bron        : {woning['bron']}"
        )

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
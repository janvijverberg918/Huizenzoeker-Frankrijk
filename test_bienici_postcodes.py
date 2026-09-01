from pathlib import Path

from bienici import zoek_bienici


TESTS = [
    {
        "postcode": "08320",
        "woningtype": "huis",
        "min_prijs": 80_000,
        "max_prijs": 220_000,
    },
    {
        "postcode": "02830",
        "woningtype": "huis",
        "min_prijs": 80_000,
        "max_prijs": 220_000,
    },
    {
        "postcode": "55700",
        "woningtype": "huis",
        "min_prijs": 80_000,
        "max_prijs": 220_000,
    },
]


def toon_resultaten(
    postcode,
    woningen,
):
    print()
    print("=" * 72)
    print(
        f"RESULTATEN POSTCODE {postcode}"
    )
    print("=" * 72)

    print(
        f"Nieuwe woningen: {len(woningen)}"
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


def main():

    print("=" * 72)
    print("BIEN'ICI MULTI-POSTCODE TEST")
    print("=" * 72)

    totaal_nieuw = 0

    for test in TESTS:

        postcode = test[
            "postcode"
        ]

        csv_bestand = (
            f"test_bienici_{postcode}.csv"
        )

        print()
        print()
        print("#" * 72)
        print(
            f"TEST POSTCODE {postcode}"
        )
        print("#" * 72)

        print(
            f"CSV-bestand: {csv_bestand}"
        )

        woningen = zoek_bienici(
            postcode,
            test[
                "woningtype"
            ],
            test[
                "min_prijs"
            ],
            test[
                "max_prijs"
            ],
            csv_bestand,
        )

        toon_resultaten(
            postcode,
            woningen,
        )

        totaal_nieuw += len(
            woningen
        )

        csv_pad = Path(
            csv_bestand
        )

        print()
        print(
            f"CSV bestaat: "
            f"{csv_pad.exists()}"
        )

        if csv_pad.exists():

            print(
                f"CSV grootte: "
                f"{csv_pad.stat().st_size:,} bytes"
            )

    print()
    print()
    print("=" * 72)
    print("SAMENVATTING")
    print("=" * 72)

    print(
        f"Geteste postcodes : "
        f"{len(TESTS)}"
    )

    print(
        f"Totaal nieuw      : "
        f"{totaal_nieuw}"
    )

    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
from pathlib import Path

import leboncoin_alerts


TEST_FILE = Path("test_leboncoin_verwerkt.json")


def main():
    print("=" * 72)
    print("LEBONCOIN - VERWERKTE ADVERTENTIES TEST")
    print("=" * 72)

    # Gebruik tijdens deze test NIET het echte productie/history-bestand.
    originele_file = leboncoin_alerts.VERWERKT_FILE
    leboncoin_alerts.VERWERKT_FILE = TEST_FILE

    try:
        if TEST_FILE.exists():
            TEST_FILE.unlink()

        advertenties = [
            {
                "advertentie_id": 3198592008,
                "prijs": 210000,
            },
            {
                "advertentie_id": 3268053815,
                "prijs": 120000,
            },
        ]

        print("\nSTAP 1 - Nieuw bestand")
        print("-" * 72)

        nieuwe = leboncoin_alerts.filter_nieuwe_advertenties(
            advertenties
        )

        print(f"Nieuwe advertenties: {len(nieuwe)}")

        assert len(nieuwe) == 2

        # ----------------------------------------------------
        # Eén advertentie succesvol verwerken
        # ----------------------------------------------------

        print("\nSTAP 2 - Advertentie 3198592008 markeren")
        print("-" * 72)

        leboncoin_alerts.markeer_als_verwerkt(
            3198592008
        )

        print(
            "3198592008 verwerkt:",
            leboncoin_alerts.is_al_verwerkt(
                3198592008
            ),
        )

        print(
            "3268053815 verwerkt:",
            leboncoin_alerts.is_al_verwerkt(
                3268053815
            ),
        )

        assert leboncoin_alerts.is_al_verwerkt(
            3198592008
        )

        assert not leboncoin_alerts.is_al_verwerkt(
            3268053815
        )

        # ----------------------------------------------------
        # Nogmaals filteren
        # ----------------------------------------------------

        print("\nSTAP 3 - Opnieuw filteren")
        print("-" * 72)

        nieuwe = leboncoin_alerts.filter_nieuwe_advertenties(
            advertenties
        )

        print(f"Nieuwe advertenties: {len(nieuwe)}")

        for advertentie in nieuwe:
            print(
                "Nog te verwerken:",
                advertentie["advertentie_id"],
            )

        assert len(nieuwe) == 1
        assert nieuwe[0]["advertentie_id"] == 3268053815

        # ----------------------------------------------------
        # Tweede advertentie markeren
        # ----------------------------------------------------

        print("\nSTAP 4 - Tweede advertentie markeren")
        print("-" * 72)

        leboncoin_alerts.markeer_als_verwerkt(
            3268053815
        )

        nieuwe = leboncoin_alerts.filter_nieuwe_advertenties(
            advertenties
        )

        print(f"Nieuwe advertenties: {len(nieuwe)}")

        assert len(nieuwe) == 0

        print("\n" + "=" * 72)
        print("ALLE CONTROLES OK")
        print("=" * 72)

    finally:
        # Testbestand opruimen.
        if TEST_FILE.exists():
            TEST_FILE.unlink()

        leboncoin_alerts.VERWERKT_FILE = originele_file


if __name__ == "__main__":
    main()
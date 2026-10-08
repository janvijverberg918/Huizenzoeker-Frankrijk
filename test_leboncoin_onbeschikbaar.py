from pathlib import Path

import leboncoin_alerts


TEST_VERWERKT = Path(
    "test_leboncoin_verwerkt.json"
)

TEST_ONBESCHIKBAAR = Path(
    "test_leboncoin_onbeschikbaar.json"
)


def main():
    print("=" * 72)
    print("LEBONCOIN - ONBESCHIKBAAR TEST")
    print("=" * 72)

    originele_verwerkt = (
        leboncoin_alerts.VERWERKT_FILE
    )

    originele_onbeschikbaar = (
        leboncoin_alerts.ONBESCHIKBAAR_FILE
    )

    leboncoin_alerts.VERWERKT_FILE = (
        TEST_VERWERKT
    )

    leboncoin_alerts.ONBESCHIKBAAR_FILE = (
        TEST_ONBESCHIKBAAR
    )

    try:
        for bestand in [
            TEST_VERWERKT,
            TEST_ONBESCHIKBAAR,
        ]:
            if bestand.exists():
                bestand.unlink()

        advertenties = [
            {
                "advertentie_id": 1001,
            },
            {
                "advertentie_id": 1002,
            },
            {
                "advertentie_id": 1003,
            },
        ]

        # ----------------------------------------------------
        # STAP 1
        # ----------------------------------------------------

        print("\nSTAP 1 - Alle advertenties zijn nieuw")
        print("-" * 72)

        nieuwe = (
            leboncoin_alerts
            .filter_nieuwe_advertenties(
                advertenties
            )
        )

        print(
            f"Nieuwe advertenties: "
            f"{len(nieuwe)}"
        )

        assert len(nieuwe) == 3

        # ----------------------------------------------------
        # STAP 2
        # ----------------------------------------------------

        print(
            "\nSTAP 2 - 1001 succesvol verwerkt"
        )
        print("-" * 72)

        leboncoin_alerts.markeer_als_verwerkt(
            1001
        )

        nieuwe = (
            leboncoin_alerts
            .filter_nieuwe_advertenties(
                advertenties
            )
        )

        print(
            f"Nieuwe advertenties: "
            f"{len(nieuwe)}"
        )

        assert len(nieuwe) == 2

        # ----------------------------------------------------
        # STAP 3
        # ----------------------------------------------------

        print(
            "\nSTAP 3 - 1002 definitief onbeschikbaar"
        )
        print("-" * 72)

        leboncoin_alerts.markeer_als_onbeschikbaar(
            1002
        )

        print(
            "1002 onbeschikbaar:",
            leboncoin_alerts.is_onbeschikbaar(
                1002
            ),
        )

        nieuwe = (
            leboncoin_alerts
            .filter_nieuwe_advertenties(
                advertenties
            )
        )

        print(
            f"Nieuwe advertenties: "
            f"{len(nieuwe)}"
        )

        for advertentie in nieuwe:
            print(
                "Nog te verwerken:",
                advertentie["advertentie_id"],
            )

        assert len(nieuwe) == 1
        assert (
            nieuwe[0]["advertentie_id"]
            == 1003
        )

        # ----------------------------------------------------
        # CONTROLE
        # ----------------------------------------------------

        assert (
            leboncoin_alerts.is_al_verwerkt(
                1001
            )
        )

        assert (
            leboncoin_alerts.is_onbeschikbaar(
                1002
            )
        )

        assert not (
            leboncoin_alerts.is_al_verwerkt(
                1002
            )
        )

        assert not (
            leboncoin_alerts.is_onbeschikbaar(
                1003
            )
        )

        print("\n" + "=" * 72)
        print("ALLE CONTROLES OK")
        print("=" * 72)

    finally:
        for bestand in [
            TEST_VERWERKT,
            TEST_ONBESCHIKBAAR,
        ]:
            if bestand.exists():
                bestand.unlink()

        leboncoin_alerts.VERWERKT_FILE = (
            originele_verwerkt
        )

        leboncoin_alerts.ONBESCHIKBAAR_FILE = (
            originele_onbeschikbaar
        )


if __name__ == "__main__":
    main()
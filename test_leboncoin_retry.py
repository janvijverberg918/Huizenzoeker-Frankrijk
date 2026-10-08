from pathlib import Path

import leboncoin_alerts


TEST_VERWERKT = Path(
    "test_leboncoin_verwerkt.json"
)

TEST_ONBESCHIKBAAR = Path(
    "test_leboncoin_onbeschikbaar.json"
)

TEST_RETRY = Path(
    "test_leboncoin_retry.json"
)


def main():
    print("=" * 72)
    print("LEBONCOIN - RETRY / COOLDOWN TEST")
    print("=" * 72)

    origineel_verwerkt = (
        leboncoin_alerts.VERWERKT_FILE
    )

    origineel_onbeschikbaar = (
        leboncoin_alerts.ONBESCHIKBAAR_FILE
    )

    origineel_retry = (
        leboncoin_alerts.RETRY_FILE
    )

    leboncoin_alerts.VERWERKT_FILE = (
        TEST_VERWERKT
    )

    leboncoin_alerts.ONBESCHIKBAAR_FILE = (
        TEST_ONBESCHIKBAAR
    )

    leboncoin_alerts.RETRY_FILE = (
        TEST_RETRY
    )

    try:
        for bestand in [
            TEST_VERWERKT,
            TEST_ONBESCHIKBAAR,
            TEST_RETRY,
        ]:
            if bestand.exists():
                bestand.unlink()

        advertenties = [
            {"advertentie_id": 1001},
            {"advertentie_id": 1002},
            {"advertentie_id": 1003},
        ]

        # ----------------------------------------------------
        # STAP 1
        # ----------------------------------------------------

        print(
            "\nSTAP 1 - Alle advertenties zijn nieuw"
        )
        print("-" * 72)

        nieuwe = (
            leboncoin_alerts
            .filter_nieuwe_advertenties(
                advertenties
            )
        )

        print(
            f"Nieuwe advertenties: {len(nieuwe)}"
        )

        assert len(nieuwe) == 3

        # ----------------------------------------------------
        # STAP 2
        # ----------------------------------------------------

        print(
            "\nSTAP 2 - Tijdelijke fout voor 1001"
        )
        print("-" * 72)

        leboncoin_alerts.registreer_retry(
            1001,
            "HTTP status 403",
        )

        print(
            "1001 direct opnieuw proberen:",
            leboncoin_alerts.mag_opnieuw_proberen(
                1001
            ),
        )

        assert not (
            leboncoin_alerts.mag_opnieuw_proberen(
                1001
            )
        )

        nieuwe = (
            leboncoin_alerts
            .filter_nieuwe_advertenties(
                advertenties
            )
        )

        print(
            f"Nieuwe advertenties: {len(nieuwe)}"
        )

        assert len(nieuwe) == 2

        # ----------------------------------------------------
        # STAP 3
        # ----------------------------------------------------

        print(
            "\nSTAP 3 - Cooldown simuleren"
        )
        print("-" * 72)

        print(
            "1001 met cooldown 0 uur:",
            leboncoin_alerts.mag_opnieuw_proberen(
                1001,
                cooldown_uren=0,
            ),
        )

        assert (
            leboncoin_alerts.mag_opnieuw_proberen(
                1001,
                cooldown_uren=0,
            )
        )

        # ----------------------------------------------------
        # STAP 4
        # ----------------------------------------------------

        print(
            "\nSTAP 4 - Retry verwijderen na succes"
        )
        print("-" * 72)

        leboncoin_alerts.verwijder_retry(
            1001
        )

        print(
            "1001 na verwijderen retry:",
            leboncoin_alerts.mag_opnieuw_proberen(
                1001
            ),
        )

        assert (
            leboncoin_alerts.mag_opnieuw_proberen(
                1001
            )
        )

        # ----------------------------------------------------
        # STAP 5
        # ----------------------------------------------------

        print(
            "\nSTAP 5 - Aantal pogingen controleren"
        )
        print("-" * 72)

        leboncoin_alerts.registreer_retry(
            1002,
            "HTTP status 403",
        )

        leboncoin_alerts.registreer_retry(
            1002,
            "HTTP status 403",
        )

        retries = leboncoin_alerts.laad_retries()

        print(
            "Aantal pogingen 1002:",
            retries["1002"]["pogingen"],
        )

        assert (
            retries["1002"]["pogingen"]
            == 2
        )

        print("\n" + "=" * 72)
        print("ALLE CONTROLES OK")
        print("=" * 72)

    finally:
        for bestand in [
            TEST_VERWERKT,
            TEST_ONBESCHIKBAAR,
            TEST_RETRY,
        ]:
            if bestand.exists():
                bestand.unlink()

        leboncoin_alerts.VERWERKT_FILE = (
            origineel_verwerkt
        )

        leboncoin_alerts.ONBESCHIKBAAR_FILE = (
            origineel_onbeschikbaar
        )

        leboncoin_alerts.RETRY_FILE = (
            origineel_retry
        )


if __name__ == "__main__":
    main()
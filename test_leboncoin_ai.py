from leboncoin import haal_detail_op

from leboncoin_alerts import (
    combineer_alert_en_detail,
)

from leboncoin_huizencoach import (
    maak_huizencoach_woning,
)

from ai_analyse import (
    analyseer_woning,
    toon_analyse,
)


ALERT = {
    "advertentie_id": 3265392486,
    "prijs": 85000,
    "woonoppervlakte": 70,
    "perceeloppervlakte": None,
    "plaats": "Givet",
    "postcode": "08600",
    "url": (
        "https://www.leboncoin.fr/vi/3265392486.htm"
        "#at_medium=email"
        "&at_emailtype=retention"
        "&at_campaign="
        "fr_lbc_immo_searchp_emllbc_part_click-ad-saved-search-other__alert"
    ),
}


def main():
    print("=" * 72)
    print("LEBONCOIN - ECHTE AI HUIZENCOACH TEST")
    print("=" * 72)

    # --------------------------------------------------------
    # STAP 1 - Leboncoin detail ophalen
    # --------------------------------------------------------

    print("\nSTAP 1 - Detailpagina ophalen")
    print("-" * 72)

    try:
        detail = haal_detail_op(
            ALERT["url"]
        )

    except Exception as exc:
        print(
            f"FOUT bij detailpagina: "
            f"{type(exc).__name__}: {exc}"
        )
        return

    print("Detailpagina: OK")

    # --------------------------------------------------------
    # STAP 2 - Alert + detail
    # --------------------------------------------------------

    print("\nSTAP 2 - Alert + detail combineren")
    print("-" * 72)

    gecombineerd = combineer_alert_en_detail(
        ALERT,
        detail,
    )

    print("Combineren: OK")

    # --------------------------------------------------------
    # STAP 3 - Naar generiek Huizencoach-record
    # --------------------------------------------------------

    print("\nSTAP 3 - Huizencoach-record maken")
    print("-" * 72)

    woning = maak_huizencoach_woning(
        gecombineerd
    )

    print(
        f"Woning : {woning.get('titel')}"
    )
    print(
        f"Prijs  : {woning.get('prijs')}"
    )
    print(
        f"Plaats : {woning.get('plaats')}"
    )
    print(
        f"Bron   : {woning.get('bron')}"
    )

    # --------------------------------------------------------
    # STAP 4 - AI Huizencoach
    # --------------------------------------------------------

    print("\nSTAP 4 - AI Huizencoach analyse")
    print("-" * 72)

    try:
        analyse = analyseer_woning(
            woning
        )

    except Exception as exc:
        print(
            f"FOUT bij AI-analyse: "
            f"{type(exc).__name__}: {exc}"
        )
        return

    # --------------------------------------------------------
    # STAP 5 - Analyse tonen
    # --------------------------------------------------------

    toon_analyse(
        analyse
    )

    print()
    print("=" * 72)
    print("AI TEST AFGEROND")
    print("=" * 72)


if __name__ == "__main__":
    main()
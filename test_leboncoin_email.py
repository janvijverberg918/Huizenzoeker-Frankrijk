from leboncoin import haal_detail_op

from leboncoin_alerts import (
    combineer_alert_en_detail,
)

from leboncoin_huizencoach import (
    maak_huizencoach_woning,
    voeg_ai_analyse_toe,
)

from ai_analyse import (
    analyseer_woning,
)

from emailer import (
    stuur_nieuwe_woningen,
)


# ============================================================
# TESTDATA
# ============================================================

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
    print("LEBONCOIN - ECHTE EMAIL TEST")
    print("=" * 72)

    # --------------------------------------------------------
    # STAP 1 - Detailpagina ophalen
    # --------------------------------------------------------

    print()
    print("STAP 1 - Detailpagina ophalen")
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
    # STAP 2 - Alert + detail combineren
    # --------------------------------------------------------

    print()
    print("STAP 2 - Alert + detail combineren")
    print("-" * 72)

    gecombineerd = combineer_alert_en_detail(
        ALERT,
        detail,
    )

    print("Combineren: OK")

    # --------------------------------------------------------
    # STAP 3 - Huizencoach-record maken
    # --------------------------------------------------------

    print()
    print("STAP 3 - Huizencoach-record maken")
    print("-" * 72)

    woning = maak_huizencoach_woning(
        gecombineerd
    )

    print(f"Woning : {woning.get('titel')}")
    print(f"Prijs  : {woning.get('prijs')}")
    print(f"Plaats : {woning.get('plaats')}")
    print(f"Foto's : {len(woning.get('fotos', []))}")

    # --------------------------------------------------------
    # STAP 4 - AI-analyse
    # --------------------------------------------------------

    print()
    print("STAP 4 - AI Huizencoach")
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

    print(
        f"Score  : {analyse.get('score')}"
    )
    print(
        f"Advies : {analyse.get('advies')}"
    )

    # --------------------------------------------------------
    # STAP 5 - AI aan woning toevoegen
    # --------------------------------------------------------

    print()
    print("STAP 5 - E-mailrecord maken")
    print("-" * 72)

    email_woning = voeg_ai_analyse_toe(
        woning,
        analyse,
    )

    print("E-mailrecord: OK")
    print(
        f"Bron   : {email_woning.get('bron')}"
    )
    print(
        f"Link   : {email_woning.get('link')}"
    )

    # --------------------------------------------------------
    # STAP 6 - Echte e-mail versturen
    # --------------------------------------------------------

    print()
    print("STAP 6 - E-mail versturen")
    print("-" * 72)

    try:
        resultaat = stuur_nieuwe_woningen(
            [email_woning]
        )
    except Exception as exc:
        print()
        print(
            f"FOUT bij versturen e-mail: "
            f"{type(exc).__name__}: {exc}"
        )
        return

    print()
    print(f"Resultaat emailer: {resultaat}")

    print()
    print("=" * 72)
    print("EMAIL TEST AFGEROND")
    print("=" * 72)


if __name__ == "__main__":
    main()
    
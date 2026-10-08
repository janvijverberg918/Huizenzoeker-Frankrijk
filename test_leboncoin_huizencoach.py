from leboncoin import haal_detail_op

from leboncoin_alerts import (
    combineer_alert_en_detail,
)

from leboncoin_huizencoach import (
    maak_huizencoach_woning,
    toon_huizencoach_woning,
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


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 72)
    print("LEBONCOIN - AI HUIZENCOACH ADAPTER TEST")
    print("=" * 72)

    # --------------------------------------------------------
    # STAP 1 - Detailpagina ophalen
    # --------------------------------------------------------

    print()
    print("STAP 1 - Leboncoin detailpagina ophalen")
    print("-" * 72)

    print(
        f"Advertentie ID : "
        f"{ALERT['advertentie_id']}"
    )

    print(
        f"Alert URL      : "
        f"{ALERT['url']}"
    )

    try:
        detail = haal_detail_op(
            ALERT["url"]
        )

    except Exception as exc:
        print()
        print("FOUT bij ophalen detailpagina:")
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return

    print("Detailpagina verwerkt: OK")

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

    print(
        "Gecombineerd woningrecord: OK"
    )

    print()
    print("BELANGRIJKE BRONVELDEN")
    print("-" * 72)

    controle_velden = [
        "advertentie_id",
        "titel",
        "prijs",
        "plaats",
        "postcode",
        "woonoppervlakte",
        "perceeloppervlakte",
        "slaapkamers",
        "badkamers",
        "verwarming",
        "dpe",
        "ges",
        "staat",
        "garage",
        "tuin",
        "aantal_fotos",
        "foto_url",
        "url",
    ]

    for veld in controle_velden:
        print(
            f"{veld:22}: "
            f"{gecombineerd.get(veld)}"
        )

    # --------------------------------------------------------
    # STAP 3 - Converteren naar Huizencoach
    # --------------------------------------------------------

    print()
    print(
        "STAP 3 - Converteren naar AI Huizencoach-formaat"
    )
    print("-" * 72)

    try:
        woning = maak_huizencoach_woning(
            gecombineerd
        )

    except Exception as exc:
        print()
        print("FOUT bij conversie:")
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return

    print("Conversie: OK")

    # --------------------------------------------------------
    # STAP 4 - Structuur controleren
    # --------------------------------------------------------

    print()
    print("STAP 4 - Structuur controleren")
    print("-" * 72)

    verplichte_velden = [
        "advertentie_id",
        "titel",
        "prijs",
        "plaats",
        "beschrijving",
        "kenmerken_tekst",
        "kenmerken",
        "fotos",
        "bron",
        "link",
    ]

    fouten = []

    for veld in verplichte_velden:
        aanwezig = veld in woning

        print(
            f"{veld:22}: "
            f"{'OK' if aanwezig else 'ONTBREEKT'}"
        )

        if not aanwezig:
            fouten.append(
                f"Veld ontbreekt: {veld}"
            )

    if not isinstance(
        woning.get("kenmerken"),
        dict,
    ):
        fouten.append(
            "kenmerken is geen dictionary"
        )

    if not isinstance(
        woning.get("fotos"),
        list,
    ):
        fouten.append(
            "fotos is geen lijst"
        )

    if woning.get("bron") != "Leboncoin":
        fouten.append(
            "bron is niet Leboncoin"
        )

    if (
        woning.get("advertentie_id")
        != ALERT["advertentie_id"]
    ):
        fouten.append(
            "advertentie_id is gewijzigd"
        )

    # --------------------------------------------------------
    # STAP 5 - Waarden controleren
    # --------------------------------------------------------

    print()
    print("STAP 5 - Waarden controleren")
    print("-" * 72)

    kenmerken = woning.get(
        "kenmerken",
        {},
    )

    controles = {
        "prijs": woning.get("prijs"),
        "plaats": woning.get("plaats"),
        "woonoppervlakte": kenmerken.get(
            "woonoppervlakte"
        ),
        "perceeloppervlakte": kenmerken.get(
            "perceeloppervlakte"
        ),
        "slaapkamers": kenmerken.get(
            "slaapkamers"
        ),
        "badkamers": kenmerken.get(
            "badkamers"
        ),
        "verwarming": kenmerken.get(
            "verwarming"
        ),
        "epc": kenmerken.get(
            "epc"
        ),
        "staat": kenmerken.get(
            "staat"
        ),
        "garage": kenmerken.get(
            "garage"
        ),
        "tuin": kenmerken.get(
            "tuin"
        ),
    }

    for veld, waarde in controles.items():
        print(
            f"{veld:22}: {waarde}"
        )

    # --------------------------------------------------------
    # STAP 6 - Volledig Huizencoach-record tonen
    # --------------------------------------------------------

    toon_huizencoach_woning(
        woning
    )

    # --------------------------------------------------------
    # Eindcontrole
    # --------------------------------------------------------

    print()
    print("=" * 72)

    if fouten:
        print("TEST NIET VOLLEDIG GESLAAGD")
        print("=" * 72)

        for fout in fouten:
            print(
                f"- {fout}"
            )

        return

    print("ALLE STRUCTUURCONTROLES OK")
    print("=" * 72)


if __name__ == "__main__":
    main()
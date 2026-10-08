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
    print("LEBONCOIN - AI → EMAILRECORD TEST")
    print("=" * 72)

    # --------------------------------------------------------
    # STAP 1 - Detail
    # --------------------------------------------------------

    print()
    print("STAP 1 - Detailpagina ophalen")
    print("-" * 72)

    detail = haal_detail_op(
        ALERT["url"]
    )

    print("Detailpagina: OK")

    # --------------------------------------------------------
    # STAP 2 - Combineren
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
    # STAP 3 - Huizencoach-record
    # --------------------------------------------------------

    print()
    print("STAP 3 - Huizencoach-record maken")
    print("-" * 72)

    woning = maak_huizencoach_woning(
        gecombineerd
    )

    print("Huizencoach-record: OK")

    # --------------------------------------------------------
    # STAP 4 - AI
    # --------------------------------------------------------

    print()
    print("STAP 4 - AI-analyse")
    print("-" * 72)

    analyse = analyseer_woning(
        woning
    )

    print("AI-analyse: OK")

    # --------------------------------------------------------
    # STAP 5 - AI toevoegen aan woningrecord
    # --------------------------------------------------------

    print()
    print("STAP 5 - AI toevoegen aan e-mailrecord")
    print("-" * 72)

    email_woning = voeg_ai_analyse_toe(
        woning,
        analyse,
    )

    velden = [
        "ai_score",
        "ai_advies",
        "ai_betrouwbaarheid",
        "ai_samenvatting",
        "ai_sterke_punten",
        "ai_aandachtspunten",
        "ai_ontbrekende_informatie",
    ]

    fouten = []

    for veld in velden:
        waarde = email_woning.get(
            veld
        )

        print(
            f"{veld:30}: {waarde}"
        )

        if veld not in email_woning:
            fouten.append(
                f"{veld} ontbreekt"
            )

    # --------------------------------------------------------
    # STAP 6 - Basiswoning controleren
    # --------------------------------------------------------

    print()
    print("STAP 6 - Basisgegevens controleren")
    print("-" * 72)

    print(
        f"Titel     : {email_woning.get('titel')}"
    )
    print(
        f"Prijs     : {email_woning.get('prijs')}"
    )
    print(
        f"Plaats    : {email_woning.get('plaats')}"
    )
    print(
        f"Bron      : {email_woning.get('bron')}"
    )
    print(
        f"Foto's    : {len(email_woning.get('fotos', []))}"
    )
    print(
        f"Link      : {email_woning.get('link')}"
    )

    # --------------------------------------------------------
    # EINDRESULTAAT
    # --------------------------------------------------------

    print()
    print("=" * 72)

    if fouten:
        print("TEST NIET GESLAAGD")

        for fout in fouten:
            print(
                f"- {fout}"
            )

    else:
        print("ALLE CONTROLES OK")

    print("=" * 72)


if __name__ == "__main__":
    main()
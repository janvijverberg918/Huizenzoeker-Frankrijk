from leboncoin import haal_detail_op
from leboncoin_alerts import (
    parse_leboncoin_alert,
    combineer_alert_en_detail,
)

ALERT_BODY = """
Bonjour Jan Vijverberg,

2 nouvelles annonces immobilières correspondant à vos critères de recherche :

[210 000 €

1 603 €/m²

Maison · 5 pièces · 131 m²

Terrain : 670m²

Givet 08600

Voir l'annonce](https://www.leboncoin.fr/vi/3198592008.htm#at_medium=email&at_emailtype=retention&at_campaign=fr_lbc_immo_searchp_emllbc_part_click-ad-saved-search-other__alert)

[120 000 €

759 €/m²

Maison · 7 pièces · 158 m²

Terrain : 50m²

Givet 08600

Voir l'annonce](https://www.leboncoin.fr/vi/3268053815.htm#at_medium=email&at_emailtype=retention&at_campaign=fr_lbc_immo_searchp_emllbc_part_click-ad-saved-search-other__alert)
"""



def main():
    print("=" * 72)
    print("LEBONCOIN - END TO END TEST")
    print("=" * 72)

    print(f"Lengte ALERT_BODY: {len(ALERT_BODY)}")
    print("Bevat /vi/:", "/vi/" in ALERT_BODY)

    alerts = parse_leboncoin_alert(ALERT_BODY)

    print(f"\nAantal advertenties in alert: {len(alerts)}")

    eindresultaten = []

    for nummer, alert in enumerate(alerts, start=1):
        print("\n" + "=" * 72)
        print(f"ADVERTENTIE {nummer}")
        print("=" * 72)

        try:
            detail = haal_detail_op(
                alert["url"]
            )

            woning = combineer_alert_en_detail(
                alert,
                detail,
            )

            eindresultaten.append(woning)

            for key, value in woning.items():
                if key == "beschrijving":
                    continue

                print(f"{key:22} : {value}")

        except Exception as exc:
            print(f"FOUT: {exc}")

    print("\n" + "=" * 72)
    print(f"EINDRESULTATEN: {len(eindresultaten)}")
    print("=" * 72)


if __name__ == "__main__":
    main()
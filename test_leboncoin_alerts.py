from leboncoin_alerts import parse_leboncoin_alert
from datetime import datetime, timedelta, timezone

RETRY_FILE = Path("leboncoin_retry.json")
RETRY_COOLDOWN_UREN = 12


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
    print("LEBONCOIN - ALERT PARSER TEST")
    print("=" * 72)

    advertenties = parse_leboncoin_alert(ALERT_BODY)

    print(f"\nAantal advertenties: {len(advertenties)}")

    for nummer, advertentie in enumerate(advertenties, start=1):
        print("\n" + "-" * 72)
        print(f"Advertentie {nummer}")
        print("-" * 72)

        for key, value in advertentie.items():
            print(f"{key:22} : {value}")

    print("\n" + "=" * 72)
    print("TEST AFGEROND")
    print("=" * 72)


if __name__ == "__main__":
    main()
def laad_retries():
    """
    Leest de administratie van tijdelijke fouten.
    """

    if not RETRY_FILE.exists():
        return {}

    try:
        data = json.loads(
            RETRY_FILE.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(data, dict):
            raise ValueError(
                "Retry-bestand bevat geen dictionary."
            )

        return data

    except (
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ) as exc:
        raise RuntimeError(
            f"Kan {RETRY_FILE} niet lezen: {exc}"
        ) from exc


def sla_retries_op(retries):
    """
    Schrijft de retry-administratie naar JSON.
    """

    RETRY_FILE.write_text(
        json.dumps(
            retries,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def registreer_retry(advertentie_id, fout):
    """
    Registreert een tijdelijke fout.

    Bewaart:
    - aantal pogingen;
    - laatste fout;
    - tijdstip laatste poging.
    """

    retries = laad_retries()

    sleutel = str(
        int(advertentie_id)
    )

    bestaand = retries.get(
        sleutel,
        {}
    )

    pogingen = (
        int(bestaand.get("pogingen", 0))
        + 1
    )

    retries[sleutel] = {
        "pogingen": pogingen,
        "laatste_fout": str(fout),
        "laatste_poging": (
            datetime.now(timezone.utc)
            .isoformat()
        ),
    }

    sla_retries_op(
        retries
    )


def verwijder_retry(advertentie_id):
    """
    Verwijdert een retry-record nadat een advertentie
    succesvol verwerkt of definitief onbeschikbaar is.
    """

    retries = laad_retries()

    sleutel = str(
        int(advertentie_id)
    )

    if sleutel in retries:
        del retries[sleutel]

        sla_retries_op(
            retries
        )


def mag_opnieuw_proberen(
    advertentie_id,
    cooldown_uren=RETRY_COOLDOWN_UREN,
):
    """
    True wanneer:
    - er nog geen tijdelijke fout geregistreerd is; of
    - de cooldown sinds de laatste poging verstreken is.
    """

    retries = laad_retries()

    sleutel = str(
        int(advertentie_id)
    )

    retry = retries.get(
        sleutel
    )

    if retry is None:
        return True

    laatste_poging = retry.get(
        "laatste_poging"
    )

    if not laatste_poging:
        return True

    try:
        tijdstip = datetime.fromisoformat(
            laatste_poging
        )

    except ValueError:
        return True

    if tijdstip.tzinfo is None:
        tijdstip = tijdstip.replace(
            tzinfo=timezone.utc
        )

    volgende_poging = (
        tijdstip
        + timedelta(
            hours=cooldown_uren
        )
    )

    return (
        datetime.now(timezone.utc)
        >= volgende_poging
    )
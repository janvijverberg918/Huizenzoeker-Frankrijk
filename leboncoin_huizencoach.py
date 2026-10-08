"""
Adapter tussen de Leboncoin-parser en de AI Huizencoach.

Dit bestand bevat geen Gmail-, Playwright-, OpenAI- of e-maillogica.
Het zet uitsluitend een gecombineerd Leboncoin-woningrecord om naar
het generieke woningformaat dat door ai_analyse.py wordt verwacht.
"""


def maak_huizencoach_woning(leboncoin_record):
    """
    Zet een gecombineerd Leboncoin-record om naar het generieke
    woningformaat voor de AI Huizencoach.

    Onbekende waarden blijven None.
    False blijft False en betekent dus expliciet afwezig.
    """

    if not leboncoin_record:
        raise ValueError("Leboncoin-record ontbreekt.")

    plaats = leboncoin_record.get("plaats")
    postcode = leboncoin_record.get("postcode")

    # ---------------------------------------------------------
    # Plaats samenstellen
    # ---------------------------------------------------------
    if postcode and plaats:
        volledige_plaats = f"{postcode} {plaats}"
    elif plaats:
        volledige_plaats = str(plaats)
    elif postcode:
        volledige_plaats = str(postcode)
    else:
        volledige_plaats = ""

    # ---------------------------------------------------------
    # Foto's
    # ---------------------------------------------------------
    fotos = []

    bron_fotos = leboncoin_record.get(
        "fotos"
    )

    if isinstance(bron_fotos, list):
        fotos = [
            foto
            for foto in bron_fotos
            if foto
        ]

    # Fallback voor oudere records.
    if not fotos:
        foto_url = leboncoin_record.get(
            "foto_url"
        )

        if foto_url:
            fotos.append(
                foto_url
            )
    # ---------------------------------------------------------
    # Gestructureerde kenmerken
    # ---------------------------------------------------------
    kenmerken = {
        "woonoppervlakte": leboncoin_record.get(
            "woonoppervlakte"
        ),
        "perceeloppervlakte": leboncoin_record.get(
            "perceeloppervlakte"
        ),
        "slaapkamers": leboncoin_record.get(
            "slaapkamers"
        ),
        "badkamers": leboncoin_record.get(
            "badkamers"
        ),
        "bouwjaar": leboncoin_record.get(
            "bouwjaar"
        ),
        "staat": leboncoin_record.get(
            "staat"
        ),
        "epc": leboncoin_record.get(
            "dpe"
        ),
        "energieverbruik": leboncoin_record.get(
            "energieverbruik"
        ),
        "verwarming": leboncoin_record.get(
            "verwarming"
        ),
        "dubbel_glas": leboncoin_record.get(
            "dubbel_glas"
        ),
        "garage": leboncoin_record.get(
            "garage"
        ),
        "schuur": leboncoin_record.get(
            "schuur"
        ),
        "tuin": leboncoin_record.get(
            "tuin"
        ),
        "terras": leboncoin_record.get(
            "terras"
        ),
        "parkeerplaatsen": leboncoin_record.get(
            "parkeerplaatsen"
        ),
        "riolering": leboncoin_record.get(
            "riolering"
        ),
        "winkels_in_buurt": leboncoin_record.get(
            "winkels_in_buurt"
        ),
        "vrijstaand": leboncoin_record.get(
            "vrijstaand"
        ),
    }

    # ---------------------------------------------------------
    # Beschrijving
    # ---------------------------------------------------------
    beschrijving = (
        leboncoin_record.get("beschrijving")
        or leboncoin_record.get("body")
        or ""
    )

    # ---------------------------------------------------------
    # Kenmerken als leesbare tekst
    #
    # Als de Leboncoin-parser later een volledige kenmerken_tekst
    # levert, gebruiken we die rechtstreeks.
    # ---------------------------------------------------------
    kenmerken_tekst = leboncoin_record.get(
        "kenmerken_tekst",
        "",
    )
    # ---------------------------------------------------------
    # Generiek Huizencoach-record
    # ---------------------------------------------------------

    titel = (
        leboncoin_record.get("titel")
        or "Leboncoin woning"
    )

    woning = {
        "advertentie_id": leboncoin_record.get(
            "advertentie_id"
        ),
        "titel": titel,
        "prijs": leboncoin_record.get(
            "prijs"
        ),
        "plaats": volledige_plaats,
        "beschrijving": beschrijving,
        "kenmerken_tekst": kenmerken_tekst,
        "kenmerken": kenmerken,
        "fotos": fotos,
        "bron": "Leboncoin",
        "link": (
            leboncoin_record.get("alert_url")
            or leboncoin_record.get("url")
            or ""
        ),
    }

    return woning
   

def toon_huizencoach_woning(woning):
    """
    Print het geconverteerde Huizencoach-record overzichtelijk.
    Alleen bedoeld voor testen/debugging.
    """

    print()
    print("=" * 72)
    print("LEBONCOIN → AI HUIZENCOACH")
    print("=" * 72)

    print(f"advertentie_id : {woning.get('advertentie_id')}")
    print(f"titel          : {woning.get('titel')}")
    print(f"prijs          : {woning.get('prijs')}")
    print(f"plaats         : {woning.get('plaats')}")
    print(f"bron           : {woning.get('bron')}")
    print(f"link           : {woning.get('link')}")

    print()
    print("KENMERKEN")
    print("-" * 72)

    for naam, waarde in woning.get(
        "kenmerken",
        {},
    ).items():
        print(
            f"{naam:22}: {waarde}"
        )

    print()
    print("BESCHRIJVING")
    print("-" * 72)

    beschrijving = woning.get(
        "beschrijving",
        "",
    )

    if beschrijving:
        print(beschrijving[:2000])
    else:
        print("Geen beschrijving beschikbaar.")

    print()
    print("FOTO'S")
    print("-" * 72)

    fotos = woning.get(
        "fotos",
        [],
    )

    print(f"Aantal foto's: {len(fotos)}")

    for foto in fotos[:5]:
        print(f"- {foto}")

    print("=" * 72)

def voeg_ai_analyse_toe(woning, analyse):
    """
    Voegt het resultaat van analyseer_woning() toe aan het
    generieke woningrecord in het formaat dat emailer.py verwacht.

    De oorspronkelijke woningdata blijven ongewijzigd.
    """

    if not woning:
        raise ValueError("Woningrecord ontbreekt.")

    if not analyse:
        raise ValueError("AI-analyse ontbreekt.")

    resultaat = dict(woning)

    resultaat["ai_score"] = analyse.get(
        "score"
    )

    resultaat["ai_advies"] = analyse.get(
        "advies",
        ""
    )

    resultaat["ai_betrouwbaarheid"] = analyse.get(
        "betrouwbaarheid",
        ""
    )

    resultaat["ai_samenvatting"] = analyse.get(
        "samenvatting",
        ""
    )

    resultaat["ai_sterke_punten"] = analyse.get(
        "sterke_punten",
        []
    )

    resultaat["ai_aandachtspunten"] = analyse.get(
        "aandachtspunten",
        []
    )

    resultaat["ai_ontbrekende_informatie"] = analyse.get(
        "ontbrekende_informatie",
        []
    )

    return resultaat
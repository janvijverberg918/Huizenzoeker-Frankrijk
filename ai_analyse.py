import json

from openai import OpenAI

from config import AI_LEEFSTIJLPROFIEL
from logger import logger
from advertentie_analyse import haal_immoweb_advertentie_op


client = OpenAI()


def maak_prompt(woning):
    """
    Maakt een duidelijke beoordelingsprompt voor één woning.
    """

    kenmerken = woning.get(
        "kenmerken",
        {},
    )

    fotos = woning.get(
        "fotos",
        [],
    )

    woningdata = {
        "titel": woning.get(
            "titel",
            "",
        ),
        "prijs": woning.get(
            "prijs",
            "",
        ),
        "plaats": woning.get(
            "plaats",
            "",
        ),
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
        "bouwjaar": kenmerken.get(
            "bouwjaar"
        ),
        "staat": kenmerken.get(
            "staat",
            "",
        ),
        "epc": kenmerken.get(
            "epc",
            "",
        ),
        "energieverbruik": kenmerken.get(
            "energieverbruik"
        ),
        "verwarming": kenmerken.get(
            "verwarming",
            "",
        ),
        "dubbel_glas": kenmerken.get(
            "dubbel_glas"
        ),
                "garage": kenmerken.get(
            "garage"
        ),
        "schuur": kenmerken.get(
            "schuur"
        ),
        "tuin": kenmerken.get(
            "tuin"
        ),
        "terras": kenmerken.get(
            "terras"
        ),
        "parkeerplaatsen": kenmerken.get(
            "parkeerplaatsen"
        ),
        "riolering": kenmerken.get(
            "riolering"
        ),
        "winkels_in_buurt": kenmerken.get(
            "winkels_in_buurt"
        ),
                "prijs_type": woning.get(
            "prijs_type",
            "",
        ),
        "verkooptype": woning.get(
            "verkooptype",
            "",
        ),
                "vrijstaand": kenmerken.get(
            "vrijstaand"
        ),

        "hoofdfoto": (
            fotos[0]
            if fotos
            else ""
        ),
        "beschrijving": woning.get(
            "beschrijving",
            "",
        ),
        "advertentiekenmerken": woning.get(
            "kenmerken_tekst",
            "",
        ),
        "bron": woning.get(
            "bron",
            "",
        ),
        "link": woning.get(
            "link",
            "",
        ),
    }

    return f"""
Je bent de AI Huizencoach.

Beoordeel onderstaande woning uitsluitend op basis van
het leefstijlprofiel en de beschikbare woninggegevens.

BELANGRIJKE REGELS:
- Verzin niets.
- Als informatie ontbreekt, zeg expliciet dat deze onbekend is.
- Trek geen negatieve of positieve conclusie uit ontbrekende informatie.
- "Niet vermeld" betekent "onbekend", niet "waarschijnlijk afwezig".
- Geef geen punten voor eigenschappen die niet uit de gegevens blijken.
- Trek geen punten af voor eigenschappen die niet uit de gegevens blijken.
- Zet onbekende leefstijlkenmerken onder ontbrekende_informatie.
- Gebruik woorden als "waarschijnlijk", "vermoedelijk" of "impliceert"
  alleen als daar concrete informatie in de advertentie voor staat.
- Ligging nabij een centrum of weg mag niet automatisch worden beoordeeld
  als gebrek aan rust, privacy of vrije ligging.
- Een woning boven het richtbudget mag toch interessant zijn.
- Als de advertentie expliciet aangeeft dat de woning te renoveren is,
  is dit een zwaar negatief punt.
- Privacy, ligging en schuur/garage zijn belangrijker dan luxe of
  grote woonoppervlakte.
- Maak duidelijk onderscheid tussen:
  1. feiten uit de advertentie;
  2. onbekende informatie;
  3. daadwerkelijke negatieve eigenschappen.
- Baseer de score uitsluitend op bekende eigenschappen.
- Ontbrekende informatie mag de betrouwbaarheid verlagen,
  maar mag niet automatisch de score verlagen.
- Baseer de score uitsluitend op bekende eigenschappen.
- Ontbrekende informatie mag de betrouwbaarheid verlagen,
  maar mag niet automatisch de score verlagen.
- Noem geen mogelijk nadeel als daarvoor geen expliciet bewijs
  in de advertentie staat.
- Gebruik "vrij gelegen", "weinig inkijk", "rustige weg" of
  vergelijkbare liggingseigenschappen alleen als die expliciet
  in de advertentie staan.
- Het ontbreken van aanwijzingen voor een nadeel geldt niet
  als bewijs van een voordeel.
- Gebruik het Belgische vastgoedbegrip "4 gevels" niet letterlijk in de beoordeling.
- Als expliciet staat dat een woning 4 gevels heeft, mag dit worden vertaald naar "vrijstaande woning".
- Noem het aantal gevels zelf niet als sterk punt; beoordeel alleen de relevante eigenschap, bijvoorbeeld vrijstaand.
- Een waarde None, null, een lege string of ontbrekend veld betekent ONBEKEND.
- Alleen de booleaanse waarde false betekent expliciet dat een eigenschap niet aanwezig is.
- Concludeer nooit dat garage, schuur, tuin of een andere voorziening ontbreekt wanneer de waarde onbekend is.
- Trek geen conclusie over beschikbare bouwruimte uit alleen de perceeloppervlakte; beoordeel ruimte voor een schuur als onbekend tenzij dit expliciet uit de advertentie blijkt.
- Maak geen eigen woonvoorkeuren; beoordeel alleen criteria
  die expliciet in het leefstijlprofiel staan.
- Een prijs in een verkoopadvertentie is de vraagprijs, niet de verkoopprijs.
- Schrijf nooit dat een woning "verkocht is voor" een bedrag, tenzij expliciet staat dat de verkoop al heeft plaatsgevonden.
- Gebruik bij een actieve verkoopadvertentie formuleringen als "vraagprijs", "te koop voor" of "aangeboden voor".
- Informatie zoals aantal badkamers, slaapkamers of woonoppervlakte
  mag alleen als aandachtspunt worden genoemd als dit strijdig is met een expliciete wens uit het leefstijlprofiel.
- Bij Biddit moet prijs altijd samen met prijs_type en verkooptype worden geïnterpreteerd.
- "Gewenste prijs" bij verkoop uit de hand is een vraagprijs/indicatieve verkoopprijs, geen gerealiseerde verkoopprijs.
- Bij openbare verkoop mag een startprijs, openingsbod of huidig bod nooit als gewone vraagprijs worden beschreven.
- Zet ontbrekende informatie nooit onder aandachtspunten; ontbrekende gegevens horen uitsluitend onder ontbrekende_informatie.
- Formuleer het ontbreken van een negatief kenmerk nooit als aandachtspunt. Als een woning bijvoorbeeld als "Goed" staat vermeld en er geen grote renovatie wordt genoemd, is dat geen negatief punt.

LEEFSTIJLPROFIEL:
{json.dumps(
    AI_LEEFSTIJLPROFIEL,
    ensure_ascii=False,
    indent=2,
)}

WONING:
{json.dumps(
    woningdata,
    ensure_ascii=False,
    indent=2,
)}

Geef een nuchtere eerste beoordeling.
"""


def analyseer_woning(woning):
    """
    Laat OpenAI één woning beoordelen.

    Retourneert een dictionary met:
    - score
    - advies
    - samenvatting
    - sterke_punten
    - aandachtspunten
    - ontbrekende_informatie
    - betrouwbaarheid
    """

    logger.info(
        "AI-analyse gestart voor woning: %s",
        woning.get(
            "titel",
            "Onbekend",
        ),
    )

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=maak_prompt(
                woning
            ),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "woning_beoordeling",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "score": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 10,
                            },
                            "advies": {
                                "type": "string",
                                "enum": [
                                    "Direct bekijken",
                                    "Zeer interessant",
                                    "Misschien interessant",
                                    "Lage prioriteit",
                                ],
                            },
                            "samenvatting": {
                                "type": "string",
                            },
                            "sterke_punten": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                },
                            },
                            "aandachtspunten": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                },
                            },
                            "ontbrekende_informatie": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                },
                            },
                            "betrouwbaarheid": {
                                "type": "string",
                                "enum": [
                                    "Laag",
                                    "Middel",
                                    "Hoog",
                                ],
                            },
                        },
                        "required": [
                            "score",
                            "advies",
                            "samenvatting",
                            "sterke_punten",
                            "aandachtspunten",
                            "ontbrekende_informatie",
                            "betrouwbaarheid",
                        ],
                        "additionalProperties": False,
                    },
                }
            },
        )

        resultaat = json.loads(
            response.output_text
        )

        logger.info(
            "AI-analyse afgerond: score=%s, advies=%s",
            resultaat.get(
                "score"
            ),
            resultaat.get(
                "advies"
            ),
        )

        return resultaat

    except Exception:
        logger.exception(
            "AI-analyse van woning is mislukt"
        )
        raise


def toon_analyse(analyse):
    """
    Print een AI-analyse overzichtelijk in de terminal.
    """

    print()
    print("=" * 60)
    print("AI HUIZENCOACH")
    print("=" * 60)

    print(
        f"Score           : "
        f"{analyse['score']} / 10"
    )

    print(
        f"Advies          : "
        f"{analyse['advies']}"
    )

    print(
        f"Betrouwbaarheid : "
        f"{analyse['betrouwbaarheid']}"
    )

    print()
    print("Samenvatting")
    print("-" * 60)
    print(
        analyse["samenvatting"]
    )

    print()
    print("Sterke punten")
    print("-" * 60)

    if analyse["sterke_punten"]:
        for punt in analyse[
            "sterke_punten"
        ]:
            print(
                f"+ {punt}"
            )
    else:
        print(
            "Geen duidelijke sterke punten "
            "op basis van de beschikbare informatie."
        )

    print()
    print("Aandachtspunten")
    print("-" * 60)

    if analyse["aandachtspunten"]:
        for punt in analyse[
            "aandachtspunten"
        ]:
            print(
                f"- {punt}"
            )
    else:
        print(
            "Geen duidelijke aandachtspunten."
        )

    print()
    print("Ontbrekende informatie")
    print("-" * 60)

    if analyse[
        "ontbrekende_informatie"
    ]:
        for punt in analyse[
            "ontbrekende_informatie"
        ]:
            print(
                f"? {punt}"
            )
    else:
        print(
            "Geen belangrijke informatie ontbreekt."
        )

    print("=" * 60)


if __name__ == "__main__":
    print()
    print("AI Huizencoach - echte Immoweb-advertentie")
    print()

    test_url = input(
        "Plak een Immoweb advertentielink: "
    ).strip()

    print()
    print("Advertentie wordt uitgelezen...")

    advertentie = haal_immoweb_advertentie_op(
        test_url
    )

    print(
        f"Gevonden: "
        f"{advertentie.get('titel', 'Onbekend')}"
    )

    print(
        f"Prijs: "
        f"{advertentie.get('prijs', 'Onbekend')}"
    )

    print(
        f"Plaats: "
        f"{advertentie.get('plaats', 'Onbekend')}"
    )

    print()
    print("AI Huizencoach analyseert de woning...")
    print()

    analyse = analyseer_woning(
        advertentie
    )

    toon_analyse(
        analyse
    )
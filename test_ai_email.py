from advertentie_analyse import haal_immoweb_advertentie_op
from ai_analyse import analyseer_woning
from emailer import stuur_nieuwe_woningen


TEST_URL = (
    "https://www.immoweb.be/nl/zoekertje/"
    "bel-etage/te-koop/saint-hubert/6870/21747439"
)


print()
print("=" * 60)
print("TEST AI HUIZENCOACH + E-MAIL")
print("=" * 60)

print()
print("1. Immoweb-advertentie uitlezen...")

woning = haal_immoweb_advertentie_op(
    TEST_URL
)

print(
    f"Gevonden: "
    f"{woning.get('titel', 'Onbekend')}"
)

print()
print("2. AI Huizencoach analyseert de woning...")

analyse = analyseer_woning(
    woning
)

woning["ai_score"] = analyse.get(
    "score"
)

woning["ai_advies"] = analyse.get(
    "advies",
    "",
)

woning["ai_samenvatting"] = analyse.get(
    "samenvatting",
    "",
)

woning["ai_sterke_punten"] = analyse.get(
    "sterke_punten",
    [],
)

woning["ai_aandachtspunten"] = analyse.get(
    "aandachtspunten",
    [],
)

woning["ai_ontbrekende_informatie"] = analyse.get(
    "ontbrekende_informatie",
    [],
)

woning["ai_betrouwbaarheid"] = analyse.get(
    "betrouwbaarheid",
    "",
)

# Hoofdfoto voor emailer.py
fotos = woning.get(
    "fotos",
    [],
)

if fotos:
    woning["hoofdfoto"] = fotos[0]

# Nodig voor groepering in de e-mail
woning["zoekprofiel"] = "Test AI Huizencoach"

print(
    f"Score : "
    f"{woning.get('ai_score')} / 10"
)

print(
    f"Advies: "
    f"{woning.get('ai_advies')}"
)

print()
print("3. Test-e-mail versturen...")

stuur_nieuwe_woningen(
    [woning]
)

print()
print("=" * 60)
print("TEST AFGEROND")
print("=" * 60)
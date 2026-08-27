from advertentie_analyse_ardenneimmo import (
    haal_ardenneimmo_advertentie_op,
)
from ai_analyse import analyseer_woning
from emailer import stuur_nieuwe_woningen


TEST_URL = (
    "https://www.ardenneimmo.be/nl/e/"
    "huis-te-koop-Berismenil-7650597"
)


print()
print("=" * 60)
print("TEST AI HUIZENCOACH + E-MAIL - ARDENNE IMMO")
print("=" * 60)

print()
print("1. Ardenne Immo-advertentie uitlezen...")

woning = haal_ardenneimmo_advertentie_op(
    TEST_URL
)

print(
    f"Gevonden: "
    f"{woning.get('titel', 'Onbekend')}"
)

print(
    f"Prijs: "
    f"{woning.get('prijs', 'Onbekend')}"
)

print(
    f"Plaats: "
    f"{woning.get('plaats', 'Onbekend')}"
)

print()
print("2. AI Huizencoach analyseert de woning...")

analyse = analyseer_woning(
    woning
)

# ---------------------------------------------------------
# AI-resultaten aan woning toevoegen
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# Hoofdfoto voor de e-mail
# ---------------------------------------------------------
fotos = woning.get(
    "fotos",
    [],
)

if fotos:
    woning["hoofdfoto"] = fotos[0]

# ---------------------------------------------------------
# Nodig voor groepering in emailer.py
# ---------------------------------------------------------
woning["zoekprofiel"] = (
    "Test AI Huizencoach - Ardenne Immo"
)

print()
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
from advertentie_analyse_biddit import (
    haal_biddit_advertentie_op,
)
from ai_analyse import analyseer_woning
from emailer import stuur_nieuwe_woningen


TEST_URL = (
    "https://www.biddit.be/nl/catalog/detail/298672"
)


print()
print("=" * 60)
print("TEST AI HUIZENCOACH + E-MAIL - BIDDIT")
print("=" * 60)

print()
print("1. Biddit-advertentie uitlezen...")

woning = haal_biddit_advertentie_op(
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
    f"Prijstype: "
    f"{woning.get('prijs_type', 'Onbekend')}"
)

print(
    f"Verkooptype: "
    f"{woning.get('verkooptype', 'Onbekend')}"
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
# AI-resultaten toevoegen
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
# Hoofdfoto
# ---------------------------------------------------------

fotos = woning.get(
    "fotos",
    [],
)

if fotos:
    woning["hoofdfoto"] = fotos[0]

# ---------------------------------------------------------
# Zoekprofiel voor emailer
# ---------------------------------------------------------

woning["zoekprofiel"] = (
    "Test AI Huizencoach - Biddit"
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
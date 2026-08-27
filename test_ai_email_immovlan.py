from advertentie_analyse_immovlan import (
    haal_immovlan_advertentie_op,
)
from ai_analyse import analyseer_woning
from emailer import stuur_nieuwe_woningen


TEST_URL = (
    "https://immovlan.be/nl/detail/huis/te-koop/6980/la-roche-en-ardenne/vbd97682"
)


print()
print("=" * 60)
print("TEST AI HUIZENCOACH + E-MAIL - IMMOVLAN")
print("=" * 60)

print()
print("1. Immovlan-advertentie uitlezen...")

woning = haal_immovlan_advertentie_op(
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

# Detailkenmerken ook op woningniveau zetten
kenmerken = woning.get(
    "kenmerken",
    {},
)

if kenmerken:
    woning["kenmerken"] = kenmerken

# Voor groepering in de e-mail
woning["zoekprofiel"] = (
    "Test AI Huizencoach - Immovlan"
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
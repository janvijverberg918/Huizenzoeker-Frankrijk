from advertentie_analyse_ardenneimmo import (
    haal_ardenneimmo_advertentie_op,
)
from ai_analyse import (
    analyseer_woning,
    toon_analyse,
)


TEST_URL = (
    "https://www.ardenneimmo.be/nl/e/"
    "huis-te-koop-Berismenil-7650597"
)


print()
print("=" * 60)
print("TEST AI HUIZENCOACH - ARDENNE IMMO")
print("=" * 60)

print()
print("Advertentie wordt uitgelezen...")

woning = haal_ardenneimmo_advertentie_op(
    TEST_URL
)

print(
    f"Gevonden: {woning.get('titel', 'Onbekend')}"
)

print(
    f"Prijs: {woning.get('prijs', 'Onbekend')}"
)

print(
    f"Plaats: {woning.get('plaats', 'Onbekend')}"
)

print()
print("AI Huizencoach analyseert de woning...")
print()

analyse = analyseer_woning(
    woning
)

toon_analyse(
    analyse
)
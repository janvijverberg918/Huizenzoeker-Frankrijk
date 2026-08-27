from advertentie_analyse_immovlan import (
    haal_immovlan_advertentie_op,
)
from ai_analyse import (
    analyseer_woning,
    toon_analyse,
)


TEST_URL = (
    "https://immovlan.be/nl/detail/huis/te-koop/6690/vielsalm/vbe48464"
)


print()
print("=" * 60)
print("TEST AI HUIZENCOACH - IMMOVLAN")
print("=" * 60)

print()
print("Advertentie wordt uitgelezen...")

woning = haal_immovlan_advertentie_op(
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
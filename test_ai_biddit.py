from advertentie_analyse_biddit import (
    haal_biddit_advertentie_op,
)
from ai_analyse import (
    analyseer_woning,
    toon_analyse,
)


TEST_URL = (
    "https://www.biddit.be/nl/catalog/detail/298672"
)


print()
print("=" * 60)
print("TEST AI HUIZENCOACH - BIDDIT")
print("=" * 60)

print()
print("Advertentie wordt uitgelezen...")

woning = haal_biddit_advertentie_op(
    TEST_URL
)

print(
    f"Gevonden: {woning.get('titel', 'Onbekend')}"
)

print(
    f"Prijs: {woning.get('prijs', 'Onbekend')}"
)

print(
    f"Prijstype: {woning.get('prijs_type', 'Onbekend')}"
)

print(
    f"Verkooptype: {woning.get('verkooptype', 'Onbekend')}"
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
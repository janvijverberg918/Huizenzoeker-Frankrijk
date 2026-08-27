from deduplicatie import (
    voeg_dubbele_woningen_samen,
    zijn_dezelfde_woning,
)


woningen = [
    {
        "titel": "Huis te koop",
        "prijs": "€ 225.000",
        "slaapkamers": "3",
        "oppervlakte": "141",
        "plaats": "6980 LA ROCHE-EN-ARDENNE",
        "link": "https://www.immoweb.be/woning-1",
        "bron": "Immoweb",
        "zoekprofiel": "La Roche",
    },
    {
        "titel": "Huis te koop",
        "prijs": "229 000 €",
        "slaapkamers": "3",
        "oppervlakte": "143",
        "plaats": "6980 La Roche-en-Ardenne",
        "link": "https://immovlan.be/woning-1",
        "bron": "Immovlan",
        "zoekprofiel": "La Roche",
    },
    {
        "titel": "Fermette te koop",
        "prijs": "179 000 €",
        "slaapkamers": "3",
        "oppervlakte": "217",
        "plaats": "6980 Beausaint",
        "link": "https://immovlan.be/woning-2",
        "bron": "Immovlan",
        "zoekprofiel": "La Roche",
    },
]


print("=" * 60)
print("TEST VAN DE VERGELIJKINGSLOGICA")
print("=" * 60)

woning_1 = woningen[0]
woning_2 = woningen[1]
woning_3 = woningen[2]

zelfde_1_en_2 = zijn_dezelfde_woning(
    woning_1,
    woning_2,
)

zelfde_1_en_3 = zijn_dezelfde_woning(
    woning_1,
    woning_3,
)

print(
    "Woning 1 versus woning 2:",
    zelfde_1_en_2,
)

print(
    "Verwachting               : True"
)

print()

print(
    "Woning 1 versus woning 3:",
    zelfde_1_en_3,
)

print(
    "Verwachting               : False"
)


print("\n" + "=" * 60)
print("VOOR SAMENVOEGEN")
print("=" * 60)

for woning in woningen:
    print(
        woning["bron"],
        "|",
        woning["prijs"],
        "|",
        woning["plaats"],
        "|",
        woning["slaapkamers"],
        "slaapkamers |",
        woning["oppervlakte"],
        "m²",
    )


samengevoegde_woningen = voeg_dubbele_woningen_samen(
    woningen
)


print("\n" + "=" * 60)
print("NA SAMENVOEGEN")
print("=" * 60)

for woning in samengevoegde_woningen:
    print()
    print("Titel        :", woning["titel"])
    print("Prijs        :", woning["prijs"])
    print("Plaats       :", woning["plaats"])
    print("Slaapkamers :", woning["slaapkamers"])
    print("Oppervlakte :", woning["oppervlakte"])
    print("Bronnen:")

    for bron in woning["bronnen"]:
        print(
            "  -",
            bron["bron"],
            ":",
            bron["link"],
        )


print("\n" + "=" * 60)
print("RESULTAAT")
print("=" * 60)

print(
    f"Advertenties voor samenvoegen : {len(woningen)}"
)

print(
    f"Unieke woningen na samenvoegen: "
    f"{len(samengevoegde_woningen)}"
)

print(
    f"Samengevoegde dubbelen        : "
    f"{len(woningen) - len(samengevoegde_woningen)}"
)


# ---------------------------------------------------------
# Automatische controles
# ---------------------------------------------------------

assert zelfde_1_en_2 is True, (
    "FOUT: woning 1 en 2 hadden als dezelfde woning "
    "herkend moeten worden."
)

assert zelfde_1_en_3 is False, (
    "FOUT: woning 1 en 3 mogen niet worden samengevoegd."
)

assert len(samengevoegde_woningen) == 2, (
    "FOUT: er moeten precies 2 unieke woningen overblijven."
)

eerste_woning = samengevoegde_woningen[0]

assert len(eerste_woning["bronnen"]) == 2, (
    "FOUT: de eerste woning moet twee bronnen bevatten."
)

bron_namen = {
    bron["bron"]
    for bron in eerste_woning["bronnen"]
}

assert "Immoweb" in bron_namen
assert "Immovlan" in bron_namen


print()
print("=" * 60)
print("TEST GESLAAGD")
print("=" * 60)

print(
    "€225.000 / 141 m² en €229.000 / 143 m² "
    "zijn correct samengevoegd."
)

print(
    "€179.000 / 217 m² is terecht apart gebleven."
)
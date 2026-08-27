from emailer import stuur_nieuwe_woningen


woning = {
    "titel": "Huis te koop",
    "prijs": "265 000 €",
    "slaapkamers": "2",
    "oppervlakte": "53",
    "perceeloppervlakte": "2500",
    "plaats": "LA ROCHE-EN-ARDENNE",
    "link": (
        "https://www.ardenneimmo.be/nl/e/"
        "huis-te-koop-la-Roche-en-Ardenne-7067864"
    ),
    "bron": "Ardenne Immo",
    "zoekprofiel": "La Roche-en-Ardenne",
}


stuur_nieuwe_woningen(
    [woning]
)
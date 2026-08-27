from dotenv import load_dotenv
import os


APP_NAME = "Huizenzoeker"
APP_VERSION = "3.2.1"

load_dotenv()


# ---------------------------------------------------------
# Testmodus
# ---------------------------------------------------------

TEST_MODUS = False
# Alleen gebruikt als TEST_MODUS = True
TEST_POSTCODES = [
    "6980"
]

# ---------------------------------------------------------
# Zoekgebieden Belgische Ardennen
# ---------------------------------------------------------

ZOEKGEBIEDEN = [
    {
        "naam": "Durbuy",
        "postcode": "6940",
        "slug": "durbuy",
    },
    {
        "naam": "La Roche-en-Ardenne",
        "postcode": "6980",
        "slug": "la_roche",
    },
    {
        "naam": "Houffalize",
        "postcode": "6660",
        "slug": "houffalize",
    },
    {
        "naam": "Érezée",
        "postcode": "6997",
        "slug": "erezee",
    },
    {
        "naam": "Manhay",
        "postcode": "6960",
        "slug": "manhay",
    },
    {
        "naam": "Rendeux",
        "postcode": "6987",
        "slug": "rendeux",
    },
    {
        "naam": "Vielsalm",
        "postcode": "6690",
        "slug": "vielsalm",
    },
    {
        "naam": "Gouvy",
        "postcode": "6670",
        "slug": "gouvy",
    },
    {
        "naam": "Bastogne",
        "postcode": "6600",
        "slug": "bastogne",
    },
    {
        "naam": "Sainte-Ode",
        "postcode": "6680",
        "slug": "sainte_ode",
    },
    {
        "naam": "Saint-Hubert",
        "postcode": "6870",
        "slug": "saint_hubert",
    },
    {
        "naam": "Libramont-Chevigny",
        "postcode": "6800",
        "slug": "libramont",
    },
    {
        "naam": "Nassogne",
        "postcode": "6950",
        "slug": "nassogne",
    },
    {
        "naam": "Marche-en-Famenne",
        "postcode": "6900",
        "slug": "marche_en_famenne",
    },
    {
        "naam": "Rochefort",
        "postcode": "5580",
        "slug": "rochefort",
    },
    {
        "naam": "Tellin",
        "postcode": "6927",
        "slug": "tellin",
    },
    {
        "naam": "Daverdisse",
        "postcode": "6929",
        "slug": "daverdisse",
    },
    {
        "naam": "Libin",
        "postcode": "6890",
        "slug": "libin",
    },
    {
        "naam": "Neufchâteau",
        "postcode": "6840",
        "slug": "neufchateau",
    },
    {
        "naam": "Vaux-sur-Sûre",
        "postcode": "6640",
        "slug": "vaux_sur_sure",
    },
    {
        "naam": "Léglise",
        "postcode": "6860",
        "slug": "leglise",
    },
    {
        "naam": "Fauvillers",
        "postcode": "6637",
        "slug": "fauvillers",
    },
    {
        "naam": "Martelange",
        "postcode": "6630",
        "slug": "martelange",
    },
    {
        "naam": "Bouillon",
        "postcode": "6830",
        "slug": "bouillon",
    },
    {
        "naam": "Bertrix",
        "postcode": "6880",
        "slug": "bertrix",
    },
    {
        "naam": "Paliseul",
        "postcode": "6850",
        "slug": "paliseul",
    },
    {
        "naam": "Herbeumont",
        "postcode": "6887",
        "slug": "herbeumont",
    },
    {
        "naam": "Bièvre",
        "postcode": "5555",
        "slug": "bievre",
    },
    {
        "naam": "Gedinne",
        "postcode": "5575",
        "slug": "gedinne",
    },
    {
        "naam": "Vresse-sur-Semois",
        "postcode": "5550",
        "slug": "vresse_sur_semois",
    },
    {
        "naam": "Spa",
        "postcode": "4900",
        "slug": "spa",
    },
]


# ---------------------------------------------------------
# Actieve zoekgebieden bepalen
# ---------------------------------------------------------

if TEST_MODUS:
    ACTIEVE_ZOEKGEBIEDEN = [
        gebied
        for gebied in ZOEKGEBIEDEN
        if gebied["postcode"] in TEST_POSTCODES
    ]
else:
    ACTIEVE_ZOEKGEBIEDEN = ZOEKGEBIEDEN


# ---------------------------------------------------------
# Zoekprofielen
# ---------------------------------------------------------

ZOEKPROFIELEN = [
    {
        "naam": "Belgische Ardennen",
        "woningtype": "huis",
        "min_prijs": 100000,
        "max_prijs": 250000,
        "websites": [
            "immoweb",
            "immovlan",
            "ardenneimmo",
            "biddit",
        ],
    },
]


# ---------------------------------------------------------
# Browser
# ---------------------------------------------------------

HEADLESS = False
SLOW_MO = 300


# ---------------------------------------------------------
# Wachttijden in milliseconden
# ---------------------------------------------------------

PAGE_TIMEOUT = 60000
COOKIE_TIMEOUT = 5000
LOCATIE_TIMEOUT = 20000
POSTCODE_WAIT = 1000
FORMULIER_WAIT = 500
RESULTATEN_WAIT = 2000


# ---------------------------------------------------------
# CSV
# ---------------------------------------------------------

CSV_BESTAND = "woningen.csv"


def maak_csv_bestandsnaam(gebied, website):
    """
    Maakt automatisch een CSV-bestandsnaam per
    zoekgebied en website.
    """

    return (
        f"woningen_{gebied['slug']}_{website}.csv"
    )


# ---------------------------------------------------------
# Email
# ---------------------------------------------------------

EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")
# ---------------------------------------------------------
# AI Huizencoach - leefstijlprofiel
# ---------------------------------------------------------

AI_LEEFSTIJLPROFIEL = {
    "richtbudget": 220000,

    "budget_regel": (
        "Tot ongeveer 220000 euro heeft de voorkeur. "
        "Een duurder pand mag toch hoog scoren als het "
        "uitzonderlijk goed bij het profiel past."
    ),

    "prioriteiten": {
        "vrije_ligging_privacy": 5,
        "bosrijke_omgeving": 5,
        "schuur_of_dubbele_garage": 5,
        "ruimte_voor_schuur_10x10": 5,

        "rustige_weg": 4,
        "perceel_minimaal_1000m2": 4,
        "geen_grote_renovatie": 4,

        "bakker_of_supermarkt_binnen_500m": 3,
        "budget_rond_220000": 3,

        "minimaal_2_slaapkamers": 2,
        "woonoppervlakte": 2,
    },

    "woonwensen": [
        "Vrij gelegen woning met zo weinig mogelijk inkijk van buren.",
        "Bij voorkeur bosrijke of natuurrijke omgeving.",
        "Niet aan een drukke of doorgaande weg.",
        "Perceel bij voorkeur minimaal 1000 m2.",
        "Grote schuur of dubbele garage heeft sterke voorkeur.",
        "Als er geen grote schuur of dubbele garage is, moet er "
        "voldoende ruimte zijn om ongeveer 100 m2 schuur te bouwen.",
        "Geschikt voor twee personen en er moet ruimte zijn voor gasten.",
        "Twee slaapkamers is voldoende; drie is mooi meegenomen.",
        "Kleine verbouwingen zijn prima.",
        "Geen woning waarvoor een grote of structurele renovatie nodig is.",
        "Bakker of kleine supermarkt bij voorkeur binnen circa "
        "500 meter bereikbaar.",
    ],

    "dealbreakers": [
        "Grote renovatie noodzakelijk.",
        "Veel directe inkijk van buren.",
        "Ligging direct aan een drukke of doorgaande weg.",
        "Geen bruikbare schuur of garage en ook geen realistische "
        "ruimte om een flinke schuur bij te bouwen.",
    ],

    "adviescategorieen": {
        "9-10": "Direct bekijken",
        "7-9": "Zeer interessant",
        "5-7": "Misschien interessant",
        "0-5": "Lage prioriteit",
    },

    "ai_regels": [
        "Nooit eigenschappen verzinnen.",
        "Als informatie ontbreekt, expliciet aangeven dat deze onbekend is.",
        "Een hoge score moet worden onderbouwd met concrete gegevens.",
        "Een woning boven het richtbudget niet automatisch afwijzen.",
        "Een grote renovatie zwaar negatief beoordelen.",
        "Privacy, omgeving en schuur/garage wegen zwaarder dan "
        "woonoppervlakte of luxe afwerking.",
    ],
}
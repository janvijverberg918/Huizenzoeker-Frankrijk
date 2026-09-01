from dotenv import load_dotenv
import os


# =========================================================
# Applicatie
# =========================================================

APP_NAME = "Huizenzoeker Frankrijk"
APP_VERSION = "1.0.0-dev"

load_dotenv()


# =========================================================
# Testmodus
# =========================================================

# Tijdens ontwikkeling ALTIJD eerst True gebruiken.
TEST_MODUS = True

# Alleen gebruikt als TEST_MODUS = True.
#
# 08600 is voorlopig onze eerste testpostcode.
TEST_POSTCODES = [
    "08600",
]


# =========================================================
# Zoekgebieden Frankrijk
# =========================================================
#
# Scope volgens functionele specificatie:
#
# - Département 08 - Ardennes
# - Département 02 - Aisne
# - Département 55 - Meuse
#
# De zoekstrategie blijft postcode-gedreven.
#
# Dubbele postcodes uit de functionele specificatie
# zijn slechts één keer opgenomen:
#
# - 08090
# - 08250
#
# Totaal: 48 unieke postcodes.
# =========================================================

ZOEKGEBIEDEN = [

    # -----------------------------------------------------
    # Département 08 - Ardennes
    # -----------------------------------------------------

    {
        "naam": "08600",
        "postcode": "08600",
        "slug": "08600",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08320",
        "postcode": "08320",
        "slug": "08320",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08170",
        "postcode": "08170",
        "slug": "08170",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08800",
        "postcode": "08800",
        "slug": "08800",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08500",
        "postcode": "08500",
        "slug": "08500",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08230",
        "postcode": "08230",
        "slug": "08230",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08380",
        "postcode": "08380",
        "slug": "08380",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08260",
        "postcode": "08260",
        "slug": "08260",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08250",
        "postcode": "08250",
        "slug": "08250",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08090",
        "postcode": "08090",
        "slug": "08090",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08000",
        "postcode": "08000",
        "slug": "08000",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08440",
        "postcode": "08440",
        "slug": "08440",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08330",
        "postcode": "08330",
        "slug": "08330",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08200",
        "postcode": "08200",
        "slug": "08200",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08140",
        "postcode": "08140",
        "slug": "08140",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08110",
        "postcode": "08110",
        "slug": "08110",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08370",
        "postcode": "08370",
        "slug": "08370",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08210",
        "postcode": "08210",
        "slug": "08210",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08450",
        "postcode": "08450",
        "slug": "08450",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08160",
        "postcode": "08160",
        "slug": "08160",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08410",
        "postcode": "08410",
        "slug": "08410",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08430",
        "postcode": "08430",
        "slug": "08430",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08460",
        "postcode": "08460",
        "slug": "08460",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08290",
        "postcode": "08290",
        "slug": "08290",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08220",
        "postcode": "08220",
        "slug": "08220",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08270",
        "postcode": "08270",
        "slug": "08270",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08130",
        "postcode": "08130",
        "slug": "08130",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08390",
        "postcode": "08390",
        "slug": "08390",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08240",
        "postcode": "08240",
        "slug": "08240",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08400",
        "postcode": "08400",
        "slug": "08400",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08310",
        "postcode": "08310",
        "slug": "08310",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08190",
        "postcode": "08190",
        "slug": "08190",
        "departement": "08-Ardennes",
    },
    {
        "naam": "08360",
        "postcode": "08360",
        "slug": "08360",
        "departement": "08-Ardennes",
    },


    # -----------------------------------------------------
    # Département 02 - Aisne
    # -----------------------------------------------------

    {
        "naam": "02830",
        "postcode": "02830",
        "slug": "02830",
        "departement": "02-Aisne",
    },
    {
        "naam": "02500",
        "postcode": "02500",
        "slug": "02500",
        "departement": "02-Aisne",
    },
    {
        "naam": "02550",
        "postcode": "02550",
        "slug": "02550",
        "departement": "02-Aisne",
    },
    {
        "naam": "02360",
        "postcode": "02360",
        "slug": "02360",
        "departement": "02-Aisne",
    },
    {
        "naam": "02140",
        "postcode": "02140",
        "slug": "02140",
        "departement": "02-Aisne",
    },
    {
        "naam": "02580",
        "postcode": "02580",
        "slug": "02580",
        "departement": "02-Aisne",
    },
    {
        "naam": "02260",
        "postcode": "02260",
        "slug": "02260",
        "departement": "02-Aisne",
    },
    {
        "naam": "02620",
        "postcode": "02620",
        "slug": "02620",
        "departement": "02-Aisne",
    },
    {
        "naam": "02170",
        "postcode": "02170",
        "slug": "02170",
        "departement": "02-Aisne",
    },
    {
        "naam": "02450",
        "postcode": "02450",
        "slug": "02450",
        "departement": "02-Aisne",
    },
    {
        "naam": "02510",
        "postcode": "02510",
        "slug": "02510",
        "departement": "02-Aisne",
    },
    {
        "naam": "02630",
        "postcode": "02630",
        "slug": "02630",
        "departement": "02-Aisne",
    },
    {
        "naam": "02120",
        "postcode": "02120",
        "slug": "02120",
        "departement": "02-Aisne",
    },


    # -----------------------------------------------------
    # Département 55 - Meuse
    # -----------------------------------------------------

    {
        "naam": "55700",
        "postcode": "55700",
        "slug": "55700",
        "departement": "55-Meuse",
    },
    {
        "naam": "55600",
        "postcode": "55600",
        "slug": "55600",
        "departement": "55-Meuse",
    },
]


# =========================================================
# Actieve zoekgebieden bepalen
# =========================================================

if TEST_MODUS:
    ACTIEVE_ZOEKGEBIEDEN = [
        gebied
        for gebied in ZOEKGEBIEDEN
        if gebied["postcode"] in TEST_POSTCODES
    ]
else:
    ACTIEVE_ZOEKGEBIEDEN = ZOEKGEBIEDEN


# =========================================================
# Zoekprofielen
# =========================================================
#
# Websites blijven bewust leeg.
#
# Pas nadat een Franse bron technisch is onderzocht en
# getest voegen we deze hier toe.
# =========================================================

ZOEKPROFIELEN = [
    {
        "naam": "Frankrijk",
        "woningtype": "huis",
        "min_prijs": 80000,
        "max_prijs": 220000,
        "websites": [
            "bienici",
        ]
    },
]


# =========================================================
# Browser
# =========================================================

HEADLESS = False
SLOW_MO = 300


# =========================================================
# Wachttijden in milliseconden
# =========================================================

PAGE_TIMEOUT = 60000
COOKIE_TIMEOUT = 5000
LOCATIE_TIMEOUT = 20000
POSTCODE_WAIT = 1000
FORMULIER_WAIT = 500
RESULTATEN_WAIT = 2000


# =========================================================
# CSV
# =========================================================

CSV_BESTAND = "woningen.csv"


def maak_csv_bestandsnaam(
    gebied,
    website,
):
    """
    Maakt automatisch een CSV-bestandsnaam
    per zoekgebied en website.

    Voorbeeld:

    woningen_08600_seloger.csv
    """

    return (
        f"woningen_"
        f"{gebied['slug']}_"
        f"{website}.csv"
    )


# =========================================================
# E-mail
# =========================================================

EMAIL_PROVIDER = os.getenv(
    "EMAIL_PROVIDER"
)

EMAIL_ADDRESS = os.getenv(
    "EMAIL_ADDRESS"
)

EMAIL_PASSWORD = os.getenv(
    "EMAIL_PASSWORD"
)

EMAIL_TO = os.getenv(
    "EMAIL_TO"
)


# =========================================================
# AI Huizencoach - leefstijlprofiel
# =========================================================
#
# Volgens de functionele specificatie blijft het
# leefstijlprofiel voor Frankrijk gelijk aan België.
# =========================================================

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
        (
            "Vrij gelegen woning met zo weinig mogelijk "
            "inkijk van buren."
        ),
        (
            "Bij voorkeur bosrijke of natuurrijke omgeving."
        ),
        (
            "Niet aan een drukke of doorgaande weg."
        ),
        (
            "Perceel bij voorkeur minimaal 1000 m2."
        ),
        (
            "Grote schuur of dubbele garage heeft "
            "sterke voorkeur."
        ),
        (
            "Als er geen grote schuur of dubbele garage is, "
            "moet er voldoende ruimte zijn om ongeveer "
            "100 m2 schuur te bouwen."
        ),
        (
            "Geschikt voor twee personen en er moet "
            "ruimte zijn voor gasten."
        ),
        (
            "Twee slaapkamers is voldoende; drie is "
            "mooi meegenomen."
        ),
        (
            "Kleine verbouwingen zijn prima."
        ),
        (
            "Geen woning waarvoor een grote of structurele "
            "renovatie nodig is."
        ),
        (
            "Bakker of kleine supermarkt bij voorkeur binnen "
            "circa 500 meter bereikbaar."
        ),
    ],

    "dealbreakers": [
        (
            "Grote renovatie noodzakelijk."
        ),
        (
            "Veel directe inkijk van buren."
        ),
        (
            "Ligging direct aan een drukke of doorgaande weg."
        ),
        (
            "Geen bruikbare schuur of garage en ook geen "
            "realistische ruimte om een flinke schuur "
            "bij te bouwen."
        ),
    ],

    "adviescategorieen": {
        "9-10": "Direct bekijken",
        "7-9": "Zeer interessant",
        "5-7": "Misschien interessant",
        "0-5": "Lage prioriteit",
    },

    "ai_regels": [
        (
            "Nooit eigenschappen verzinnen."
        ),
        (
            "Als informatie ontbreekt, expliciet aangeven "
            "dat deze onbekend is."
        ),
        (
            "Een hoge score moet worden onderbouwd met "
            "concrete gegevens."
        ),
        (
            "Een woning boven het richtbudget niet "
            "automatisch afwijzen."
        ),
        (
            "Een grote renovatie zwaar negatief beoordelen."
        ),
        (
            "Privacy, omgeving en schuur/garage wegen "
            "zwaarder dan woonoppervlakte of luxe afwerking."
        ),
    ],
}
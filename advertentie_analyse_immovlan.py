import re

from playwright.sync_api import sync_playwright

from config import (
    HEADLESS,
    PAGE_TIMEOUT,
    SLOW_MO,
)
from immovlan import accepteer_cookies
from logger import logger


def veilige_tekst(locator):
    """
    Geeft de tekst van een locator terug.
    Bij een fout wordt een lege string teruggegeven.
    """

    try:
        if locator.count() > 0:
            return locator.first.inner_text().strip()
    except Exception:
        pass

    return ""


def prijs_naar_getal(prijs_tekst):
    """
    Zet bijvoorbeeld '199 000 €' of '199.000 €'
    om naar 199000.
    """

    if not prijs_tekst:
        return None

    cijfers = re.findall(
        r"\d+",
        str(prijs_tekst),
    )

    if not cijfers:
        return None

    try:
        return int(
            "".join(cijfers)
        )
    except ValueError:
        return None


def ja_nee_naar_bool(waarde):
    """
    Zet Ja/Nee om naar True/False.
    """

    if not waarde:
        return None

    waarde = waarde.strip().lower()

    if waarde == "ja":
        return True

    if waarde == "nee":
        return False

    return None


def haal_waarde_na_label(
    regels,
    label,
):
    """
    Immovlan gebruikt vaak:

    Bouwjaar
    1899

    Deze functie zoekt het label en geeft
    de eerstvolgende niet-lege regel terug.
    """

    label_lower = label.lower()

    for i, regel in enumerate(regels):
        if regel.lower() == label_lower:
            if i + 1 < len(regels):
                return regels[i + 1].strip()

    return ""


def haal_gestructureerde_kenmerken(
    volledige_tekst,
):
    """
    Haalt de belangrijkste kenmerken uit
    één Immovlan-detailadvertentie.
    """

    regels = [
        regel.strip()
        for regel in volledige_tekst.splitlines()
        if regel.strip()
    ]

    gegevens = {
        "woonoppervlakte": None,
        "perceeloppervlakte": None,
        "slaapkamers": None,
        "badkamers": None,
        "bouwjaar": None,
        "staat": "",
        "epc": "",
        "energieverbruik": None,
        "verwarming": "",
        "dubbel_glas": None,

        # Extra kenmerken AI Huizencoach
        "garage": None,
        "schuur": None,
        "tuin": None,
        "terras": None,
        "riolering": None,
        "parkeerplaatsen": None,
    }

    # -----------------------------------------------------
    # Woonoppervlakte
    # -----------------------------------------------------
    waarde = haal_waarde_na_label(
        regels,
        "Bewoonbare oppervlakte",
    )

    match = re.search(
        r"(\d+)\s*m²",
        waarde,
        re.IGNORECASE,
    )

    if match:
        gegevens["woonoppervlakte"] = int(
            match.group(1)
        )

    # -----------------------------------------------------
    # Perceeloppervlakte
    # -----------------------------------------------------
    waarde = haal_waarde_na_label(
        regels,
        "Totale grondoppervlakte",
    )

    match = re.search(
        r"(\d+)\s*m²",
        waarde,
        re.IGNORECASE,
    )

    if match:
        gegevens["perceeloppervlakte"] = int(
            match.group(1)
        )

    # -----------------------------------------------------
    # Slaapkamers
    # -----------------------------------------------------
    waarde = haal_waarde_na_label(
        regels,
        "Aantal slaapkamers",
    )

    if waarde.isdigit():
        gegevens["slaapkamers"] = int(
            waarde
        )

    # -----------------------------------------------------
    # Badkamers
    # -----------------------------------------------------
    waarde = haal_waarde_na_label(
        regels,
        "Aantal badkamers",
    )

    if waarde.isdigit():
        gegevens["badkamers"] = int(
            waarde
        )

    # -----------------------------------------------------
    # Bouwjaar
    # -----------------------------------------------------
    waarde = haal_waarde_na_label(
        regels,
        "Bouwjaar",
    )

    if re.fullmatch(
        r"\d{4}",
        waarde,
    ):
        gegevens["bouwjaar"] = int(
            waarde
        )

    # -----------------------------------------------------
    # Staat
    # -----------------------------------------------------
    waarde = haal_waarde_na_label(
        regels,
        "Staat van het zoekertje",
    )

    if waarde:
        gegevens["staat"] = waarde

    # -----------------------------------------------------
    # Verwarming
    # -----------------------------------------------------
    waarde = haal_waarde_na_label(
        regels,
        "Type verwarming",
    )

    if waarde:
        gegevens["verwarming"] = waarde

    # -----------------------------------------------------
    # Dubbel glas
    # -----------------------------------------------------
    waarde = haal_waarde_na_label(
        regels,
        "Type glas",
    )

    if waarde:
        gegevens["dubbel_glas"] = (
            "dubbel" in waarde.lower()
        )

    # -----------------------------------------------------
    # Tuin
    # -----------------------------------------------------
    waarde = haal_waarde_na_label(
        regels,
        "Tuin",
    )

    gegevens["tuin"] = ja_nee_naar_bool(
        waarde
    )

    # -----------------------------------------------------
    # Terras
    # -----------------------------------------------------
    waarde = haal_waarde_na_label(
        regels,
        "Terras",
    )

    gegevens["terras"] = ja_nee_naar_bool(
        waarde
    )

    # -----------------------------------------------------
    # Riolering
    # -----------------------------------------------------
    waarde = haal_waarde_na_label(
        regels,
        "Aansluiting riolering",
    )

    gegevens["riolering"] = (
        ja_nee_naar_bool(
            waarde
        )
    )

    # -----------------------------------------------------
    # Parkeerplaatsen
    # -----------------------------------------------------
    waarde = haal_waarde_na_label(
        regels,
        "Aantal parkeerplaatsen (buiten)",
    )

    if waarde.isdigit():
        gegevens["parkeerplaatsen"] = int(
            waarde
        )

    # -----------------------------------------------------
    # Energieverbruik
    # -----------------------------------------------------
    waarde = haal_waarde_na_label(
        regels,
        "Specifiek primair energieverbruik",
    )

    match = re.search(
        r"(\d+)\s*kWh/m²",
        waarde,
        re.IGNORECASE,
    )

    if match:
        gegevens["energieverbruik"] = int(
            match.group(1)
        )

    # -----------------------------------------------------
    # EPC-label
    #
    # Soms staat dit alleen in de beschrijving,
    # bijvoorbeeld "PEB E".
    # -----------------------------------------------------
    match = re.search(
        r"\b(?:PEB|EPC)\s+([A-G])\b",
        volledige_tekst,
        re.IGNORECASE,
    )

    if match:
        gegevens["epc"] = (
            match.group(1).upper()
        )

    # -----------------------------------------------------
    # Garage / schuur
    #
    # Alleen als de advertentietekst dit expliciet noemt.
    # -----------------------------------------------------
    if re.search(
        r"\bgarage\b",
        volledige_tekst,
        re.IGNORECASE,
    ):
        gegevens["garage"] = True

    if re.search(
        r"\bschuur\b",
        volledige_tekst,
        re.IGNORECASE,
    ):
        gegevens["schuur"] = True

    return gegevens


def haal_immovlan_advertentie_op(url):
    """
    Leest één Immovlan-detailadvertentie uit.
    """

    logger.info(
        "Immovlan advertentie-analyse gestart: %s",
        url,
    )

    resultaat = {
        "titel": "",
        "prijs": None,
        "plaats": "",
        "beschrijving": "",
        "kenmerken_tekst": "",
        "kenmerken": {},
        "volledige_tekst": "",
        "fotos": [],
        "link": url,
        "bron": "Immovlan",
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS,
            slow_mo=0 if HEADLESS else SLOW_MO,
        )

        try:
            page = browser.new_page()

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=PAGE_TIMEOUT,
            )

            # Cookie-popup sluiten.
            accepteer_cookies(
                page
            )

            page.wait_for_timeout(
                2000
            )

            logger.info(
                "Immovlan detailpagina geopend: %s",
                page.url,
            )

            volledige_tekst = veilige_tekst(
                page.locator("body")
            )

            resultaat[
                "volledige_tekst"
            ] = volledige_tekst

            regels = [
                regel.strip()
                for regel in volledige_tekst.splitlines()
                if regel.strip()
            ]

            # -------------------------------------------------
            # Titel
            # -------------------------------------------------
            titel = veilige_tekst(
                page.locator("h1")
            )

            resultaat["titel"] = titel

            # -------------------------------------------------
            # Plaats
            #
            # Voorbeeld:
            # Route de Cierreux 28 6690 Vielsalm
            # -------------------------------------------------
            plaats_match = re.search(
                r"\b(\d{4})\s+"
                r"([A-Za-zÀ-ÖØ-öø-ÿ'’\- ]+)",
                volledige_tekst,
            )

            if plaats_match:
                postcode = (
                    plaats_match.group(1)
                    .strip()
                )

                plaatsnaam = (
                    plaats_match.group(2)
                    .strip()
                    .splitlines()[0]
                )

                resultaat["plaats"] = (
                    f"{postcode} {plaatsnaam}"
                )

            # -------------------------------------------------
            # Prijs
            #
            # De eerste duidelijke europrijs vóór
            # "Financiële details" gebruiken.
            # -------------------------------------------------
            bovenste_tekst = volledige_tekst

            if "Financiële details" in volledige_tekst:
                bovenste_tekst = (
                    volledige_tekst.split(
                        "Financiële details",
                        1,
                    )[0]
                )

            prijs_match = re.search(
                r"(\d[\d\s\u202f\.]*)\s*€",
                bovenste_tekst,
            )

            if prijs_match:
                resultaat["prijs"] = (
                    prijs_naar_getal(
                        prijs_match.group(0)
                    )
                )

            # -------------------------------------------------
            # Beschrijving
            # -------------------------------------------------
            beschrijving = ""

            try:
                start = regels.index(
                    "Beschrijving"
                )

                eind = None

                for i in range(
                    start + 1,
                    len(regels),
                ):
                    if regels[i] in (
                        "Toon alles",
                        "Financiële details",
                    ):
                        eind = i
                        break

                if eind is not None:
                    beschrijving = "\n".join(
                        regels[
                            start + 1:eind
                        ]
                    )

            except ValueError:
                beschrijving = ""

            resultaat[
                "beschrijving"
            ] = beschrijving

            # -------------------------------------------------
            # Kenmerken
            # -------------------------------------------------
            kenmerken_tekst = ""

            if "Extra informatie" in volledige_tekst:
                kenmerken_tekst = (
                    volledige_tekst.split(
                        "Extra informatie",
                        1,
                    )[1]
                )
            else:
                kenmerken_tekst = volledige_tekst

            resultaat[
                "kenmerken_tekst"
            ] = kenmerken_tekst

            resultaat[
                "kenmerken"
            ] = haal_gestructureerde_kenmerken(
                volledige_tekst
            )

            logger.info(
                "Immovlan advertentie uitgelezen: "
                "titel=%s, plaats=%s",
                resultaat["titel"],
                resultaat["plaats"],
            )

        finally:
            browser.close()

    return resultaat


def toon_advertentie(advertentie):
    """
    Print de Immovlan-detailanalyse overzichtelijk.
    """

    print()
    print("=" * 70)
    print("IMMOVLAN ADVERTENTIE")
    print("=" * 70)

    print(
        f"Titel : {advertentie['titel']}"
    )

    print(
        f"Prijs : {advertentie['prijs']}"
    )

    print(
        f"Plaats: {advertentie['plaats']}"
    )

    print()
    print("GESTRUCTUREERDE KENMERKEN")
    print("-" * 70)

    for naam, waarde in advertentie[
        "kenmerken"
    ].items():
        print(
            f"{naam:22}: {waarde}"
        )

    print()
    print("BESCHRIJVING")
    print("-" * 70)

    print(
        advertentie[
            "beschrijving"
        ][:5000]
    )


if __name__ == "__main__":
    print()
    print(
        "Immovlan advertentie-analyse"
    )
    print()

    test_url = input(
        "Plak een Immovlan advertentielink: "
    ).strip()

    advertentie = (
        haal_immovlan_advertentie_op(
            test_url
        )
    )

    toon_advertentie(
        advertentie
    )
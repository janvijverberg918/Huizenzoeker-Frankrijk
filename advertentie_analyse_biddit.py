import re

from playwright.sync_api import sync_playwright

from config import (
    HEADLESS,
    PAGE_TIMEOUT,
    SLOW_MO,
)
from logger import logger


BASE_URL = "https://www.biddit.be"


def veilige_tekst(locator):
    """
    Geeft tekst terug van een locator.
    Bij fouten wordt een lege string teruggegeven.
    """

    try:
        if locator.count() > 0:
            return locator.first.inner_text().strip()
    except Exception:
        pass

    return ""


def prijs_naar_getal(prijs_tekst):
    """
    Zet een prijs om naar integer.
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


def haal_waarde_na_label(
    regels,
    label,
):
    """
    Zoekt:

    Label
    Waarde

    en geeft de eerstvolgende regel terug.
    """

    label_lower = label.lower()

    for i, regel in enumerate(regels):
        if regel.lower() == label_lower:
            if i + 1 < len(regels):
                return regels[i + 1].strip()

    return ""


def haal_biddit_fotos(page):
    """
    Haalt echte woningfoto's van Biddit op.

    Logo's, energie-labels en footer-afbeeldingen
    worden genegeerd.
    """

    fotos = []

    afbeeldingen = page.locator("img")

    for i in range(
        afbeeldingen.count()
    ):
        afbeelding = afbeeldingen.nth(i)

        src = afbeelding.get_attribute(
            "src"
        )

        if not src:
            continue

        src = src.strip()

        if src.startswith("/"):
            src = BASE_URL + src

        # Echte Biddit vastgoedfoto's
        if "/stg/eco/images/" not in src:
            continue

        if src not in fotos:
            fotos.append(
                src
            )

    return fotos


def haal_epc_label(page):
    """
    Probeert EPC/PEB-label uit de afbeelding te halen.

    Voorbeeld:
    assets/energy-labels/peb/peb-e.png
    """

    afbeeldingen = page.locator(
        "img"
    )

    for i in range(
        afbeeldingen.count()
    ):
        src = afbeeldingen.nth(
            i
        ).get_attribute(
            "src"
        )

        if not src:
            continue

        match = re.search(
            r"peb-([a-g])\.",
            src,
            re.IGNORECASE,
        )

        if match:
            return (
                match.group(1).upper()
            )

    return ""


def haal_gestructureerde_kenmerken(
    volledige_tekst,
    page,
):
    """
    Haalt gestructureerde Biddit-kenmerken op.
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
        "garage": None,
        "schuur": None,
        "tuin": None,
        "terras": None,
        "riolering": None,
        "parkeerplaatsen": None,
        "vrijstaand": None,
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
        gegevens[
            "woonoppervlakte"
        ] = int(
            match.group(1)
        )

    # -----------------------------------------------------
    # Perceel
    # -----------------------------------------------------
    waarde = haal_waarde_na_label(
        regels,
        "Oppervlakte grond",
    )

    match = re.search(
        r"(\d+)\s*m²",
        waarde,
        re.IGNORECASE,
    )

    if match:
        gegevens[
            "perceeloppervlakte"
        ] = int(
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
        gegevens[
            "slaapkamers"
        ] = int(
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
        gegevens[
            "badkamers"
        ] = int(
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
        gegevens[
            "bouwjaar"
        ] = int(
            waarde
        )

    # -----------------------------------------------------
    # Staat
    # -----------------------------------------------------
    waarde = haal_waarde_na_label(
        regels,
        "Staat van het gebouw",
    )

    if waarde:
        gegevens[
            "staat"
        ] = waarde

    # -----------------------------------------------------
    # Verwarming
    # -----------------------------------------------------
    waarde = haal_waarde_na_label(
        regels,
        "Verwarmingstype",
    )

    if waarde:
        gegevens[
            "verwarming"
        ] = waarde

    # -----------------------------------------------------
    # Aantal gevels -> vrijstaand
    #
    # Alleen 4 gevels betekent vrijstaand.
    # 3 gevels is niet vrijstaand.
    # -----------------------------------------------------
    waarde = haal_waarde_na_label(
        regels,
        "Aantal gevels",
    )

    if waarde.isdigit():
        aantal_gevels = int(
            waarde
        )

        if aantal_gevels == 4:
            gegevens[
                "vrijstaand"
            ] = True

        elif aantal_gevels in (
            2,
            3,
        ):
            gegevens[
                "vrijstaand"
            ] = False

    # -----------------------------------------------------
    # EPC / PEB
    # -----------------------------------------------------
    gegevens[
        "epc"
    ] = haal_epc_label(
        page
    )

    # -----------------------------------------------------
    # Garage / schuur / tuin / terras
    #
    # Alleen positief zetten als expliciet genoemd.
    # -----------------------------------------------------
    if re.search(
        r"\bgarage\b",
        volledige_tekst,
        re.IGNORECASE,
    ):
        gegevens[
            "garage"
        ] = True

    if re.search(
        r"\bschuur\b",
        volledige_tekst,
        re.IGNORECASE,
    ):
        gegevens[
            "schuur"
        ] = True

    if re.search(
        r"\btuin\b",
        volledige_tekst,
        re.IGNORECASE,
    ):
        gegevens[
            "tuin"
        ] = True

    if re.search(
        r"\bterras\b",
        volledige_tekst,
        re.IGNORECASE,
    ):
        gegevens[
            "terras"
        ] = True

    return gegevens


def haal_biddit_advertentie_op(url):
    """
    Leest één Biddit-detailadvertentie uit.
    """

    logger.info(
        "Biddit advertentie-analyse gestart: %s",
        url,
    )

    resultaat = {
        "titel": "",
        "prijs": None,
        "prijs_type": "",
        "verkooptype": "",
        "plaats": "",
        "beschrijving": "",
        "kenmerken_tekst": "",
        "kenmerken": {},
        "volledige_tekst": "",
        "fotos": [],
        "link": url,
        "bron": "Biddit",
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

            page.wait_for_timeout(
                1500
            )

            # Cookies
            try:
                page.get_by_role(
                    "button",
                    name="Alle cookies aanvaarden",
                ).click(
                    timeout=5000
                )

                page.wait_for_timeout(
                    1000
                )

            except Exception:
                pass

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
            resultaat[
                "titel"
            ] = veilige_tekst(
                page.locator("h1")
            )

            # -------------------------------------------------
            # Plaats
            #
            # Voorbeeld:
            # 4910 Theux- Avenue Reine Elisabeth 22
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
                    .split("-")[0]
                    .strip()
                )

                resultaat[
                    "plaats"
                ] = (
                    f"{postcode} {plaatsnaam}"
                )

            # -------------------------------------------------
            # Verkooptype
            # -------------------------------------------------
            tekst_lower = (
                volledige_tekst.lower()
            )

            if "uit de hand" in tekst_lower:
                resultaat[
                    "verkooptype"
                ] = "Uit de hand"

            elif "openbare verkoop" in tekst_lower:
                resultaat[
                    "verkooptype"
                ] = "Openbare verkoop"

            # -------------------------------------------------
            # Prijs
            #
            # Uit de hand:
            # Gewenste prijs
            # € 210.000
            # -------------------------------------------------
            gewenste_prijs = (
                haal_waarde_na_label(
                    regels,
                    "Gewenste prijs",
                )
            )

            if gewenste_prijs:
                resultaat[
                    "prijs"
                ] = prijs_naar_getal(
                    gewenste_prijs
                )

                resultaat[
                    "prijs_type"
                ] = "Gewenste prijs"

            else:
                # -------------------------------------------------
                # Voor openbare verkoop zoeken we NIET automatisch
                # naar elke europrijs, omdat dit een startprijs,
                # huidig bod of andere waarde kan zijn.
                # -------------------------------------------------
                resultaat[
                    "prijs"
                ] = None

                resultaat[
                    "prijs_type"
                ] = "Onbekend"

            # -------------------------------------------------
            # Beschrijving
            # -------------------------------------------------
            beschrijving = ""

            try:
                start = regels.index(
                    "HuisCode: 298672"
                )
            except ValueError:
                start = None

            # Betere generieke methode:
            # tekst tussen de korte intro en "Kenmerken van het goed"
            if "Kenmerken van het goed" in regels:
                eind = regels.index(
                    "Kenmerken van het goed"
                )

                # zoek een bruikbaar begin in de regels
                for i in range(
                    max(0, eind - 20),
                    eind,
                ):
                    regel = regels[i]

                    if len(regel) > 40:
                        beschrijving = "\n".join(
                            regels[i:eind]
                        )
                        break

            resultaat[
                "beschrijving"
            ] = beschrijving

            # -------------------------------------------------
            # Kenmerken
            # -------------------------------------------------
            resultaat[
                "kenmerken_tekst"
            ] = volledige_tekst

            resultaat[
                "kenmerken"
            ] = haal_gestructureerde_kenmerken(
                volledige_tekst,
                page,
            )

            # -------------------------------------------------
            # Foto's
            #
            # Biddit toont op de detailpagina ook foto's van
            # aanbevolen andere panden. Daardoor kunnen we hier
            # niet betrouwbaar bepalen welke foto bij de huidige
            # advertentie hoort.
            #
            # De hoofdfoto uit de zoekresultaatkaart in biddit.py
            # is betrouwbaarder en wordt daarom behouden.
            # -------------------------------------------------
            resultaat["fotos"] = []

            logger.info(
                "Biddit advertentie uitgelezen: "
                "titel=%s, plaats=%s, verkooptype=%s, foto's=%s",
                resultaat["titel"],
                resultaat["plaats"],
                resultaat["verkooptype"],
                len(
                    resultaat["fotos"]
                ),
            )

        finally:
            browser.close()

    return resultaat


def toon_advertentie(advertentie):
    """
    Print Biddit-detailanalyse.
    """

    print()
    print("=" * 70)
    print("BIDDIT ADVERTENTIE")
    print("=" * 70)

    print(
        f"Titel      : {advertentie['titel']}"
    )

    print(
        f"Prijs      : {advertentie['prijs']}"
    )

    print(
        f"Prijstype  : {advertentie['prijs_type']}"
    )

    print(
        f"Verkooptype: {advertentie['verkooptype']}"
    )

    print(
        f"Plaats     : {advertentie['plaats']}"
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
    print(
        f"Aantal foto's: "
        f"{len(advertentie['fotos'])}"
    )

    for foto in advertentie[
        "fotos"
    ][:5]:
        print(
            f"- {foto}"
        )

    print()
    print("BESCHRIJVING")
    print("-" * 70)

    print(
        advertentie[
            "beschrijving"
        ][:4000]
    )


if __name__ == "__main__":
    print()
    print(
        "Biddit advertentie-analyse"
    )
    print()

    test_url = input(
        "Plak een Biddit advertentielink: "
    ).strip()

    advertentie = (
        haal_biddit_advertentie_op(
            test_url
        )
    )

    toon_advertentie(
        advertentie
    )
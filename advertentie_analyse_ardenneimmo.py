import re

from playwright.sync_api import sync_playwright

from config import (
    HEADLESS,
    PAGE_TIMEOUT,
    SLOW_MO,
)
from logger import logger


BASE_URL = "https://www.ardenneimmo.be"


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
    Zet een prijs om naar een integer.
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


def haal_fotos_op(page):
    """
    Probeert bruikbare woningfoto's van de detailpagina
    te verzamelen.
    """

    fotos = []

    try:
        afbeeldingen = page.locator("img")

        for i in range(
            afbeeldingen.count()
        ):
            afbeelding = afbeeldingen.nth(i)

            kandidaten = [
                afbeelding.get_attribute("src"),
                afbeelding.get_attribute("data-src"),
                afbeelding.get_attribute("data-lazy-src"),
            ]

            srcset = afbeelding.get_attribute(
                "srcset"
            )

            if srcset:
                onderdelen = [
                    deel.strip()
                    for deel in srcset.split(",")
                    if deel.strip()
                ]

                if onderdelen:
                    kandidaten.append(
                        onderdelen[-1]
                        .split()[0]
                        .strip()
                    )

            for foto in kandidaten:
                if not foto:
                    continue

                foto = foto.strip()

                if foto.startswith("//"):
                    foto = "https:" + foto

                elif foto.startswith("/"):
                    foto = BASE_URL + foto

                if not foto.startswith("http"):
                    continue

                # Kleine iconen/logo's zoveel mogelijk uitsluiten.
                foto_lower = foto.lower()

                if any(
                    woord in foto_lower
                    for woord in (
                        "logo",
                        "icon",
                        "favicon",
                        "avatar",
                    )
                ):
                    continue

                if foto not in fotos:
                    fotos.append(foto)

    except Exception:
        logger.exception(
            "Ardenne Immo foto's konden niet "
            "worden uitgelezen"
        )

    return fotos

def haal_gestructureerde_kenmerken(
    volledige_tekst,
):
    """
    Haalt de belangrijkste kenmerken uit een
    Ardenne Immo-detailadvertentie.

    Alleen informatie die daadwerkelijk uit de
    advertentie blijkt wordt ingevuld.
    """

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

        # Extra kenmerken voor de AI Huizencoach
        "garage": None,
        "schuur": None,
        "tuin": None,
        "riolering": None,
        "winkels_in_buurt": None,
    }

    # ---------------------------------------------------------
    # Woonoppervlakte
    #
    # Ardenne Immo gebruikt bijvoorbeeld:
    # oppervlakte     136 m²
    # ---------------------------------------------------------
    match = re.search(
        r"(?im)^oppervlakte\s+(\d+)\s*m²\s*$",
        volledige_tekst,
    )

    if match:
        gegevens[
            "woonoppervlakte"
        ] = int(
            match.group(1)
        )

    # ---------------------------------------------------------
    # Perceeloppervlakte
    # ---------------------------------------------------------
    match = re.search(
        r"(?im)^grond-oppervlakte\s+(\d+)\s*m²\s*$",
        volledige_tekst,
    )

    if match:
        gegevens[
            "perceeloppervlakte"
        ] = int(
            match.group(1)
        )

    # ---------------------------------------------------------
    # Slaapkamers
    # ---------------------------------------------------------
    patronen = [
        r"(?im)^(\d+)\s+kamers?\s*$",
        r"(\d+)\s+slaapkamers?\b",
        r"(\d+)\s*k\.",
    ]

    for patroon in patronen:
        match = re.search(
            patroon,
            volledige_tekst,
            re.IGNORECASE,
        )

        if match:
            gegevens[
                "slaapkamers"
            ] = int(
                match.group(1)
            )
            break

    # ---------------------------------------------------------
    # Badkamers
    # ---------------------------------------------------------
    match = re.search(
        r"(\d+)\s+badkamers?\b",
        volledige_tekst,
        re.IGNORECASE,
    )

    if match:
        gegevens[
            "badkamers"
        ] = int(
            match.group(1)
        )

    # ---------------------------------------------------------
    # Bouwjaar
    # ---------------------------------------------------------
    match = re.search(
        r"bouwjaar\s*:?\s*(\d{4})",
        volledige_tekst,
        re.IGNORECASE,
    )

    if match:
        gegevens[
            "bouwjaar"
        ] = int(
            match.group(1)
        )

    # ---------------------------------------------------------
    # Staat van de woning
    # ---------------------------------------------------------
    tekst_lower = volledige_tekst.lower()

    if (
        "volledig gerenoveerd moet worden"
        in tekst_lower
    ):
        gegevens[
            "staat"
        ] = "Volledig te renoveren"

    elif (
        "volledig te renoveren"
        in tekst_lower
    ):
        gegevens[
            "staat"
        ] = "Volledig te renoveren"

    elif (
        "te renoveren"
        in tekst_lower
    ):
        gegevens[
            "staat"
        ] = "Te renoveren"

    # ---------------------------------------------------------
    # EPC-label
    #
    # Alleen invullen als daadwerkelijk een letter wordt vermeld.
    # ---------------------------------------------------------
    match = re.search(
        r"\b(?:EPC|PEB)[^A-G0-9]{0,20}([A-G])\b",
        volledige_tekst,
        re.IGNORECASE,
    )

    if match:
        gegevens[
            "epc"
        ] = match.group(1).upper()

    # ---------------------------------------------------------
    # Energieverbruik
    #
    # Ardenne Immo:
    # Espec 488 Kwh/m²/j.
    # ---------------------------------------------------------
    match = re.search(
        r"Espec\s+(\d+)\s*Kwh/m²",
        volledige_tekst,
        re.IGNORECASE,
    )

    if not match:
        match = re.search(
            r"(\d+)\s*kWh\s*/?\s*m²",
            volledige_tekst,
            re.IGNORECASE,
        )

    if match:
        gegevens[
            "energieverbruik"
        ] = int(
            match.group(1)
        )

    # ---------------------------------------------------------
    # Garage
    # ---------------------------------------------------------
    if re.search(
        r"\bgarage\b",
        volledige_tekst,
        re.IGNORECASE,
    ):
        gegevens[
            "garage"
        ] = True

    # ---------------------------------------------------------
    # Schuur
    # ---------------------------------------------------------
    if re.search(
        r"\bschuur\b",
        volledige_tekst,
        re.IGNORECASE,
    ):
        gegevens[
            "schuur"
        ] = True

    # ---------------------------------------------------------
    # Tuin
    # ---------------------------------------------------------
    if re.search(
        r"\btuin\b",
        volledige_tekst,
        re.IGNORECASE,
    ):
        gegevens[
            "tuin"
        ] = True

    # ---------------------------------------------------------
    # Riolering
    # ---------------------------------------------------------
    match = re.search(
        r"(?im)^riolering\s+(ja|nee)\s*$",
        volledige_tekst,
    )

    if match:
        gegevens[
            "riolering"
        ] = (
            match.group(1).lower()
            == "ja"
        )

    # ---------------------------------------------------------
    # Winkels in de buurt
    # ---------------------------------------------------------
    match = re.search(
        r"(?im)^winkels in de buurt\s+(ja|nee)\s*$",
        volledige_tekst,
    )

    if match:
        gegevens[
            "winkels_in_buurt"
        ] = (
            match.group(1).lower()
            == "ja"
        )

    return gegevens


def haal_ardenneimmo_advertentie_op(url):
    """
    Leest één Ardenne Immo-detailadvertentie uit.
    """

    logger.info(
        "Ardenne Immo advertentie-analyse gestart: %s",
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
        "bron": "Ardenne Immo",
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
                2000
            )

            logger.info(
                "Ardenne Immo detailpagina geopend: %s",
                page.url,
            )

            volledige_tekst = veilige_tekst(
                page.locator("body")
            )

            resultaat["volledige_tekst"] = volledige_tekst

            regels = [
                regel.strip()
                for regel in volledige_tekst.splitlines()
                if regel.strip()
            ]

            # ---------------------------------------------
            # Titel / plaats
            #
            # Op Ardenne Immo staat na "ref.: <nummer>"
            # doorgaans de plaatsnaam.
            # ---------------------------------------------
            plaats = ""

            for i, regel in enumerate(regels):
                if regel.lower().startswith("ref.:"):
                    if i + 1 < len(regels):
                        plaats = regels[i + 1].strip()
                    break

            resultaat["plaats"] = plaats

            # Woningtype staat meestal vóór ref.
            titel = ""

            for i, regel in enumerate(regels):
                if regel.lower().startswith("ref.:"):
                    if i > 0:
                        titel = regels[i - 1].strip()
                    break

            if titel:
                resultaat["titel"] = titel.capitalize()
            else:
                resultaat["titel"] = page.title().strip()

            # ---------------------------------------------
            # Prijs
            #
            # Alleen een volledige regel met euroteken pakken.
            # Daardoor wordt huisnummer 92 niet meegenomen.
            # ---------------------------------------------
            prijs = None

            for regel in regels:
                if re.fullmatch(
                    r"\d[\d\s\.]*\s*€",
                    regel,
                ):
                    prijs = prijs_naar_getal(
                        regel
                    )
                    break

            resultaat["prijs"] = prijs

            # ---------------------------------------------
            # Beschrijving isoleren
            # ---------------------------------------------
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
                    if regels[i] == "Kenmerken":
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

            resultaat["beschrijving"] = beschrijving

            # ---------------------------------------------
            # Kenmerkenblok
            # ---------------------------------------------
            kenmerken_tekst = ""

            try:
                start = regels.index(
                    "Kenmerken"
                )

                kenmerken_tekst = "\n".join(
                    regels[start + 1:]
                )

            except ValueError:
                kenmerken_tekst = volledige_tekst

            resultaat["kenmerken_tekst"] = kenmerken_tekst

            # ---------------------------------------------
            # Gestructureerde kenmerken
            # ---------------------------------------------
            kenmerken = haal_gestructureerde_kenmerken(
                volledige_tekst
            )

            # ---------------------------------------------
            # Ardenne Immo samenvattingsregel
            #
            # Voorbeeld:
            # 3 kamers
            # 778 m²
            #
            # Op deze pagina is 778 m² het enige genoemde
            # oppervlaktegetal in de samenvatting.
            # Voorlopig behandelen we dit als perceeloppervlakte.
            # ---------------------------------------------
            for i, regel in enumerate(regels):
                kamers_match = re.fullmatch(
                    r"(\d+)\s+kamers?",
                    regel,
                    re.IGNORECASE,
                )

                if kamers_match:
                    kenmerken["slaapkamers"] = int(
                        kamers_match.group(1)
                    )

                    if i + 1 < len(regels):
                        opp_match = re.fullmatch(
                            r"(\d+)\s*m²",
                            regels[i + 1],
                            re.IGNORECASE,
                        )

                        if opp_match:
                            kenmerken[
                                "perceeloppervlakte"
                            ] = int(
                                opp_match.group(1)
                            )

                    break

            resultaat["kenmerken"] = kenmerken

            # ---------------------------------------------
            # Foto's
            # ---------------------------------------------
            resultaat["fotos"] = haal_fotos_op(
                page
            )

            logger.info(
                "Ardenne Immo advertentie uitgelezen: "
                "titel=%s, plaats=%s, foto's=%s",
                resultaat["titel"],
                resultaat["plaats"],
                len(
                    resultaat["fotos"]
                ),
            )

        finally:
            browser.close()

    return resultaat

def toon_advertentie(advertentie):
    """
    Toont de uitgelezen advertentie voor onze test.
    """

    print()
    print("=" * 70)
    print("ARDENNE IMMO ADVERTENTIE")
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
    print(
        "Aantal foto's gevonden: "
        f"{len(advertentie['fotos'])}"
    )

    for foto in advertentie[
        "fotos"
    ][:10]:
        print(
            f"- {foto}"
        )

    print()
    print("PAGINATEKST")
    print("-" * 70)

    print(
        advertentie[
            "volledige_tekst"
        ][:5000]
    )


if __name__ == "__main__":
    print()
    print(
        "Ardenne Immo advertentie-analyse"
    )
    print()

    test_url = input(
        "Plak een Ardenne Immo advertentielink: "
    ).strip()

    advertentie = (
        haal_ardenneimmo_advertentie_op(
            test_url
        )
    )

    toon_advertentie(
        advertentie
    )
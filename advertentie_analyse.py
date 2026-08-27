import re

from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

from config import (
    HEADLESS,
    PAGE_TIMEOUT,
    RESULTATEN_WAIT,
    SLOW_MO,
)

from config import AI_LEEFSTIJLPROFIEL
from logger import logger


def veilige_tekst(locator):
    """
    Geeft de tekst van een locator terug.
    Als het element niet bestaat, wordt een lege string teruggegeven.
    """

    try:
        if locator.count() == 0:
            return ""

        return locator.first.inner_text().strip()

    except Exception:
        return ""

def haal_plaats_uit_immoweb(page, volledige_tekst):
    """
    Probeert postcode en plaats van de woning betrouwbaar
    uit de Immoweb-detailpagina te halen.

    Eerst proberen we postcode + plaats uit de paginatekst.
    Als de plaatsnaam ontbreekt, gebruiken we de Immoweb-URL
    als fallback.
    """

    # -----------------------------------------------------
    # Eerst zoeken in de paginatekst
    # -----------------------------------------------------
    match = re.search(
        r"\b(\d{4})\s*[-–]?\s*"
        r"([A-Za-zÀ-ÖØ-öø-ÿ'’\- ]*)",
        volledige_tekst,
    )

    if match:
        postcode = match.group(1).strip()
        plaatsnaam = match.group(2).strip()

        # Alleen gebruiken als we echt een plaatsnaam hebben
        if plaatsnaam and len(plaatsnaam) <= 60:
            return f"{postcode} {plaatsnaam}"

    else:
        postcode = ""

    # -----------------------------------------------------
    # Fallback: plaats en postcode uit Immoweb-URL
    #
    # Voorbeeld:
    # /saint-hubert/6870/21747439
    # -----------------------------------------------------
    url_match = re.search(
        r"/([^/]+)/(\d{4})/\d+/?$",
        page.url,
    )

    if url_match:
        plaats_slug = url_match.group(1)
        postcode_url = url_match.group(2)

        plaatsnaam = plaats_slug.replace(
            "-",
            " ",
        ).title()

        return f"{postcode_url} {plaatsnaam}"

    # -----------------------------------------------------
    # Als alleen de postcode gevonden werd
    # -----------------------------------------------------
    if postcode:
        return postcode

    return ""
    

def is_bruikbare_immoweb_foto(url):
    """
    Controleert of een URL waarschijnlijk een echte
    woningfoto van Immoweb is.

    Logo's, SVG's en klantlogo's worden uitgesloten.
    """

    if not url:
        return False

    url_lower = url.lower()

    # Alleen echte http(s)-URL's
    if not url_lower.startswith(
        ("http://", "https://")
    ):
        return False

    # Logo's / iconen uitsluiten
    if url_lower.endswith(
        ".svg"
    ):
        return False

    if "/logo/" in url_lower:
        return False

    if "brand-logo" in url_lower:
        return False

    if "customers/" in url_lower:
        return False

    # Sterke voorkeur voor echte classified images
    if (
        "media-resize.immowebstatic.be/classifieds/"
        in url_lower
    ):
        return True

    if (
        "immowebstatic.be/classifieds/"
        in url_lower
    ):
        return True

    return False

def haal_gestructureerde_kenmerken(kenmerken_tekst):
    """
    Zet de belangrijkste woningkenmerken om
    naar afzonderlijke velden.
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
    }

    # Woonoppervlakte
    match = re.search(
        r"Bewoonbare oppervlakte\s+(\d+)\s*m²",
        kenmerken_tekst,
        re.IGNORECASE,
    )
    if match:
        gegevens["woonoppervlakte"] = int(match.group(1))

    # Perceeloppervlakte
    match = re.search(
        r"Oppervlakte van het perceel\s+(\d+)\s*m²",
        kenmerken_tekst,
        re.IGNORECASE,
    )
    if match:
        gegevens["perceeloppervlakte"] = int(match.group(1))

    # Slaapkamers
    match = re.search(
        r"^\s*Slaapkamers\s+(\d+)\s*$",
        kenmerken_tekst,
        re.IGNORECASE | re.MULTILINE,
    )
    if match:
        gegevens["slaapkamers"] = int(match.group(1))

    # Badkamers
    match = re.search(
        r"Badkamers\s+(\d+)",
        kenmerken_tekst,
        re.IGNORECASE,
    )
    if match:
        gegevens["badkamers"] = int(match.group(1))

    # Bouwjaar
    match = re.search(
        r"Bouwjaar\s+(\d{4})",
        kenmerken_tekst,
        re.IGNORECASE,
    )
    if match:
        gegevens["bouwjaar"] = int(match.group(1))

    # Staat van het gebouw
    match = re.search(
        r"Staat van het gebouw\s+([^\n]+)",
        kenmerken_tekst,
        re.IGNORECASE,
    )
    if match:
        gegevens["staat"] = match.group(1).strip()

    # EPC-label
    match = re.search(
        r"EPB/EPC-label\s+([A-G])",
        kenmerken_tekst,
        re.IGNORECASE,
    )
    if match:
        gegevens["epc"] = match.group(1).upper()

    # Energieverbruik
    match = re.search(
        r"Primair energieverbruik\s+(\d+)\s*kWh/m²",
        kenmerken_tekst,
        re.IGNORECASE,
    )
    if match:
        gegevens["energieverbruik"] = int(match.group(1))

    # Verwarming
    match = re.search(
        r"Type verwarming\s+([^\n]+)",
        kenmerken_tekst,
        re.IGNORECASE,
    )
    if match:
        gegevens["verwarming"] = match.group(1).strip()

    # Dubbel glas
    match = re.search(
        r"Dubbel glas\s+(Ja|Nee)",
        kenmerken_tekst,
        re.IGNORECASE,
    )
    if match:
        gegevens["dubbel_glas"] = (
            match.group(1).lower() == "ja"
        )

    return gegevens

def haal_immoweb_advertentie_op(url):
    """
    Leest één Immoweb-detailpagina uit.

    Retourneert een dictionary met:
    - titel
    - prijs
    - plaats
    - beschrijving
    - kenmerken_tekst
    - volledige_tekst
    - fotos
    - link
    - bron
    """

    logger.info(
        "Immoweb advertentie-analyse gestart: %s",
        url,
    )
    
    resultaat = {
        "titel": "",
        "prijs": "",
        "plaats": "",
        "beschrijving": "",
        "kenmerken_tekst": "",
        "kenmerken": {},
        "volledige_tekst": "",
        "fotos": [],
        "link": url,
        "bron": "Immoweb",
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
                RESULTATEN_WAIT
            )

            logger.info(
                "Immoweb detailpagina geopend: %s",
                page.url,
            )

            # -------------------------------------------------
            # Cookies
            # -------------------------------------------------
            try:
                page.get_by_test_id(
                    "uc-accept-all-button"
                ).click(
                    timeout=3000
                )

                page.wait_for_timeout(
                    500
                )

            except PlaywrightTimeoutError:
                pass

            # -------------------------------------------------
            # Titel
            # -------------------------------------------------
            titel = veilige_tekst(
                page.locator(
                    "h1"
                )
            )

            resultaat["titel"] = titel

            # -------------------------------------------------
            # Volledige bodytekst
            # -------------------------------------------------
            volledige_tekst = (
                page.locator(
                    "body"
                )
                .inner_text()
                .strip()
            )

            resultaat["volledige_tekst"] = (
                volledige_tekst
            )

            # -------------------------------------------------
            # Prijs
            # -------------------------------------------------
            
            prijs_tekst = veilige_tekst(
                page.locator(
                    "[class*='price']"
                )
            )

            prijs = None

            if prijs_tekst:
                prijs_match = re.search(
                    r"€\s*([\d\.]+)",
                    prijs_tekst,
                )

                if prijs_match:
                    prijs_cijfers = re.sub(
                        r"[^\d]",
                        "",
                        prijs_match.group(1),
                    )

                    if prijs_cijfers:
                        prijs = int(
                            prijs_cijfers
                        )

            # Fallback: zoeken in volledige paginatekst
            if prijs is None:
                prijs_match = re.search(
                    r"€\s*([\d\.]+)",
                    volledige_tekst,
                )

                if prijs_match:
                    prijs_cijfers = re.sub(
                        r"[^\d]",
                        "",
                        prijs_match.group(1),
                    )

                    if prijs_cijfers:
                        prijs = int(
                            prijs_cijfers
                        )

            resultaat["prijs"] = prijs

            # -------------------------------------------------
            # Plaats
            # -------------------------------------------------
            resultaat["plaats"] = (
                haal_plaats_uit_immoweb(
                    page,
                    volledige_tekst,
                )
            )

            # -------------------------------------------------
            # Beschrijving
            # -------------------------------------------------
            beschrijving_selectors = [
                "[class*='description']",
                "[class*='classified__description']",
                "section[class*='description']",
                "div[class*='description']",
            ]

            beschrijving = ""

            for selector in beschrijving_selectors:
                tekst = veilige_tekst(
                    page.locator(
                        selector
                    )
                )

                if (
                    tekst
                    and len(tekst)
                    > len(beschrijving)
                ):
                    beschrijving = tekst

            resultaat[
                "beschrijving"
            ] = beschrijving

            # -------------------------------------------------
            # Kenmerken / details
            # -------------------------------------------------
            kenmerken_delen = []

            mogelijke_blokken = page.locator(
                "section, dl, table"
            )

            for i in range(
                mogelijke_blokken.count()
            ):
                blok = mogelijke_blokken.nth(
                    i
                )

                try:
                    tekst = (
                        blok.inner_text().strip()
                    )

                    if not tekst:
                        continue

                    tekst_lower = (
                        tekst.lower()
                    )

                    if any(
                        sleutelwoord
                        in tekst_lower
                        for sleutelwoord in [
                            "slaapkamer",
                            "oppervlakte",
                            "perceel",
                            "garage",
                            "bouwjaar",
                            "renovatie",
                            "energie",
                            "epc",
                            "epb",
                            "tuin",
                            "terras",
                            "verwarming",
                            "parkeer",
                        ]
                    ):
                        if (
                            tekst
                            not in kenmerken_delen
                        ):
                            kenmerken_delen.append(
                                tekst
                            )

                except Exception:
                    continue

            resultaat[
                "kenmerken_tekst"
            ] = "\n\n".join(
                kenmerken_delen
            )
            resultaat["kenmerken"] = (
                haal_gestructureerde_kenmerken(
                    resultaat["kenmerken_tekst"]
                )
            )
            # -------------------------------------------------
            # Foto's
            # -------------------------------------------------
            foto_urls = []

            afbeeldingen = page.locator(
                "img"
            )

            for i in range(
                afbeeldingen.count()
            ):
                afbeelding = afbeeldingen.nth(
                    i
                )

                try:
                    kandidaten = []

                    src = (
                        afbeelding
                        .get_attribute(
                            "src"
                        )
                    )

                    if src:
                        kandidaten.append(
                            src
                        )

                    data_src = (
                        afbeelding
                        .get_attribute(
                            "data-src"
                        )
                    )

                    if data_src:
                        kandidaten.append(
                            data_src
                        )

                    srcset = (
                        afbeelding
                        .get_attribute(
                            "srcset"
                        )
                    )

                    if srcset:
                        onderdelen = [
                            onderdeel.strip()
                            for onderdeel
                            in srcset.split(",")
                            if onderdeel.strip()
                        ]

                        if onderdelen:
                            kandidaten.append(
                                onderdelen[-1]
                                .split()[0]
                            )

                    for foto in kandidaten:
                        foto = foto.strip()

                        if not (
                            is_bruikbare_immoweb_foto(
                                foto
                            )
                        ):
                            continue

                        if (
                            foto
                            not in foto_urls
                        ):
                            foto_urls.append(
                                foto
                            )

                except Exception:
                    continue

            resultaat[
                "fotos"
            ] = foto_urls

            logger.info(
                "Immoweb advertentie uitgelezen: "
                "titel=%s, plaats=%s, foto's=%s",
                resultaat["titel"],
                resultaat["plaats"],
                len(
                    resultaat["fotos"]
                ),
            )

            return resultaat

        finally:
            browser.close()


def toon_advertentie(advertentie):
    """
    Print de uitgelezen advertentie overzichtelijk
    in de terminal.
    """

    print()
    print("=" * 70)
    print("IMMOWEB ADVERTENTIE")
    print("=" * 70)

    print(
        f"Titel : "
        f"{advertentie['titel']}"
    )

    print(
        f"Prijs : "
        f"{advertentie['prijs']}"
    )

    print(
        f"Plaats: "
        f"{advertentie['plaats']}"
    )

    print()
    print("BESCHRIJVING")
    print("-" * 70)

    beschrijving = (
        advertentie[
            "beschrijving"
        ]
        or
        "Geen aparte beschrijving gevonden."
    )

    print(
        beschrijving[:5000]
    )

    print()
    print("KENMERKEN")
    print("-" * 70)

    kenmerken = (
        advertentie[
            "kenmerken_tekst"
        ]
        or
        "Geen afzonderlijk kenmerkenblok gevonden."
    )

    print(
        kenmerken[:5000]
    )

    print()
    print(
        f"Aantal echte woningfoto's gevonden: "
        f"{len(advertentie['fotos'])}"
    )

    for foto in advertentie[
        "fotos"
    ][:5]:
        print(
            f"- {foto}"
        )

    print("=" * 70)
    
    print()
    print("GESTRUCTUREERDE KENMERKEN")
    print("-" * 70)

    for naam, waarde in advertentie[
        "kenmerken"
    ].items():
        print(
            f"{naam:22}: {waarde}"
        )
    
if __name__ == "__main__":
    test_url = input(
        "Plak een Immoweb advertentielink: "
    ).strip()

    advertentie = (
        haal_immoweb_advertentie_op(
            test_url
        )
    )

    toon_advertentie(
        advertentie
    )
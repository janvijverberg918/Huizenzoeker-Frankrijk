import re

from playwright.sync_api import (
    Error as PlaywrightError,
    sync_playwright,
)

from config import (
    HEADLESS,
    PAGE_TIMEOUT,
    RESULTATEN_WAIT,
    SLOW_MO,
)
from csv_opslaan import opslaan_csv
from logger import logger
from vergelijk import nieuwe_woningen


BASE_URL = "https://www.biddit.be"

MAX_START_POGINGEN = 2


def prijs_naar_getal(prijs_tekst):
    """
    Zet een prijs om naar een geheel getal.

    Voorbeelden:
    '€ 234.400' -> 234400
    '€ 90.000'  -> 90000
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


def haal_postcode_uit_tekst(tekst):
    """
    Haalt de echte postcode uit een Biddit-resultaat.

    We zoeken naar een regel die begint met vier cijfers
    gevolgd door een plaatsnaam.

    Hierdoor wordt bijvoorbeeld:

    '2200 m²'

    niet aangezien voor postcode 2200.
    """

    if not tekst:
        return None

    regels = [
        regel.strip()
        for regel in str(tekst).splitlines()
        if regel.strip()
    ]

    for regel in reversed(regels):
        match = re.match(
            r"^(\d{4})\s+\D+",
            regel,
        )

        if match:
            return match.group(1)

    return None


def haal_plaats_uit_tekst(tekst):
    """
    Haalt een plaatsregel uit een Biddit-resultaat.

    Voorbeeld:
    '6987 Rendeux'
    """

    if not tekst:
        return "Onbekend"

    regels = [
        regel.strip()
        for regel in str(tekst).splitlines()
        if regel.strip()
    ]

    for regel in reversed(regels):
        if re.match(
            r"^\d{4}\s+\D+",
            regel,
        ):
            return regel

    return "Onbekend"


def haal_titel_uit_regels(regels):
    """
    Probeert uit een Biddit-kaart een bruikbare titel
    of omschrijving te halen.

    Technische regels zoals prijs, oppervlakte,
    verkooptype, postcode en losse getallen worden
    overgeslagen.
    """

    for regel in regels[1:]:

        # Los getal, bijvoorbeeld aantal kamers
        if regel.isdigit():
            continue

        # Oppervlakte
        if re.fullmatch(
            r"\d+\s*m²",
            regel,
            re.IGNORECASE,
        ):
            continue

        # Postcode + plaats
        if re.match(
            r"^\d{4}\s+\D+",
            regel,
        ):
            continue

        regel_lower = regel.lower()

        # Verkoopinformatie
        if (
            "uit de hand" in regel_lower
            or "openbare verkoop" in regel_lower
            or "start op" in regel_lower
        ):
            continue

        # Datum/tijdachtige regels
        if re.search(
            r"\d{1,2}/\d{1,2}",
            regel,
        ):
            continue

        return regel

    return "Vastgoed te koop"


def haal_foto_url_biddit(link_element):
    """
    Probeert de hoofdfoto van een Biddit-resultaatkaart
    uit te lezen.

    Probeert verschillende attributen omdat websites
    afbeeldingen soms lazy-loaden.

    Volgorde:
    - src
    - data-src
    - data-lazy-src
    - srcset

    Geeft een lege string terug als geen bruikbare
    afbeelding wordt gevonden.
    """

    try:
        afbeeldingen = link_element.locator(
            "img"
        )

        if afbeeldingen.count() == 0:
            return ""

        for i in range(
            afbeeldingen.count()
        ):
            afbeelding = afbeeldingen.nth(
                i
            )

            # ---------------------------------------------
            # Normale src
            # ---------------------------------------------
            foto = afbeelding.get_attribute(
                "src"
            )

            if foto and foto.strip():
                foto = foto.strip()

                if foto.startswith("//"):
                    foto = "https:" + foto

                elif foto.startswith("/"):
                    foto = BASE_URL + foto

                return foto

            # ---------------------------------------------
            # Lazy loading: data-src
            # ---------------------------------------------
            foto = afbeelding.get_attribute(
                "data-src"
            )

            if foto and foto.strip():
                foto = foto.strip()

                if foto.startswith("//"):
                    foto = "https:" + foto

                elif foto.startswith("/"):
                    foto = BASE_URL + foto

                return foto

            # ---------------------------------------------
            # Alternatieve lazy loading
            # ---------------------------------------------
            foto = afbeelding.get_attribute(
                "data-lazy-src"
            )

            if foto and foto.strip():
                foto = foto.strip()

                if foto.startswith("//"):
                    foto = "https:" + foto

                elif foto.startswith("/"):
                    foto = BASE_URL + foto

                return foto

            # ---------------------------------------------
            # Responsive afbeelding
            # ---------------------------------------------
            srcset = afbeelding.get_attribute(
                "srcset"
            )

            if srcset and srcset.strip():
                onderdelen = [
                    onderdeel.strip()
                    for onderdeel in srcset.split(",")
                    if onderdeel.strip()
                ]

                if onderdelen:
                    foto = (
                        onderdelen[-1]
                        .split()[0]
                        .strip()
                    )

                    if foto.startswith("//"):
                        foto = "https:" + foto

                    elif foto.startswith("/"):
                        foto = BASE_URL + foto

                    return foto

    except Exception:
        logger.exception(
            "Hoofdfoto kon niet worden uitgelezen "
            "van Biddit-resultaat"
        )

    return ""


def open_biddit(page):
    """
    Opent de Biddit-startpagina.

    Er wordt maximaal twee keer geprobeerd omdat Biddit
    incidenteel een DNS/netwerkfout kan geven.
    """

    laatste_fout = None

    for poging in range(
        1,
        MAX_START_POGINGEN + 1,
    ):
        try:
            logger.info(
                "Biddit startpagina poging %s van %s",
                poging,
                MAX_START_POGINGEN,
            )

            page.goto(
                "https://www.biddit.be/nl/landing",
                wait_until="domcontentloaded",
                timeout=PAGE_TIMEOUT,
            )

            return

        except PlaywrightError as fout:
            laatste_fout = fout

            logger.warning(
                "Biddit startpagina kon bij poging %s "
                "niet worden geopend: %s",
                poging,
                fout,
            )

            if poging < MAX_START_POGINGEN:
                wachttijd = 3000 * poging

                logger.info(
                    "Wachten %s ms voor nieuwe "
                    "Biddit-poging",
                    wachttijd,
                )

                page.wait_for_timeout(
                    wachttijd
                )

    raise laatste_fout


def zoek_biddit(
    postcode,
    woningtype,
    min_prijs,
    max_prijs,
    csv_bestand,
):
    """
    Zoekt vastgoed op Biddit.

    Bewuste strategie voor Biddit:

    - zoekpostcode wordt gebruikt als ingang naar de regio;
    - resultaten met omliggende postcodes mogen mee;
    - woningtype wordt NIET hard gefilterd;
    - alleen prijsrange wordt toegepast;
    - dezelfde Biddit-link kan via meerdere zoekgebieden
      terugkomen;
    - centrale deduplicatie in huizenzoeker.py verwijdert
      die dubbelen later;
    - CSV-historie bepaalt welke advertenties nieuw zijn.
    """

    logger.info(
        "Zoeken op Biddit gestart: "
        "postcode=%s, woningtype=%s, prijs=%s-%s",
        postcode,
        woningtype,
        min_prijs,
        max_prijs,
    )

    resultaten = []
    nieuw = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=HEADLESS,
                slow_mo=0 if HEADLESS else SLOW_MO,
            )

            try:
                page = browser.new_page()

                # -------------------------------------------------
                # Biddit openen
                # -------------------------------------------------
                open_biddit(
                    page
                )

                # -------------------------------------------------
                # Cookies
                # -------------------------------------------------
                try:
                    page.get_by_role(
                        "button",
                        name="Alle cookies aanvaarden",
                    ).click(
                        timeout=5000
                    )

                    logger.info(
                        "Biddit cookiemelding geaccepteerd"
                    )

                except Exception:
                    logger.info(
                        "Geen Biddit cookiemelding zichtbaar"
                    )

                # -------------------------------------------------
                # Zoekpostcode invullen
                # -------------------------------------------------
                locatie = page.get_by_role(
                    "textbox",
                    name="Provincie, gemeente, postcode",
                )

                locatie.click()

                locatie.fill(
                    str(postcode)
                )

                page.wait_for_timeout(
                    1500
                )

                # -------------------------------------------------
                # Autocomplete
                # -------------------------------------------------
                locatie.press(
                    "ArrowDown"
                )

                page.wait_for_timeout(
                    300
                )

                locatie.press(
                    "Enter"
                )

                page.wait_for_timeout(
                    1000
                )

                logger.info(
                    "Biddit-locatiesuggestie geselecteerd "
                    "voor postcode %s",
                    postcode,
                )

                # -------------------------------------------------
                # Alle verkopen
                # -------------------------------------------------
                try:
                    page.get_by_role(
                        "tab",
                        name="Alle Verkopen",
                    ).click(
                        timeout=5000
                    )

                except Exception:
                    logger.info(
                        "Tab 'Alle Verkopen' hoefde niet "
                        "apart geselecteerd te worden"
                    )

                # -------------------------------------------------
                # Zoekopdracht uitvoeren
                # -------------------------------------------------
                page.get_by_role(
                    "button",
                    name="Zoeken",
                ).click()

                page.wait_for_load_state(
                    "domcontentloaded"
                )

                page.wait_for_timeout(
                    RESULTATEN_WAIT
                )

                logger.info(
                    "Biddit resultatenpagina geopend: %s",
                    page.url,
                )

                # -------------------------------------------------
                # Detail-links vinden
                # -------------------------------------------------
                detail_links = page.locator(
                    "a[href^='/nl/catalog/detail/']"
                )

                aantal_links = (
                    detail_links.count()
                )

                logger.info(
                    "%s Biddit-detail-links gevonden "
                    "voor zoekpostcode %s",
                    aantal_links,
                    postcode,
                )

                aantal_buiten_prijs = 0
                aantal_zonder_prijs = 0

                # -------------------------------------------------
                # Resultaten uitlezen
                # -------------------------------------------------
                for i in range(
                    aantal_links
                ):
                    link_element = (
                        detail_links.nth(i)
                    )

                    try:
                        tekst = (
                            link_element
                            .inner_text()
                            .strip()
                        )

                        href = (
                            link_element
                            .get_attribute(
                                "href"
                            )
                        )

                        if not tekst or not href:
                            continue

                        regels = [
                            regel.strip()
                            for regel in tekst.splitlines()
                            if regel.strip()
                        ]

                        if not regels:
                            continue

                        # -----------------------------------------
                        # Prijs
                        # -----------------------------------------
                        prijs = regels[0]

                        prijs_getal = (
                            prijs_naar_getal(
                                prijs
                            )
                        )

                        if prijs_getal is None:
                            aantal_zonder_prijs += 1
                            continue

                        if not (
                            min_prijs
                            <= prijs_getal
                            <= max_prijs
                        ):
                            aantal_buiten_prijs += 1
                            continue

                        # -----------------------------------------
                        # Werkelijke postcode
                        # -----------------------------------------
                        gevonden_postcode = (
                            haal_postcode_uit_tekst(
                                tekst
                            )
                        )

                        logger.info(
                            "Biddit resultaat %s: "
                            "zoekpostcode=%s, "
                            "gevonden postcode=%s",
                            i,
                            postcode,
                            gevonden_postcode,
                        )

                        # -----------------------------------------
                        # Oppervlakte
                        # -----------------------------------------
                        oppervlakte_match = re.search(
                            r"(\d+)\s*m²",
                            tekst,
                            re.IGNORECASE,
                        )

                        oppervlakte = (
                            oppervlakte_match.group(1)
                            if oppervlakte_match
                            else "Onbekend"
                        )

                        # -----------------------------------------
                        # Titel / omschrijving
                        # -----------------------------------------
                        titel = (
                            haal_titel_uit_regels(
                                regels
                            )
                        )

                        # -----------------------------------------
                        # Plaats
                        # -----------------------------------------
                        plaats = (
                            haal_plaats_uit_tekst(
                                tekst
                            )
                        )

                        # -----------------------------------------
                        # Hoofdfoto
                        # -----------------------------------------
                        foto = haal_foto_url_biddit(
                            link_element
                        )

                        if foto:
                            logger.info(
                                "Biddit foto gevonden "
                                "voor resultaat %s",
                                i,
                            )

                        else:
                            logger.info(
                                "Geen Biddit foto gevonden "
                                "voor resultaat %s",
                                i,
                            )

                        # -----------------------------------------
                        # Absolute link
                        # -----------------------------------------
                        if href.startswith("/"):
                            link = (
                                BASE_URL
                                + href
                            )

                        else:
                            link = href

                        # -----------------------------------------
                        # Resultaat
                        # -----------------------------------------
                        resultaten.append({
                            "titel": titel,
                            "prijs": prijs,
                            "slaapkamers": "Onbekend",
                            "oppervlakte": oppervlakte,
                            "perceeloppervlakte": "",
                            "plaats": plaats,
                            "link": link,
                            "foto": foto,
                            "bron": "Biddit",
                        })

                    except Exception:
                        logger.exception(
                            "Biddit resultaat %s kon niet "
                            "worden uitgelezen",
                            i,
                        )

                # -------------------------------------------------
                # Samenvatting parser
                # -------------------------------------------------
                logger.info(
                    "Biddit zoekpostcode %s: "
                    "%s detail-links, "
                    "%s buiten prijsrange, "
                    "%s zonder bruikbare prijs, "
                    "%s passend",
                    postcode,
                    aantal_links,
                    aantal_buiten_prijs,
                    aantal_zonder_prijs,
                    len(resultaten),
                )

                print(
                    f"Biddit: "
                    f"{len(resultaten)} "
                    f"passende object(en) uitgelezen"
                )

                # -------------------------------------------------
                # Nieuwe advertenties bepalen
                # -------------------------------------------------
                nieuw = nieuwe_woningen(
                    resultaten,
                    csv_bestand=csv_bestand,
                )

                logger.info(
                    "%s nieuwe Biddit-advertentie(s) "
                    "gevonden voor zoekpostcode %s",
                    len(nieuw),
                    postcode,
                )

                # -------------------------------------------------
                # Historie opslaan
                # -------------------------------------------------
                opslaan_csv(
                    resultaten,
                    bestandsnaam=csv_bestand,
                )

                logger.info(
                    "Biddit CSV-bestand '%s' bijgewerkt",
                    csv_bestand,
                )

            finally:
                browser.close()

                logger.info(
                    "Biddit-browser gesloten "
                    "voor postcode %s",
                    postcode,
                )

    except Exception:
        logger.exception(
            "Biddit-zoekopdracht voor postcode %s "
            "is mislukt",
            postcode,
        )

        raise

    return nieuw
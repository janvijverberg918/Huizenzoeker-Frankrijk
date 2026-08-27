import re

from playwright.sync_api import (
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


BASE_URL = "https://www.ardenneimmo.be"


def prijs_naar_getal(prijs_tekst):
    """
    Zet een Ardenne Immo-prijs om naar een integer.

    Voorbeelden:
    '199 000 €' -> 199000
    '245.000 €' -> 245000

    Teksten zoals 'te laat' leveren None op.
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


def is_gewenst_woningtype(
    link,
    woningtype,
):
    """
    Controleert het woningtype op basis van de detail-URL.

    Voor versie 3 ondersteunen we hier voorlopig 'huis'.
    """

    if woningtype == "huis":
        return "huis-te-koop" in link.lower()

    raise ValueError(
        f"Woningtype '{woningtype}' is voor "
        f"Ardenne Immo nog niet ingebouwd"
    )


def haal_foto_url_ardenneimmo(kaart):
    """
    Probeert de hoofdfoto van een Ardenne Immo
    woningkaart uit te lezen.

    Probeert:
    - src
    - data-src
    - data-lazy-src
    - srcset

    Geeft een lege string terug wanneer geen
    bruikbare afbeelding gevonden wordt.
    """

    try:
        afbeeldingen = kaart.locator("img")

        if afbeeldingen.count() == 0:
            return ""

        # Soms kan een kaart meerdere afbeeldingen bevatten.
        # We proberen ze daarom één voor één.
        for i in range(
            afbeeldingen.count()
        ):
            afbeelding = afbeeldingen.nth(i)

            # Normale src
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

            # Lazy loading
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

            # Alternatieve lazy-loading
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

            # Responsive afbeeldingen
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
            "van Ardenne Immo woningkaart"
        )

    return ""


def zoek_ardenneimmo(
    postcode,
    woningtype,
    min_prijs,
    max_prijs,
    csv_bestand,
):
    logger.info(
        "Zoeken op Ardenne Immo gestart: "
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
                # Website openen
                # -------------------------------------------------
                page.goto(
                    "https://www.ardenneimmo.be/nl",
                    wait_until="domcontentloaded",
                    timeout=PAGE_TIMEOUT,
                )

                logger.info(
                    "Ardenne Immo URL: %s",
                    page.url,
                )

                logger.info(
                    "Ardenne Immo paginatitel: %s",
                    page.title(),
                )

                # -------------------------------------------------
                # Postcode invullen
                # -------------------------------------------------
                locatie = page.get_by_role(
                    "combobox",
                    name="Find",
                )

                locatie.click()
                locatie.fill(
                    str(postcode)
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
                    "Ardenne Immo resultatenpagina geopend: %s",
                    page.url,
                )

                # -------------------------------------------------
                # Mogelijke woningkaarten zoeken
                # -------------------------------------------------
                kandidaten = page.locator(
                    "[id]"
                )

                woningkaarten = []

                for i in range(
                    kandidaten.count()
                ):
                    element = kandidaten.nth(i)

                    try:
                        element_id = element.get_attribute(
                            "id"
                        )

                        if not element_id:
                            continue

                        # Woning-ID's op Ardenne Immo zijn numeriek
                        if re.fullmatch(
                            r"\d+",
                            element_id,
                        ):
                            woningkaarten.append(
                                element
                            )

                    except Exception:
                        continue

                logger.info(
                    "%s mogelijke woningkaarten gevonden "
                    "op Ardenne Immo voor postcode %s",
                    len(woningkaarten),
                    postcode,
                )

                aantal_verkeerd_type = 0
                aantal_buiten_prijs = 0
                aantal_zonder_prijs = 0

                # -------------------------------------------------
                # Woningkaarten uitlezen
                # -------------------------------------------------
                for i, kaart in enumerate(
                    woningkaarten
                ):
                    try:
                        tekst = kaart.inner_text().strip()

                        if not tekst:
                            continue

                        regels = [
                            regel.strip()
                            for regel in tekst.splitlines()
                            if regel.strip()
                        ]

                        if len(regels) < 3:
                            continue

                        # Voorbeeld:
                        #
                        # LA ROCHE-EN-ARDENNE
                        # 265 000 €
                        # 2 k. 53 m² 2500 m²
                        # Meer info

                        plaats_zonder_postcode = regels[0]
                        prijs = regels[1]

                        kenmerken_tekst = " ".join(
                            regels[2:]
                        )

                        # -------------------------------------------------
                        # Detail-link eerst bepalen
                        # -------------------------------------------------
                        links = kaart.locator(
                            "a"
                        )

                        link = None

                        for j in range(
                            links.count()
                        ):
                            href = links.nth(
                                j
                            ).get_attribute(
                                "href"
                            )

                            if not href:
                                continue

                            if "/nl/e/" in href:
                                link = href
                                break

                        if not link:
                            logger.warning(
                                "Geen detail-link gevonden "
                                "voor Ardenne Immo kaart %s",
                                i,
                            )
                            continue

                        # -------------------------------------------------
                        # Woningtype filteren
                        # -------------------------------------------------
                        if not is_gewenst_woningtype(
                            link,
                            woningtype,
                        ):
                            aantal_verkeerd_type += 1
                            continue

                        # -------------------------------------------------
                        # Prijs filteren
                        # -------------------------------------------------
                        prijs_getal = prijs_naar_getal(
                            prijs
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

                        # -------------------------------------------------
                        # Slaapkamers
                        # -------------------------------------------------
                        slaapkamers_match = re.search(
                            r"(\d+)\s*k\.",
                            kenmerken_tekst,
                            re.IGNORECASE,
                        )

                        slaapkamers = (
                            slaapkamers_match.group(1)
                            if slaapkamers_match
                            else "Onbekend"
                        )

                        # -------------------------------------------------
                        # Woon- en perceeloppervlakte
                        # -------------------------------------------------
                        oppervlaktes = re.findall(
                            r"(\d+)\s*m²",
                            kenmerken_tekst,
                            re.IGNORECASE,
                        )

                        oppervlakte = (
                            oppervlaktes[0]
                            if len(oppervlaktes) >= 1
                            else "Onbekend"
                        )

                        perceeloppervlakte = (
                            oppervlaktes[1]
                            if len(oppervlaktes) >= 2
                            else "Onbekend"
                        )

                        # -------------------------------------------------
                        # Hoofdfoto
                        # -------------------------------------------------
                        foto = haal_foto_url_ardenneimmo(
                            kaart
                        )

                        if foto:
                            logger.info(
                                "Ardenne Immo foto gevonden "
                                "voor woning %s",
                                i,
                            )
                        else:
                            logger.info(
                                "Geen Ardenne Immo foto gevonden "
                                "voor woning %s",
                                i,
                            )

                        # -------------------------------------------------
                        # Absolute URL maken
                        # -------------------------------------------------
                        if link.startswith("/"):
                            link = (
                                BASE_URL
                                + link
                            )

                        # -------------------------------------------------
                        # Postcode toevoegen aan plaats
                        #
                        # Dit is belangrijk voor onze deduplicatie met
                        # Immoweb en Immovlan.
                        # -------------------------------------------------
                        plaats = (
                            f"{postcode} "
                            f"{plaats_zonder_postcode}"
                        )

                        # -------------------------------------------------
                        # Titel
                        # -------------------------------------------------
                        titel = "Huis te koop"

                        resultaten.append({
                            "titel": titel,
                            "prijs": prijs,
                            "slaapkamers": slaapkamers,
                            "oppervlakte": oppervlakte,
                            "perceeloppervlakte": perceeloppervlakte,
                            "plaats": plaats,
                            "link": link,
                            "foto": foto,
                            "bron": "Ardenne Immo",
                        })

                    except Exception:
                        logger.exception(
                            "Ardenne Immo woning %s "
                            "kon niet worden uitgelezen",
                            i,
                        )

                # -------------------------------------------------
                # Logging filters
                # -------------------------------------------------
                logger.info(
                    "Ardenne Immo postcode %s: "
                    "%s kaarten bekeken, "
                    "%s verkeerd woningtype, "
                    "%s buiten prijsrange, "
                    "%s zonder bruikbare prijs",
                    postcode,
                    len(woningkaarten),
                    aantal_verkeerd_type,
                    aantal_buiten_prijs,
                    aantal_zonder_prijs,
                )

                logger.info(
                    "%s woningen voldoen aan de filters "
                    "op Ardenne Immo voor postcode %s",
                    len(resultaten),
                    postcode,
                )

                print(
                    f"Ardenne Immo: "
                    f"{len(resultaten)} passende woningen uitgelezen"
                )

                # -------------------------------------------------
                # Nieuwe woningen bepalen
                # -------------------------------------------------
                nieuw = nieuwe_woningen(
                    resultaten,
                    csv_bestand=csv_bestand,
                )

                logger.info(
                    "%s nieuwe Ardenne Immo-woningen gevonden "
                    "voor postcode %s",
                    len(nieuw),
                    postcode,
                )

                # -------------------------------------------------
                # CSV opslaan
                # -------------------------------------------------
                opslaan_csv(
                    resultaten,
                    bestandsnaam=csv_bestand,
                )

                logger.info(
                    "Ardenne Immo CSV-bestand '%s' bijgewerkt",
                    csv_bestand,
                )

            finally:
                browser.close()

                logger.info(
                    "Ardenne Immo-browser gesloten "
                    "voor postcode %s",
                    postcode,
                )

    except Exception:
        logger.exception(
            "Ardenne Immo-zoekopdracht voor postcode %s "
            "is mislukt",
            postcode,
        )
        raise

    return nieuw
import re
import time

from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

from config import (
    COOKIE_TIMEOUT,
    FORMULIER_WAIT,
    HEADLESS,
    LOCATIE_TIMEOUT,
    PAGE_TIMEOUT,
    RESULTATEN_WAIT,
    SLOW_MO,
)
from csv_opslaan import opslaan_csv
from logger import logger
from vergelijk import nieuwe_woningen


MAX_POGINGEN = 3


# =========================================================
# Snelle directe Immovlan-route
# =========================================================

# Deze 26 postcode/municipal-combinaties zijn op 20-08-2026
# gevalideerd: de directe resultaten-URL miste geen woningen
# ten opzichte van de normale formuliermethode.
IMMOVLAN_DIRECT_VEILIG = {
    "5550": "vresse-sur-semois",
    "5555": "bievre",
    "5575": "gedinne",
    "5580": "rochefort",
    "6600": "bastogne",
    "6637": "fauvillers",
    "6640": "vaux-sur-sure",
    "6660": "houffalize",
    "6670": "gouvy",
    "6680": "sainte-ode",
    "6800": "libramont-chevigny",
    "6830": "bouillon",
    "6840": "neufchateau",
    "6870": "saint-hubert",
    "6880": "bertrix",
    "6887": "herbeumont",
    "6890": "libin",
    "6900": "marche-en-famenne",
    "6927": "tellin",
    "6929": "daverdisse",
    "6940": "durbuy",
    "6950": "nassogne",
    "6960": "manhay",
    "6980": "la-roche-en-ardenne",
    "6987": "rendeux",
    "6997": "erezee",
}

# Deze postcodes blijven bewust op de normale formulierroute.
IMMOVLAN_NORMALE_FALLBACK = {
    "4900",  # Spa: geen bruikbare municipal
    "6630",  # Martelange: geen bruikbare municipal
    "6690",  # Vielsalm: directe route miste woning(en)
    "6850",  # Paliseul: directe route miste woning(en)
    "6860",  # Léglise: directe route miste woning(en)
}


# =========================================================
# Algemene hulpfuncties
# =========================================================

def prijs_naar_getal(waarde):
    """
    Zet een prijs om naar een geheel getal.

    Voorbeelden:
    '€ 225.000' -> 225000
    '225 000 €' -> 225000
    """

    if waarde is None:
        return None

    cijfers = re.findall(
        r"\d+",
        str(waarde),
    )

    if not cijfers:
        return None

    try:
        return int(
            "".join(cijfers)
        )

    except ValueError:
        return None


def haal_foto_url_immovlan(card):
    """
    Probeert een bruikbare hoofdfoto van een
    Immovlan-resultaatkaart uit te lezen.

    Alleen echte http(s)-afbeeldingen worden gebruikt.
    Relatieve Immovlan-URL's worden absoluut gemaakt.
    Data-URL's en placeholders worden genegeerd.
    """

    try:
        afbeeldingen = card.locator(
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

            kandidaten = []

            # ---------------------------------------------
            # src
            # ---------------------------------------------
            src = afbeelding.get_attribute(
                "src"
            )

            if src:
                kandidaten.append(
                    src.strip()
                )

            # ---------------------------------------------
            # data-src
            # ---------------------------------------------
            data_src = afbeelding.get_attribute(
                "data-src"
            )

            if data_src:
                kandidaten.append(
                    data_src.strip()
                )

            # ---------------------------------------------
            # srcset
            # ---------------------------------------------
            srcset = afbeelding.get_attribute(
                "srcset"
            )

            if srcset:
                onderdelen = [
                    onderdeel.strip()
                    for onderdeel in srcset.split(",")
                    if onderdeel.strip()
                ]

                # Grootste variant staat normaal als laatste.
                for onderdeel in reversed(
                    onderdelen
                ):
                    url = (
                        onderdeel
                        .split()[0]
                        .strip()
                    )

                    if url:
                        kandidaten.append(
                            url
                        )

            # ---------------------------------------------
            # Kandidaten controleren
            # ---------------------------------------------
            for foto in kandidaten:
                if not foto:
                    continue

                foto_lower = foto.lower()

                # Geen inline placeholder.
                if foto_lower.startswith(
                    "data:"
                ):
                    continue

                # Logo's / iconen overslaan.
                if any(
                    woord in foto_lower
                    for woord in (
                        "logo",
                        "icon",
                        "placeholder",
                        "favicon",
                    )
                ):
                    continue

                # Protocol-relative URL
                if foto.startswith("//"):
                    foto = (
                        "https:"
                        + foto
                    )

                # Relatieve Immovlan URL
                elif foto.startswith("/"):
                    foto = (
                        "https://immovlan.be"
                        + foto
                    )

                # Alleen echte web-URL's accepteren.
                if not foto.startswith(
                    (
                        "https://",
                        "http://",
                    )
                ):
                    continue

                return foto

    except Exception:
        logger.exception(
            "Hoofdfoto kon niet worden uitgelezen "
            "van Immovlan-resultaatkaart"
        )

    return ""


def accepteer_cookies(page):
    """
    Probeert de Immovlan / Didomi cookiemelding
    betrouwbaar af te handelen.
    """

    page.wait_for_timeout(
        1000
    )

    cookie_knop = page.get_by_role(
        "button",
        name="Akkoord en sluiten: Akkoord",
    )

    didomi_popup = page.locator(
        "#didomi-popup"
    )

    try:
        cookie_knop.click(
            timeout=COOKIE_TIMEOUT
        )

        logger.info(
            "Immovlan cookiemelding geaccepteerd"
        )

    except PlaywrightTimeoutError:
        logger.info(
            "Cookieknop niet direct zichtbaar"
        )

    page.wait_for_timeout(
        500
    )

    try:
        popup_zichtbaar = (
            didomi_popup.is_visible()
        )

    except Exception:
        popup_zichtbaar = False

    if popup_zichtbaar:
        logger.warning(
            "Immovlan cookie-popup nog zichtbaar; "
            "tweede poging"
        )

        try:
            cookie_knop.click(
                timeout=COOKIE_TIMEOUT,
                force=True,
            )

            page.wait_for_timeout(
                500
            )

            logger.info(
                "Immovlan cookiemelding bij "
                "tweede poging gesloten"
            )

        except Exception:
            logger.exception(
                "Immovlan cookie-popup kon "
                "niet worden gesloten"
            )

            raise


# =========================================================
# Startpagina en interface-detectie
# =========================================================

def open_startpagina(page):
    """
    Opent Immovlan en bepaalt welke zoekinterface
    beschikbaar is.

    Mogelijkheden:

    1. Oude klassieke interface
    2. Nieuw AI-scherm -> klassieke V3-interface

    Retourneert:
        "oud" of "v3"
    """

    page.goto(
        "https://immovlan.be/nl",
        wait_until="domcontentloaded",
        timeout=PAGE_TIMEOUT,
    )

    logger.info(
        "Immovlan URL: %s",
        page.url,
    )

    logger.info(
        "Immovlan paginatitel: %s",
        page.title(),
    )

    accepteer_cookies(
        page
    )

    # -----------------------------------------------------
    # Oude klassieke interface direct beschikbaar?
    # -----------------------------------------------------
    oude_woningtype_selector = (
        page.get_by_role(
            "listbox",
            name="Wat?",
        )
    )

    try:
        oude_woningtype_selector.wait_for(
            state="visible",
            timeout=3000,
        )

        logger.info(
            "Immovlan oude klassieke "
            "zoekinterface direct beschikbaar"
        )

        return "oud"

    except PlaywrightTimeoutError:
        logger.info(
            "Immovlan oude klassieke interface "
            "niet direct zichtbaar"
        )

    # -----------------------------------------------------
    # V3-interface misschien al zichtbaar?
    # -----------------------------------------------------
    v3_woningtype = page.locator(
        "#v3-property-type"
    )

    try:
        v3_woningtype.wait_for(
            state="visible",
            timeout=2000,
        )

        logger.info(
            "Immovlan V3-zoekinterface "
            "direct beschikbaar"
        )

        return "v3"

    except PlaywrightTimeoutError:
        pass

    # -----------------------------------------------------
    # AI-scherm herkennen
    # -----------------------------------------------------
    klassieke_link = page.get_by_role(
        "link",
        name=re.compile(
            r"klassieke",
            re.IGNORECASE,
        ),
    )

    try:
        klassieke_link.wait_for(
            state="visible",
            timeout=5000,
        )

        logger.info(
            "Immovlan AI-zoekscherm gedetecteerd; "
            "overschakelen naar klassieke zoekopdracht"
        )

        klassieke_link.click()

        page.wait_for_timeout(
            1500
        )

    except PlaywrightTimeoutError:
        logger.warning(
            "Geen link naar klassieke zoekopdracht "
            "gevonden op Immovlan"
        )

    # -----------------------------------------------------
    # Na klik opnieuw interfaces controleren
    # -----------------------------------------------------
    try:
        oude_woningtype_selector.wait_for(
            state="visible",
            timeout=3000,
        )

        logger.info(
            "Immovlan oude klassieke "
            "zoekinterface beschikbaar"
        )

        return "oud"

    except PlaywrightTimeoutError:
        pass

    try:
        v3_woningtype.wait_for(
            state="visible",
            timeout=LOCATIE_TIMEOUT,
        )

        logger.info(
            "Immovlan V3-zoekinterface beschikbaar"
        )

        return "v3"

    except PlaywrightTimeoutError:
        raise RuntimeError(
            "Geen bruikbare Immovlan-zoekinterface gevonden"
        )


# =========================================================
# Plaats kiezen - oude interface
# =========================================================

def kies_plaats(
    page,
    postcode,
):
    """
    Selecteert de juiste plaats/deelgemeente
    in de oude Immovlan-interface.
    """

    postcode_regex = re.compile(
        rf".*\({re.escape(str(postcode))}\).*",
        re.IGNORECASE,
    )

    plaats_opties = page.get_by_role(
        "option",
        name=postcode_regex,
    )

    plaats_opties.first.wait_for(
        state="visible",
        timeout=LOCATIE_TIMEOUT,
    )

    aantal_opties = (
        plaats_opties.count()
    )

    gekozen_plaats = (
        plaats_opties
        .first
        .inner_text()
        .strip()
    )

    plaats_opties.first.click()

    logger.info(
        "%s Immovlan-plaatsoptie(s) gevonden "
        "voor postcode %s",
        aantal_opties,
        postcode,
    )

    logger.info(
        "Plaats '%s' automatisch geselecteerd "
        "voor postcode %s",
        gekozen_plaats,
        postcode,
    )


# =========================================================
# Oude interface
# =========================================================

def voer_oude_zoekopdracht_uit(
    page,
    postcode,
    woningtype,
    min_prijs,
    max_prijs,
):
    """
    Voert een zoekopdracht uit via de oude
    klassieke Immovlan-interface.
    """

    logger.info(
        "Immovlan gebruikt oude klassieke interface"
    )

    # -----------------------------------------------------
    # Woningtype
    # -----------------------------------------------------
    woningtype_selector = (
        page.get_by_role(
            "listbox",
            name="Wat?",
        )
    )

    woningtype_selector.click()

    if woningtype == "huis":
        page.locator(
            "#sale-form span"
        ).filter(
            has_text="Huis"
        ).click()

    else:
        raise ValueError(
            f"Woningtype '{woningtype}' is voor "
            f"Immovlan nog niet ingebouwd"
        )

    page.wait_for_timeout(
        FORMULIER_WAIT
    )

    # -----------------------------------------------------
    # Postcode
    # -----------------------------------------------------
    locatie = page.get_by_role(
        "textbox",
        name="Waar? Stad, Postcode,",
    )

    locatie.wait_for(
        state="visible",
        timeout=LOCATIE_TIMEOUT,
    )

    locatie.click()
    locatie.fill("")

    locatie.press_sequentially(
        str(postcode),
        delay=150,
    )

    page.wait_for_timeout(
        1000
    )

    kies_plaats(
        page,
        postcode,
    )

    page.wait_for_timeout(
        FORMULIER_WAIT
    )

    # -----------------------------------------------------
    # Prijs
    # -----------------------------------------------------
    page.get_by_role(
        "textbox",
        name="Prijs",
    ).click()

    page.get_by_role(
        "spinbutton",
        name="Min. prijs €",
    ).fill(
        str(min_prijs)
    )

    page.get_by_role(
        "spinbutton",
        name="Max. prijs €",
    ).fill(
        str(max_prijs)
    )

    page.wait_for_timeout(
        FORMULIER_WAIT
    )

    # -----------------------------------------------------
    # Zoeken
    # -----------------------------------------------------
    page.get_by_role(
        "button",
        name=" Zoeken in lijst",
    ).click()

    page.wait_for_load_state(
        "domcontentloaded"
    )

    page.wait_for_timeout(
        RESULTATEN_WAIT
    )


# =========================================================
# Nieuwe V3-interface
# =========================================================

def vind_v3_prijs_selector(page):
    """
    Zoekt in de V3-interface de selectbox
    met prijsklassen.
    """

    selects = page.locator(
        "select"
    )

    for i in range(
        selects.count()
    ):
        selector = selects.nth(
            i
        )

        opties = selector.locator(
            "option"
        )

        waarden = []

        for j in range(
            opties.count()
        ):
            waarde = (
                opties.nth(j)
                .get_attribute("value")
            )

            if waarde:
                waarden.append(
                    waarde
                )

        if any(
            re.fullmatch(
                r"\d+-\d+",
                waarde,
            )
            for waarde in waarden
        ):
            return selector

    # Fallback zoals Playwright Codegen
    comboboxen = page.get_by_role(
        "combobox"
    )

    if comboboxen.count() >= 3:
        return comboboxen.nth(
            2
        )

    raise RuntimeError(
        "Geen V3-prijsselector gevonden op Immovlan"
    )


def kies_v3_prijsklasse(
    page,
    max_prijs,
):
    """
    De V3-interface heeft geen aparte minimum-
    en maximumprijs.

    We kiezen daarom de kleinste beschikbare
    0-X range die groot genoeg is.

    Daarna filtert Python exact op onze
    min_prijs en max_prijs.
    """

    prijs_selector = (
        vind_v3_prijs_selector(
            page
        )
    )

    opties = prijs_selector.locator(
        "option"
    )

    kandidaten = []

    for i in range(
        opties.count()
    ):
        optie = opties.nth(
            i
        )

        waarde = optie.get_attribute(
            "value"
        )

        if not waarde:
            continue

        match = re.fullmatch(
            r"(\d+)-(\d+)",
            waarde,
        )

        if not match:
            continue

        ondergrens = int(
            match.group(1)
        )

        bovengrens = int(
            match.group(2)
        )

        if (
            ondergrens == 0
            and bovengrens >= max_prijs
        ):
            kandidaten.append(
                (
                    bovengrens,
                    waarde,
                )
            )

    if kandidaten:
        kandidaten.sort(
            key=lambda item: item[0]
        )

        gekozen_waarde = (
            kandidaten[0][1]
        )

    else:
        alle_ranges = []

        for i in range(
            opties.count()
        ):
            waarde = (
                opties.nth(i)
                .get_attribute("value")
            )

            if not waarde:
                continue

            match = re.fullmatch(
                r"0-(\d+)",
                waarde,
            )

            if match:
                alle_ranges.append(
                    (
                        int(match.group(1)),
                        waarde,
                    )
                )

        if not alle_ranges:
            raise RuntimeError(
                "Geen bruikbare prijsklasse "
                "gevonden in Immovlan V3"
            )

        alle_ranges.sort(
            reverse=True
        )

        gekozen_waarde = (
            alle_ranges[0][1]
        )

    prijs_selector.select_option(
        gekozen_waarde
    )

    logger.info(
        "Immovlan V3-prijsklasse geselecteerd: %s",
        gekozen_waarde,
    )


def voer_v3_zoekopdracht_uit(
    page,
    postcode,
    woningtype,
    min_prijs,
    max_prijs,
):
    """
    Voert de zoekopdracht uit via de nieuwe
    klassieke V3-interface.
    """

    logger.info(
        "Immovlan gebruikt nieuwe V3-interface"
    )

    # -----------------------------------------------------
    # Woningtype
    # -----------------------------------------------------
    woningtype_selector = (
        page.locator(
            "#v3-property-type"
        )
    )

    woningtype_selector.wait_for(
        state="visible",
        timeout=LOCATIE_TIMEOUT,
    )

    if woningtype == "huis":
        woningtype_selector.select_option(
            "huis"
        )

    else:
        raise ValueError(
            f"Woningtype '{woningtype}' is voor "
            f"Immovlan V3 nog niet ingebouwd"
        )

    logger.info(
        "Immovlan V3 woningtype 'huis' geselecteerd"
    )

    page.wait_for_timeout(
        FORMULIER_WAIT
    )

    # -----------------------------------------------------
    # Postcode
    # -----------------------------------------------------
    locatie = page.get_by_role(
        "combobox",
        name=re.compile(
            r"Stad,\s*postcode,\s*provincie\s*of",
            re.IGNORECASE,
        ),
    )

    locatie.wait_for(
        state="visible",
        timeout=LOCATIE_TIMEOUT,
    )

    locatie.click()
    locatie.fill("")

    locatie.press_sequentially(
        str(postcode),
        delay=150,
    )

    page.wait_for_timeout(
        1500
    )

    # -----------------------------------------------------
    # Bovenste V3-locatiesuggestie selecteren
    # -----------------------------------------------------
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
        "Immovlan V3 bovenste locatiesuggestie "
        "geselecteerd voor postcode %s",
        postcode,
    )

    # -----------------------------------------------------
    # Prijsklasse
    # -----------------------------------------------------
    kies_v3_prijsklasse(
        page,
        max_prijs,
    )

    page.wait_for_timeout(
        FORMULIER_WAIT
    )

    # -----------------------------------------------------
    # Zoeken
    # -----------------------------------------------------
    zoek_knop = page.get_by_role(
        "button",
        name=re.compile(
            r"Zoeken",
            re.IGNORECASE,
        ),
    )

    zoek_knop.click()

    page.wait_for_load_state(
        "domcontentloaded"
    )

    page.wait_for_timeout(
        RESULTATEN_WAIT
    )


# =========================================================
# Snelle directe resultaten-URL
# =========================================================

def voer_directe_zoekopdracht_uit(
    page,
    postcode,
    woningtype,
    min_prijs,
    max_prijs,
):
    """
    Opent voor gevalideerde postcodes rechtstreeks de
    Immovlan-resultatenpagina.

    Bij een technische fout gooit deze functie de fout door,
    zodat zoek_immovlan automatisch kan terugvallen op de
    bestaande formuliermethode.
    """

    postcode = str(postcode)

    if woningtype != "huis":
        raise ValueError(
            f"Woningtype '{woningtype}' is voor "
            f"Immovlan direct nog niet ingebouwd"
        )

    municipal = IMMOVLAN_DIRECT_VEILIG.get(postcode)

    if not municipal:
        raise ValueError(
            f"Geen gevalideerde directe Immovlan-route "
            f"voor postcode {postcode}"
        )

    url = (
        "https://immovlan.be/nl/vastgoed"
        "?transactiontypes=te-koop,in-openbare-verkoop"
        "&propertytypes=huis"
        f"&municipals={municipal}"
        f"&minprice={min_prijs}"
        f"&maxprice={max_prijs}"
        "&noindex=1"
    )

    logger.info(
        "Immovlan snelle directe route voor postcode %s: %s",
        postcode,
        url,
    )

    page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=PAGE_TIMEOUT,
    )

    # Bewust geen vaste RESULTATEN_WAIT: bij de gevalideerde
    # directe route zijn de article-kaarten na DOMContentLoaded
    # al beschikbaar. Wel kort wachten als de pagina ze nog
    # asynchroon toevoegt.
    try:
        page.locator("article").first.wait_for(
            state="attached",
            timeout=3000,
        )
    except PlaywrightTimeoutError:
        # Nul resultaten is een geldige uitkomst. Daarom niet
        # automatisch als fout behandelen.
        logger.info(
            "Immovlan directe route postcode %s: "
            "geen article-element binnen 3 seconden",
            postcode,
        )

    logger.info(
        "Immovlan directe resultatenpagina geopend: %s",
        page.url,
    )


# =========================================================
# Zoekopdracht routeren
# =========================================================

def voer_zoekopdracht_uit(
    page,
    postcode,
    woningtype,
    min_prijs,
    max_prijs,
):
    """
    Herkent automatisch welke Immovlan-interface actief is
    en gebruikt de juiste zoekmethode.
    """

    interface = open_startpagina(
        page
    )

    logger.info(
        "Immovlan interface gedetecteerd: %s",
        interface,
    )

    if interface == "oud":
        voer_oude_zoekopdracht_uit(
            page,
            postcode,
            woningtype,
            min_prijs,
            max_prijs,
        )

    elif interface == "v3":
        voer_v3_zoekopdracht_uit(
            page,
            postcode,
            woningtype,
            min_prijs,
            max_prijs,
        )

    else:
        raise RuntimeError(
            f"Onbekende Immovlan-interface: {interface}"
        )

    logger.info(
        "Immovlan resultatenpagina geopend: %s",
        page.url,
    )


# =========================================================
# Hoofdfunctie
# =========================================================

def zoek_immovlan(
    postcode,
    woningtype,
    min_prijs,
    max_prijs,
    csv_bestand,
):
    logger.info(
        "Zoeken op Immovlan gestart: "
        "postcode=%s, woningtype=%s",
        postcode,
        woningtype,
    )

    resultaten = []
    nieuw = []

    # ---------------------------------------------------------
    # Performance-meting
    # ---------------------------------------------------------
    perf_start = time.perf_counter()
    perf_browser_start = None
    perf_zoeken_start = None
    perf_uitlezen_start = None
    perf_csv_start = None

    try:
        perf_browser_start = time.perf_counter()

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=HEADLESS,
                slow_mo=0 if HEADLESS else SLOW_MO,
                args=[
                    "--deny-permission-prompts",
                ],
            )

            try:
                page = browser.new_page()

                perf_zoeken_start = time.perf_counter()

                zoekopdracht_gelukt = False

                # -------------------------------------------------
                # Hele zoekactie maximaal drie keer proberen
                # -------------------------------------------------
                for poging in range(
                    1,
                    MAX_POGINGEN + 1,
                ):
                    try:
                        logger.info(
                            "Immovlan poging %s van %s "
                            "voor postcode %s",
                            poging,
                            MAX_POGINGEN,
                            postcode,
                        )

                        postcode_str = str(postcode)

                        if postcode_str in IMMOVLAN_DIRECT_VEILIG:
                            try:
                                voer_directe_zoekopdracht_uit(
                                    page,
                                    postcode_str,
                                    woningtype,
                                    min_prijs,
                                    max_prijs,
                                )

                            except Exception:
                                logger.exception(
                                    "Immovlan snelle directe route "
                                    "mislukt voor postcode %s; "
                                    "automatische fallback naar "
                                    "normale formulierroute",
                                    postcode_str,
                                )

                                try:
                                    page.close()
                                except Exception:
                                    pass

                                page = browser.new_page()

                                voer_zoekopdracht_uit(
                                    page,
                                    postcode_str,
                                    woningtype,
                                    min_prijs,
                                    max_prijs,
                                )

                        else:
                            logger.info(
                                "Immovlan normale fallback-route "
                                "voor postcode %s",
                                postcode_str,
                            )

                            voer_zoekopdracht_uit(
                                page,
                                postcode_str,
                                woningtype,
                                min_prijs,
                                max_prijs,
                            )

                        zoekopdracht_gelukt = True

                        break

                    except Exception:
                        logger.exception(
                            "Immovlan poging %s mislukt "
                            "voor postcode %s",
                            poging,
                            postcode,
                        )

                        if poging >= MAX_POGINGEN:
                            raise

                        volgende_poging = (
                            poging + 1
                        )

                        logger.warning(
                            "Nieuwe browserpagina wordt geopend "
                            "voor Immovlan poging %s "
                            "voor postcode %s",
                            volgende_poging,
                            postcode,
                        )

                        try:
                            page.close()

                        except Exception:
                            pass

                        page = browser.new_page()

                        wachttijd = (
                            3000 * poging
                        )

                        logger.info(
                            "Wachten %s ms voordat Immovlan "
                            "opnieuw wordt geprobeerd",
                            wachttijd,
                        )

                        page.wait_for_timeout(
                            wachttijd
                        )

                if not zoekopdracht_gelukt:
                    raise RuntimeError(
                        f"Immovlan zoekopdracht voor "
                        f"postcode {postcode} is niet gelukt"
                    )

                # -------------------------------------------------
                # Resultatenkaarten
                # -------------------------------------------------
                perf_uitlezen_start = time.perf_counter()

                cards = page.locator(
                    "article"
                )

                aantal_cards = (
                    cards.count()
                )

                logger.info(
                    "%s article-elementen gevonden "
                    "op Immovlan",
                    aantal_cards,
                )

                aantal_buiten_prijs = 0

                for i in range(
                    aantal_cards
                ):
                    card = cards.nth(
                        i
                    )

                    try:
                        tekst = (
                            card.inner_text().strip()
                        )

                        if not tekst:
                            continue

                        regels = [
                            regel.strip()
                            for regel in tekst.splitlines()
                            if regel.strip()
                        ]

                        if len(regels) < 3:
                            continue

                        prijs = regels[0]
                        titel = regels[1]
                        plaats = regels[2]

                        # -----------------------------------------
                        # Prijs
                        # -----------------------------------------
                        prijs_getal = (
                            prijs_naar_getal(
                                prijs
                            )
                        )

                        if prijs_getal is None:
                            continue

                        if not (
                            min_prijs
                            <= prijs_getal
                            <= max_prijs
                        ):
                            aantal_buiten_prijs += 1

                            continue

                        # -----------------------------------------
                        # Slaapkamers
                        # -----------------------------------------
                        slaapkamers_match = re.search(
                            r"(\d+)\s+slaapkamer\(s\)",
                            tekst,
                            re.IGNORECASE,
                        )

                        slaapkamers = (
                            slaapkamers_match.group(1)
                            if slaapkamers_match
                            else "Onbekend"
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
                        # Hoofdfoto
                        # -----------------------------------------
                        foto = haal_foto_url_immovlan(
                            card
                        )

                        if foto:
                            logger.info(
                                "Immovlan foto gevonden "
                                "voor woning %s",
                                i,
                            )

                        else:
                            logger.info(
                                "Geen Immovlan foto gevonden "
                                "voor woning %s",
                                i,
                            )

                        # -----------------------------------------
                        # Detail-link
                        # -----------------------------------------
                        details = card.get_by_text(
                            "Details",
                            exact=True,
                        )

                        if details.count() == 0:
                            logger.warning(
                                "Geen Details-link gevonden "
                                "voor Immovlan card %s",
                                i,
                            )

                            continue

                        link = (
                            details
                            .first
                            .get_attribute(
                                "href"
                            )
                        )

                        if not link:
                            logger.warning(
                                "Lege Details-link gevonden "
                                "voor Immovlan card %s",
                                i,
                            )

                            continue

                        resultaten.append({
                            "titel": titel,
                            "prijs": prijs,
                            "slaapkamers": slaapkamers,
                            "oppervlakte": oppervlakte,
                            "plaats": plaats,
                            "link": link,
                            "foto": foto,
                            "bron": "Immovlan",
                        })

                    except Exception:
                        logger.exception(
                            "Immovlan woning %s kon niet "
                            "worden uitgelezen",
                            i,
                        )

                logger.info(
                    "Immovlan postcode %s: "
                    "%s kaarten bekeken, "
                    "%s buiten prijsrange, "
                    "%s passende woningen",
                    postcode,
                    aantal_cards,
                    aantal_buiten_prijs,
                    len(resultaten),
                )

                logger.info(
                    "%s woningen succesvol uitgelezen "
                    "van Immovlan voor postcode %s",
                    len(resultaten),
                    postcode,
                )

                print(
                    f"Immovlan: "
                    f"{len(resultaten)} "
                    f"woningen uitgelezen"
                )

                # -------------------------------------------------
                # Nieuwe woningen bepalen
                # -------------------------------------------------
                perf_csv_start = time.perf_counter()

                nieuw = nieuwe_woningen(
                    resultaten,
                    csv_bestand=csv_bestand,
                )

                logger.info(
                    "%s nieuwe Immovlan-woningen gevonden "
                    "voor postcode %s",
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
                    "Immovlan CSV-bestand '%s' bijgewerkt",
                    csv_bestand,
                )

                perf_einde = time.perf_counter()

                browser_tijd = (
                    perf_zoeken_start
                    - perf_browser_start
                )

                zoeken_tijd = (
                    perf_uitlezen_start
                    - perf_zoeken_start
                )

                uitlezen_tijd = (
                    perf_csv_start
                    - perf_uitlezen_start
                )

                csv_tijd = (
                    perf_einde
                    - perf_csv_start
                )

                totaal_tijd = (
                    perf_einde
                    - perf_start
                )

                logger.info(
                    "-" * 60
                )

                logger.info(
                    "IMMOVLAN PERFORMANCE postcode %s",
                    postcode,
                )

                logger.info(
                    "Browser starten              : %.2f seconden",
                    browser_tijd,
                )

                logger.info(
                    "Startpagina + zoeken         : %.2f seconden",
                    zoeken_tijd,
                )

                logger.info(
                    "Resultaatkaarten uitlezen    : %.2f seconden",
                    uitlezen_tijd,
                )

                logger.info(
                    "CSV + vergelijking           : %.2f seconden",
                    csv_tijd,
                )

                logger.info(
                    "Totaal gemeten               : %.2f seconden",
                    totaal_tijd,
                )

                logger.info(
                    "-" * 60
                )

            finally:
                browser.close()

                logger.info(
                    "Immovlan-browser gesloten "
                    "voor postcode %s",
                    postcode,
                )

    except Exception:
        logger.exception(
            "Immovlan-zoekopdracht voor postcode %s "
            "is definitief mislukt",
            postcode,
        )

        raise

    return nieuw
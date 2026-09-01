"""
bienici.py

Bronmodule Bien'ici voor Huizenzoeker Frankrijk.

Huidige status:
- zoekfunctie voor Bien'ici;
- detailparser voor AI Huizencoach;
- Playwright voor gerenderde pagina's;
- BeautifulSoup voor parsing;
- CSV/historie via bestaande Huizenzoeker-componenten.

Belangrijk:
De directe zoekroute is op dit moment technisch gevalideerd voor:
    08600 -> Givet

Andere postcodes worden bewust nog niet gegokt.
Die voegen we later gecontroleerd toe.
"""

from __future__ import annotations

import json
import os
import re
import time
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

from csv_opslaan import opslaan_csv
from logger import logger
from vergelijk import nieuwe_woningen


# ============================================================
# CONFIGURATIE
# ============================================================

BASE_URL = "https://www.bienici.com"

PAGE_TIMEOUT = 45_000
RESULTATEN_TIMEOUT = 20_000
RESULTATEN_WAIT = 2_000

# Lokaal zichtbaar, in GitHub Actions headless.
HEADLESS = (
    os.getenv(
        "CI",
        "",
    ).lower()
    == "true"
)

SLOW_MO = (
    0
    if HEADLESS
    else 100
)


# ============================================================
# GEVALIDEERDE DIRECTE ROUTES
# ============================================================

BIENICI_DIRECTE_ROUTES = {
    "08600": "givet",
}


# ============================================================
# ALGEMENE HELPERS
# ============================================================

def normale_tekst(
    tekst,
):
    """
    Normaliseert HTML-tekst.
    """

    if tekst is None:
        return ""

    tekst = str(
        tekst
    )

    tekst = tekst.replace(
        "\xa0",
        " ",
    )

    tekst = tekst.replace(
        "\u202f",
        " ",
    )

    tekst = re.sub(
        r"\s+",
        " ",
        tekst,
    )

    return tekst.strip()


def prijs_naar_getal(
    waarde,
):
    """
    Zet prijs om naar integer.

    Voorbeelden:

        "212 000 €" -> 212000
        "€ 212.000" -> 212000
    """

    if waarde is None:
        return None

    cijfers = re.findall(
        r"\d+",
        str(
            waarde
        ),
    )

    if not cijfers:
        return None

    try:
        return int(
            "".join(
                cijfers
            )
        )

    except ValueError:
        return None


def prijs_naar_tekst(
    prijs,
):
    """
    212000 -> € 212.000
    """

    if prijs is None:
        return "Onbekend"

    return (
        f"€ {prijs:,}"
        .replace(
            ",",
            ".",
        )
    )


def eerste_getal(
    tekst,
):
    """
    Geeft eerste plausibele integer uit tekst.
    """

    if not tekst:
        return None

    match = re.search(
        r"(\d[\d\s.]*)",
        tekst,
    )

    if not match:
        return None

    waarde = (
        match.group(1)
        .replace(
            " ",
            "",
        )
        .replace(
            ".",
            "",
        )
    )

    try:
        return int(
            waarde
        )

    except ValueError:
        return None


def normaliseer_foto_url(
    url,
):
    """
    Verwijdert resize-queryparameters uit een
    Bien'ici foto-URL.
    """

    if not url:
        return None

    url = (
        str(url)
        .replace(
            "&amp;",
            "&",
        )
        .strip()
    )

    delen = urlsplit(
        url
    )

    return urlunsplit(
        (
            delen.scheme,
            delen.netloc,
            delen.path,
            "",
            "",
        )
    )


# ============================================================
# ZOEK-URL
# ============================================================

def maak_zoek_url(
    postcode,
    woningtype,
):
    """
    Bouwt een gevalideerde directe Bien'ici zoek-URL.

    Momenteel:
        08600 -> Givet

    Andere postcodes worden nog niet automatisch gegokt.
    """

    postcode = str(
        postcode
    ).strip()

    woningtype = str(
        woningtype
    ).strip().lower()

    if woningtype != "huis":
        raise ValueError(
            "Bien'ici ondersteunt momenteel alleen "
            f"woningtype 'huis', niet '{woningtype}'"
        )

    plaats_slug = (
        BIENICI_DIRECTE_ROUTES.get(
            postcode
        )
    )

    if not plaats_slug:
        raise ValueError(
            "Nog geen gevalideerde Bien'ici-route "
            f"voor postcode {postcode}"
        )

    return (
        f"{BASE_URL}/recherche/achat/"
        f"{plaats_slug}-{postcode}/maisonvilla"
    )


# ============================================================
# COOKIES
# ============================================================

def accepteer_cookies(
    page,
):
    """
    Accepteert indien zichtbaar de Bien'ici cookie-popup.

    Retourneert True als een knop is aangeklikt.
    """

    patronen = [
        r"^ACCEPTER$",
        r"^Accepter$",
        r"^Tout accepter$",
        r"^Accepter tout$",
        r"^J'accepte$",
        r"^OK$",
    ]

    for patroon in patronen:

        locator = page.get_by_text(
            re.compile(
                patroon,
                re.IGNORECASE,
            ),
            exact=True,
        )

        try:

            if locator.count() == 0:
                continue

            if not locator.first.is_visible():
                continue

            logger.info(
                "Bien'ici cookieknop gevonden: %s",
                normale_tekst(
                    locator.first.inner_text()
                ),
            )

            locator.first.click(
                timeout=5000
            )

            page.wait_for_timeout(
                750
            )

            logger.info(
                "Bien'ici cookies geaccepteerd"
            )

            return True

        except Exception:

            continue

    logger.info(
        "Bien'ici: geen actieve cookie-popup gevonden"
    )

    return False


# ============================================================
# BROWSER HTML OPHALEN
# ============================================================

def haal_html_op(
    url,
    wacht_op_resultaten=False,
):
    """
    Opent een Bien'ici pagina met Playwright
    en retourneert de gerenderde HTML.
    """

    logger.info(
        "Bien'ici opent pagina met Playwright: %s",
        url,
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=HEADLESS,
            slow_mo=SLOW_MO,
        )

        context = browser.new_context(
            locale="fr-FR",
            viewport={
                "width": 1440,
                "height": 1000,
            },
        )

        page = context.new_page()

        page.set_default_timeout(
            PAGE_TIMEOUT
        )

        try:

            response = page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=PAGE_TIMEOUT,
            )

            status = (
                response.status
                if response is not None
                else None
            )

            logger.info(
                "Bien'ici HTTP-status: %s",
                status,
            )

            if (
                status is not None
                and status >= 400
            ):
                raise RuntimeError(
                    f"Bien'ici HTTP-status {status}"
                )

            page.wait_for_timeout(
                750
            )

            accepteer_cookies(
                page
            )

            if wacht_op_resultaten:

                try:

                    page.locator(
                        "article[data-id]"
                    ).first.wait_for(
                        state="attached",
                        timeout=RESULTATEN_TIMEOUT,
                    )

                except PlaywrightTimeoutError:

                    logger.warning(
                        "Bien'ici resultaatkaart niet "
                        "binnen timeout gevonden"
                    )

            else:

                try:

                    page.locator(
                        "section.description"
                    ).wait_for(
                        state="attached",
                        timeout=RESULTATEN_TIMEOUT,
                    )

                except PlaywrightTimeoutError:

                    logger.warning(
                        "Bien'ici detailsectie niet "
                        "binnen timeout gevonden"
                    )

            page.wait_for_timeout(
                RESULTATEN_WAIT
            )

            titel = page.title()

            html = page.content()

            logger.info(
                "Bien'ici paginatitel: %s",
                titel,
            )

            logger.info(
                "Bien'ici gerenderde HTML: %s tekens",
                len(
                    html
                ),
            )

            if len(html) < 20_000:

                raise RuntimeError(
                    "Bien'ici leverde onverwacht weinig HTML op"
                )

            return html

        finally:

            context.close()
            browser.close()

            logger.info(
                "Bien'ici browser gesloten"
            )


# ============================================================
# RESULTAATKAARTEN
# ============================================================

def zoek_unieke_kaarten(
    soup,
):
    """
    Bien'ici gebruikt:

        <article data-id="...">

    Promoted advertenties kunnen later opnieuw
    in de gewone resultatenlijst staan.

    Daarom dedupliceren we op data-id.
    """

    unieke_kaarten = {}

    artikelen = soup.find_all(
        "article",
        attrs={
            "data-id": True,
        },
    )

    for artikel in artikelen:

        advertentie_id = artikel.get(
            "data-id"
        )

        if not advertentie_id:
            continue

        link = artikel.find(
            "a",
            class_="detailedSheetLink",
        )

        if link is None:
            continue

        unieke_kaarten.setdefault(
            advertentie_id,
            artikel,
        )

    return unieke_kaarten


def haal_url_uit_kaart(
    kaart,
):
    link = kaart.find(
        "a",
        class_="detailedSheetLink",
    )

    if link is None:
        return None

    href = link.get(
        "href"
    )

    if not href:
        return None

    # Zoekparameters verwijderen.
    href = href.split(
        "?",
        1,
    )[0]

    return urljoin(
        BASE_URL,
        href,
    )


def haal_titel_uit_kaart(
    kaart,
):
    element = kaart.select_one(
        ".real-estate-main-info__title"
    )

    if element is None:
        return "Onbekend"

    return normale_tekst(
        element.get_text(
            " ",
            strip=True,
        )
    )


def haal_adres_uit_kaart(
    kaart,
):
    element = kaart.select_one(
        ".real-estate-main-info__address"
    )

    if element is None:
        return (
            None,
            None,
        )

    tekst = normale_tekst(
        element.get_text(
            " ",
            strip=True,
        )
    )

    match = re.search(
        r"\b(\d{5})\s+(.+)$",
        tekst,
    )

    if not match:
        return (
            None,
            None,
        )

    return (
        match.group(1),
        match.group(2).strip(),
    )


def haal_prijs_uit_kaart(
    kaart,
):
    element = kaart.select_one(
        ".ad-price__the-price"
    )

    if element is None:
        return None

    return prijs_naar_getal(
        element.get_text(
            " ",
            strip=True,
        )
    )


def haal_woonoppervlakte_uit_kaart(
    kaart,
):
    titel = haal_titel_uit_kaart(
        kaart
    )

    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*m²",
        titel,
        re.IGNORECASE,
    )

    if not match:
        return None

    waarde = (
        match.group(1)
        .replace(
            ",",
            ".",
        )
    )

    try:

        getal = float(
            waarde
        )

        if getal.is_integer():
            return int(
                getal
            )

        return getal

    except ValueError:

        return None


def haal_omschrijving_uit_kaart(
    kaart,
):
    element = kaart.select_one(
        ".ad-overview-description"
    )

    if element is None:
        return ""

    return normale_tekst(
        element.get_text(
            " ",
            strip=True,
        )
    )


def haal_slaapkamers_uit_kaart(
    kaart,
):
    """
    Slaapkamers staan niet altijd in de kaarttitel.

    Daarom proberen we de verborgen omschrijving.
    """

    tekst = haal_omschrijving_uit_kaart(
        kaart
    )

    patronen = [
        r"(\d+)\s+chambres?",
        r"(\d+)\s+chambre\(s\)",
    ]

    for patroon in patronen:

        match = re.search(
            patroon,
            tekst,
            re.IGNORECASE,
        )

        if match:
            return match.group(1)

    return "Onbekend"


def haal_terrain_uit_kaart(
    kaart,
):
    """
    Alleen wanneer expliciet genoemd.

    Anders leeg laten; niet gokken.
    """

    tekst = haal_omschrijving_uit_kaart(
        kaart
    )

    patronen = [
        r"terrain\s+de\s+(\d+)\s*m²",
        r"terrain\s+d['’]environ\s+(\d+)\s*m²",
        r"parcelle\s+de\s+(\d+)\s*m²",
        r"parcelle\s+d['’]environ\s+(\d+)\s*m²",
        r"sur\s+un\s+terrain\s+de\s+(\d+)\s*m²",
    ]

    for patroon in patronen:

        match = re.search(
            patroon,
            tekst,
            re.IGNORECASE,
        )

        if match:
            return match.group(1)

    return ""


def haal_foto_uit_kaart(
    kaart,
):
    afbeelding = kaart.select_one(
        ".ad-overview-photo__image img"
    )

    if afbeelding is None:
        return ""

    src = afbeelding.get(
        "src"
    )

    if not src:
        return ""

    return src.strip()


# ============================================================
# ZOEKFUNCTIE
# ============================================================

def zoek_bienici(
    postcode,
    woningtype,
    min_prijs,
    max_prijs,
    csv_bestand,
):
    """
    Zoekfunctie volgens het Huizenzoeker-contract.

    Retourneert alleen nieuwe woningen.
    """

    logger.info(
        "Zoeken op Bien'ici gestart: "
        "postcode=%s, woningtype=%s",
        postcode,
        woningtype,
    )

    start_tijd = time.perf_counter()

    zoek_url = maak_zoek_url(
        postcode,
        woningtype,
    )

    logger.info(
        "Bien'ici zoek-URL: %s",
        zoek_url,
    )

    html = haal_html_op(
        zoek_url,
        wacht_op_resultaten=True,
    )

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    kaarten = zoek_unieke_kaarten(
        soup
    )

    logger.info(
        "Bien'ici unieke resultaatkaarten: %s",
        len(
            kaarten
        ),
    )

    resultaten = []

    aantal_buiten_prijs = 0
    aantal_fouten = 0

    for nummer, (
        advertentie_id,
        kaart,
    ) in enumerate(
        kaarten.items(),
        start=1,
    ):

        try:

            prijs_getal = (
                haal_prijs_uit_kaart(
                    kaart
                )
            )

            if prijs_getal is None:

                logger.warning(
                    "Bien'ici kaart %s heeft geen prijs",
                    advertentie_id,
                )

                continue

            if not (
                min_prijs
                <= prijs_getal
                <= max_prijs
            ):

                aantal_buiten_prijs += 1

                continue

            postcode_kaart, plaats = (
                haal_adres_uit_kaart(
                    kaart
                )
            )

            link = haal_url_uit_kaart(
                kaart
            )

            if not link:

                logger.warning(
                    "Bien'ici kaart %s heeft geen detail-URL",
                    advertentie_id,
                )

                continue

            titel = haal_titel_uit_kaart(
                kaart
            )

            oppervlakte = (
                haal_woonoppervlakte_uit_kaart(
                    kaart
                )
            )

            slaapkamers = (
                haal_slaapkamers_uit_kaart(
                    kaart
                )
            )

            perceel = (
                haal_terrain_uit_kaart(
                    kaart
                )
            )

            foto = haal_foto_uit_kaart(
                kaart
            )

            woning = {
                "titel": titel,
                "prijs": prijs_naar_tekst(
                    prijs_getal
                ),
                "slaapkamers": slaapkamers,
                "oppervlakte": (
                    str(
                        oppervlakte
                    )
                    if oppervlakte is not None
                    else "Onbekend"
                ),
                "perceeloppervlakte": perceel,
                "plaats": (
                    plaats
                    if plaats
                    else "Onbekend"
                ),
                "link": link,
                "foto": foto,
                "bron": "Bien'ici",
                "bron_sleutel": "bienici",
            }

            resultaten.append(
                woning
            )

            logger.info(
                "Bien'ici woning gevonden: "
                "%s | %s | %s",
                woning["prijs"],
                woning["plaats"],
                woning["link"],
            )

        except Exception:

            aantal_fouten += 1

            logger.exception(
                "Bien'ici woningkaart %s kon niet "
                "worden verwerkt",
                nummer,
            )

    logger.info(
        "Bien'ici postcode %s: "
        "%s unieke kaarten, "
        "%s buiten prijsrange, "
        "%s kaartfouten, "
        "%s passende woningen",
        postcode,
        len(
            kaarten
        ),
        aantal_buiten_prijs,
        aantal_fouten,
        len(
            resultaten
        ),
    )

    print(
        f"Bien'ici: "
        f"{len(resultaten)} woningen uitgelezen"
    )

    # ========================================================
    # NIEUWE WONINGEN
    # ========================================================

    nieuw = nieuwe_woningen(
        resultaten,
        csv_bestand=csv_bestand,
    )

    logger.info(
        "%s nieuwe Bien'ici-woningen gevonden "
        "voor postcode %s",
        len(
            nieuw
        ),
        postcode,
    )

    # ========================================================
    # CSV
    # ========================================================

    opslaan_csv(
        resultaten,
        bestandsnaam=csv_bestand,
    )

    logger.info(
        "Bien'ici CSV-bestand '%s' bijgewerkt",
        csv_bestand,
    )

    looptijd = (
        time.perf_counter()
        - start_tijd
    )

    logger.info(
        "Bien'ici zoekopdracht afgerond "
        "voor postcode %s in %.2f seconden",
        postcode,
        looptijd,
    )

    return nieuw


# ============================================================
# JSON-LD
# ============================================================

def lees_json_ld(
    soup,
):
    objecten = []

    for script in soup.find_all(
        "script",
        type="application/ld+json",
    ):

        inhoud = script.string

        if not inhoud:
            continue

        try:

            data = json.loads(
                inhoud
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):

            continue

        if isinstance(
            data,
            list,
        ):

            objecten.extend(
                data
            )

        elif isinstance(
            data,
            dict,
        ):

            objecten.append(
                data
            )

    return objecten

# ============================================================
# DETAILPARSER
# ============================================================

def parse_bienici_detail(
    html,
):
    """
    Parseert de HTML van één Bien'ici-detailpagina.

    Belangrijk:
    - ontbrekende gegevens blijven None;
    - True betekent expliciet aanwezig;
    - False betekent expliciet afwezig;
    - er worden geen woningkenmerken gegokt.
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    resultaat = {
        "titel": None,
        "prijs": None,
        "plaats": None,
        "postcode": None,
        "woonoppervlakte": None,
        "perceeloppervlakte": None,
        "kamers": None,
        "slaapkamers": None,
        "badkamers": None,
        "wc": None,
        "bouwjaar": None,

        "staat": None,
        "renovatiestatus": None,
        "verwarming": None,

        "dpe_klasse": None,
        "dpe_verbruik": None,
        "ges_klasse": None,
        "ges_uitstoot": None,

        "garage": None,
        "schuur": None,
        "dependances": None,
        "assainissement": None,
        "tuin": None,
        "terras": None,
        "parking": None,

        "omschrijving": None,

        "foto_url": None,
        "aantal_fotos": 0,
        "fotos": [],
    }

    # ========================================================
    # TITEL
    # ========================================================

    h1 = soup.find(
        "h1"
    )

    if h1:

        resultaat["titel"] = normale_tekst(
            h1.get_text(
                " ",
                strip=True,
            )
        )

    elif soup.title:

        resultaat["titel"] = normale_tekst(
            soup.title.get_text(
                " ",
                strip=True,
            )
        )

    # ========================================================
    # STRUCTURELE WONINGDETAILS
    # ========================================================

    details_section = soup.select_one(
        "section.detailsSection_aboutThisProperty"
    )

    detailregels = []

    if details_section:

        detail_elementen = details_section.select(
            ".labelInfo"
        )

        detailregels = [
            normale_tekst(
                element.get_text(
                    " ",
                    strip=True,
                )
            )
            for element in detail_elementen
        ]

        detailregels = [
            regel
            for regel in detailregels
            if regel
        ]

        for regel in detailregels:

            regel_lower = regel.lower()

            # ------------------------------------------------
            # PRIJS
            # ------------------------------------------------

            if regel_lower.startswith(
                "prix"
            ):

                resultaat["prijs"] = (
                    eerste_getal(
                        regel
                    )
                )

            # ------------------------------------------------
            # PERCEELOPPERVLAKTE
            # ------------------------------------------------

            elif (
                "m² de terrain"
                in regel_lower
            ):

                resultaat[
                    "perceeloppervlakte"
                ] = eerste_getal(
                    regel
                )

            # ------------------------------------------------
            # WOONOPPERVLAKTE
            #
            # Bijvoorbeeld:
            # 92 m²
            # ------------------------------------------------

            elif re.fullmatch(
                r"[\d\s.,]+\s*m²",
                regel_lower,
            ):

                resultaat[
                    "woonoppervlakte"
                ] = eerste_getal(
                    regel
                )

            # ------------------------------------------------
            # KAMERS
            # ------------------------------------------------

            elif "pièce" in regel_lower:

                resultaat[
                    "kamers"
                ] = eerste_getal(
                    regel
                )

            # ------------------------------------------------
            # SLAAPKAMERS
            # ------------------------------------------------

            elif "chambre" in regel_lower:

                resultaat[
                    "slaapkamers"
                ] = eerste_getal(
                    regel
                )

            # ------------------------------------------------
            # BADKAMERS
            # ------------------------------------------------

            elif (
                "salle de bain"
                in regel_lower
            ):

                resultaat[
                    "badkamers"
                ] = eerste_getal(
                    regel
                )

            # ------------------------------------------------
            # WC
            # ------------------------------------------------

            elif re.search(
                r"\bwc\b",
                regel_lower,
            ):

                resultaat[
                    "wc"
                ] = eerste_getal(
                    regel
                )

            # ------------------------------------------------
            # BOUWJAAR
            # ------------------------------------------------

            elif (
                "construit en"
                in regel_lower
            ):

                resultaat[
                    "bouwjaar"
                ] = eerste_getal(
                    regel
                )

            # ------------------------------------------------
            # VERWARMING
            # ------------------------------------------------

            elif regel_lower.startswith(
                "chauffage"
            ):

                delen = regel.split(
                    ":",
                    1,
                )

                if len(delen) == 2:

                    resultaat[
                        "verwarming"
                    ] = normale_tekst(
                        delen[1]
                    )

            # ------------------------------------------------
            # EXPLICIETE KENMERKEN
            # ------------------------------------------------

            if regel_lower == "jardin":

                resultaat[
                    "tuin"
                ] = True

            if regel_lower == "terrasse":

                resultaat[
                    "terras"
                ] = True

            if (
                "place de parking"
                in regel_lower
                or
                "places de parking"
                in regel_lower
            ):

                resultaat[
                    "parking"
                ] = True

            if (
                regel_lower == "garage"
                or
                regel_lower.startswith(
                    "garage "
                )
            ):

                resultaat[
                    "garage"
                ] = True

            if (
                "dépendance"
                in regel_lower
                or
                "dependance"
                in regel_lower
            ):

                resultaat[
                    "dependances"
                ] = True

            if (
                "grange"
                in regel_lower
            ):

                resultaat[
                    "schuur"
                ] = True

    # ========================================================
    # OMSCHRIJVING
    # ========================================================

    description_section = soup.select_one(
        "section.description"
    )

    if description_section:

        content = description_section.select_one(
            ".see-more-description__content"
        )

        if content:

            resultaat[
                "omschrijving"
            ] = normale_tekst(
                content.get_text(
                    " ",
                    strip=True,
                )
            )

    omschrijving_lower = (
        resultaat.get(
            "omschrijving"
        )
        or ""
    ).lower()

    # ========================================================
    # PLAATS + POSTCODE + JSON-LD FALLBACK
    # ========================================================

    json_ld = lees_json_ld(
        soup
    )

    for item in json_ld:

        if not isinstance(
            item,
            dict,
        ):
            continue

        # ----------------------------------------------------
        # Accommodation
        # ----------------------------------------------------

        if (
            item.get(
                "@type"
            )
            == "Accommodation"
        ):

            adres = item.get(
                "address",
                {},
            )

            if isinstance(
                adres,
                dict,
            ):

                resultaat[
                    "plaats"
                ] = (
                    resultaat[
                        "plaats"
                    ]
                    or
                    adres.get(
                        "addressLocality"
                    )
                )

                resultaat[
                    "postcode"
                ] = (
                    resultaat[
                        "postcode"
                    ]
                    or
                    adres.get(
                        "postalCode"
                    )
                )

            floor_size = item.get(
                "floorSize"
            )

            if (
                resultaat[
                    "woonoppervlakte"
                ]
                is None
                and isinstance(
                    floor_size,
                    dict,
                )
            ):

                resultaat[
                    "woonoppervlakte"
                ] = floor_size.get(
                    "value"
                )

            if (
                resultaat[
                    "kamers"
                ]
                is None
            ):

                resultaat[
                    "kamers"
                ] = item.get(
                    "numberOfRooms"
                )

        # ----------------------------------------------------
        # Product
        # ----------------------------------------------------

        if (
            item.get(
                "@type"
            )
            == "Product"
        ):

            offers = item.get(
                "offers",
                {},
            )

            if isinstance(
                offers,
                dict,
            ):

                prijs_specificatie = (
                    offers.get(
                        "priceSpecification",
                        {},
                    )
                )

                if (
                    resultaat[
                        "prijs"
                    ]
                    is None
                    and isinstance(
                        prijs_specificatie,
                        dict,
                    )
                ):

                    resultaat[
                        "prijs"
                    ] = prijs_specificatie.get(
                        "price"
                    )

            image = item.get(
                "image"
            )

            if (
                image
                and resultaat[
                    "foto_url"
                ]
                is None
            ):

                if isinstance(
                    image,
                    str,
                ):

                    resultaat[
                        "foto_url"
                    ] = (
                        normaliseer_foto_url(
                            image
                        )
                    )

                elif (
                    isinstance(
                        image,
                        list,
                    )
                    and image
                ):

                    resultaat[
                        "foto_url"
                    ] = (
                        normaliseer_foto_url(
                            image[0]
                        )
                    )

    # ========================================================
    # FALLBACK POSTCODE / PLAATS VIA H1
    # ========================================================

    if h1:

        h1_tekst = normale_tekst(
            h1.get_text(
                " ",
                strip=True,
            )
        )

        match = re.search(
            r"\b(\d{5})\s+"
            r"([A-Za-zÀ-ÿ'’ -]+)",
            h1_tekst,
        )

        if match:

            if (
                resultaat[
                    "postcode"
                ]
                is None
            ):

                resultaat[
                    "postcode"
                ] = match.group(
                    1
                )

            if (
                resultaat[
                    "plaats"
                ]
                is None
            ):

                resultaat[
                    "plaats"
                ] = normale_tekst(
                    match.group(
                        2
                    )
                )

    # ========================================================
    # GARAGE
    # ========================================================
    #
    # Alleen expliciete vermeldingen.
    #
    # None  = onbekend
    # True  = expliciet aanwezig
    # False = expliciet afwezig
    # ========================================================

    if resultaat["garage"] is None:

        if re.search(
            r"\bgarage\b",
            omschrijving_lower,
        ):

            resultaat[
                "garage"
            ] = True

        if re.search(
            r"\b(?:sans|aucun)\s+garage\b",
            omschrijving_lower,
        ):

            resultaat[
                "garage"
            ] = False

    # ========================================================
    # TUIN
    # ========================================================

    if resultaat["tuin"] is None:

        if re.search(
            r"\b(?:jardin|jardinet)\b",
            omschrijving_lower,
        ):

            resultaat[
                "tuin"
            ] = True

        if re.search(
            r"\bsans\s+jardin\b",
            omschrijving_lower,
        ):

            resultaat[
                "tuin"
            ] = False

    # ========================================================
    # TERRAS
    # ========================================================

    if resultaat["terras"] is None:

        if re.search(
            r"\bterrasse\b",
            omschrijving_lower,
        ):

            resultaat[
                "terras"
            ] = True

        if re.search(
            r"\bsans\s+terrasse\b",
            omschrijving_lower,
        ):

            resultaat[
                "terras"
            ] = False

    # ========================================================
    # PARKING
    # ========================================================

    if resultaat["parking"] is None:

        if re.search(
            r"\bparking\b",
            omschrijving_lower,
        ):

            resultaat[
                "parking"
            ] = True

        if re.search(
            r"\bsans\s+parking\b",
            omschrijving_lower,
        ):

            resultaat[
                "parking"
            ] = False

    # ========================================================
    # SCHUUR / GRANGE
    # ========================================================

    if resultaat["schuur"] is None:

        if re.search(
            r"\bgrange\b",
            omschrijving_lower,
        ):

            resultaat[
                "schuur"
            ] = True

        if re.search(
            r"\bsans\s+grange\b",
            omschrijving_lower,
        ):

            resultaat[
                "schuur"
            ] = False

    # ========================================================
    # DEPENDANCES
    # ========================================================

    if resultaat["dependances"] is None:

        if re.search(
            r"\bd[ée]pendances?\b",
            omschrijving_lower,
        ):

            resultaat[
                "dependances"
            ] = True

        if re.search(
            r"\bsans\s+d[ée]pendances?\b",
            omschrijving_lower,
        ):

            resultaat[
                "dependances"
            ] = False

    # ========================================================
    # ASSAINISSEMENT
    # ========================================================
    #
    # Dit houden we bewust als tekstveld.
    # Zo verliezen we geen informatie.
    # ========================================================

    assainissement_patronen = [
        (
            "tout-à-l'égout",
            r"\btout[- ]?[àa][- ]?l['’]?égout\b",
        ),
        (
            "assainissement collectif",
            r"\bassainissement collectif\b",
        ),
        (
            "assainissement individuel",
            r"\bassainissement individuel\b",
        ),
        (
            "fosse septique",
            r"\bfosse septique\b",
        ),
    ]

    for (
        waarde,
        patroon,
    ) in assainissement_patronen:

        if re.search(
            patroon,
            omschrijving_lower,
            re.IGNORECASE,
        ):

            resultaat[
                "assainissement"
            ] = waarde

            break

    # ========================================================
    # RENOVATIESTATUS / STAAT
    # ========================================================

    renovatie_patronen = [
        (
            "volledig te renoveren",
            r"\bà rénover entièrement\b",
        ),
        (
            "te renoveren",
            r"\bà rénover\b",
        ),
        (
            "gerenoveerd",
            r"\brénové(?:e|es|s)?\b",
        ),
        (
            "goede staat",
            r"\bbon état\b",
        ),
        (
            "zeer goede staat",
            r"\btrès bon état\b",
        ),
        (
            "nieuwstaat",
            r"\bétat neuf\b",
        ),
    ]

    for (
        nederlandse_status,
        patroon,
    ) in renovatie_patronen:

        if re.search(
            patroon,
            omschrijving_lower,
            re.IGNORECASE,
        ):

            resultaat[
                "renovatiestatus"
            ] = nederlandse_status

            resultaat[
                "staat"
            ] = nederlandse_status

            break

    # ========================================================
    # DPE / GES
    # ========================================================

    energy_section = soup.select_one(
        "section.energySection"
    )

    if energy_section:

        energy_text = normale_tekst(
            energy_section.get_text(
                " ",
                strip=True,
            )
        )

        # ----------------------------------------------------
        # DPE VERBRUIK
        # ----------------------------------------------------

        dpe_match = re.search(
            r"(\d+)\s*kWh/m",
            energy_text,
            re.IGNORECASE,
        )

        if dpe_match:

            resultaat[
                "dpe_verbruik"
            ] = int(
                dpe_match.group(
                    1
                )
            )

        # ----------------------------------------------------
        # GES UITSTOOT
        # ----------------------------------------------------

        ges_match = re.search(
            r"(\d+)\s*kg\s*CO",
            energy_text,
            re.IGNORECASE,
        )

        if ges_match:

            resultaat[
                "ges_uitstoot"
            ] = int(
                ges_match.group(
                    1
                )
            )

        # ----------------------------------------------------
        # DPE KLASSE
        # ----------------------------------------------------

        actieve_dpe = (
            energy_section.select_one(
                ".dpe-line.active"
            )
        )

        if actieve_dpe:

            actieve_tekst = normale_tekst(
                actieve_dpe.get_text(
                    " ",
                    strip=True,
                )
            )

            klasse_match = re.search(
                r"\b([A-G])\b",
                actieve_tekst,
            )

            if klasse_match:

                resultaat[
                    "dpe_klasse"
                ] = klasse_match.group(
                    1
                )

        # ----------------------------------------------------
        # GES KLASSE
        # ----------------------------------------------------

        mogelijke_ges = (
            energy_section.select(
                ".ges-line.active, "
                ".greenhouse-gas-line.active"
            )
        )

        for element in mogelijke_ges:

            tekst = normale_tekst(
                element.get_text(
                    " ",
                    strip=True,
                )
            )

            klasse_match = re.search(
                r"\b([A-G])\b",
                tekst,
            )

            if klasse_match:

                resultaat[
                    "ges_klasse"
                ] = klasse_match.group(
                    1
                )

                break

    # ========================================================
    # FOTO'S
    # ========================================================

    fotos = []

    for img in soup.find_all(
        "img"
    ):

        kandidaten = [
            img.get(
                "src"
            ),
            img.get(
                "src2"
            ),
        ]

        for url in kandidaten:

            if not url:
                continue

            if (
                "file.bienici.com/photo/"
                not in url
            ):
                continue

            foto = normaliseer_foto_url(
                url
            )

            if (
                foto
                and foto not in fotos
            ):

                fotos.append(
                    foto
                )

    resultaat[
        "fotos"
    ] = fotos

    resultaat[
        "aantal_fotos"
    ] = len(
        fotos
    )

    if fotos:

        resultaat[
            "foto_url"
        ] = fotos[
            0
        ]

    return resultaat


# ============================================================
# PUBLIEKE DETAILFUNCTIE
# ============================================================

def haal_bienici_advertentie_op(
    url,
):
    """
    Haalt één Bien'ici-advertentie live op
    en retourneert de geparseerde woninggegevens.

    Deze functie is de publieke detailfunctie voor
    DETAILFUNCTIES in Huizenzoeker Frankrijk.
    """

    if not url:

        raise ValueError(
            "Bien'ici detail-URL ontbreekt"
        )

    logger.info(
        "Bien'ici detailpagina ophalen: %s",
        url,
    )

    html = haal_html_op(
        url,
        wacht_op_resultaten=False,
    )

    advertentie = parse_bienici_detail(
        html
    )

    # Algemene bronvelden toevoegen.
    advertentie[
        "link"
    ] = url

    advertentie[
        "bron"
    ] = "Bien'ici"

    advertentie[
        "bron_sleutel"
    ] = "bienici"

    logger.info(
        "Bien'ici detailpagina verwerkt: %s",
        advertentie.get(
            "titel"
        ),
    )

    logger.info(
        "Bien'ici detail: "
        "prijs=%s, "
        "plaats=%s, "
        "woonoppervlakte=%s, "
        "terrein=%s, "
        "slaapkamers=%s, "
        "DPE=%s, "
        "foto's=%s",
        advertentie.get(
            "prijs"
        ),
        advertentie.get(
            "plaats"
        ),
        advertentie.get(
            "woonoppervlakte"
        ),
        advertentie.get(
            "perceeloppervlakte"
        ),
        advertentie.get(
            "slaapkamers"
        ),
        advertentie.get(
            "dpe_klasse"
        ),
        len(
            advertentie.get(
                "fotos"
            )
            or []
        ),
    )

    return advertentie

# ============================================================
#
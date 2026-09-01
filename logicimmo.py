"""
Logic-Immo bronmodule voor Huizenzoeker Frankrijk.

Deze versie gebruikt:
- Playwright voor het openen van de Logic-Immo zoekpagina;
- BeautifulSoup voor het parsen van de gerenderde HTML;
- de bewezen zoekstructuur voor postcode 08600 (Givet);
- exacte prijsfiltering in Python;
- correcte selectie van de woningfoto i.p.v. het makelaarslogo.

Belangrijk:
Voor andere postcodes is de interne Logic-Immo locatiecode nog niet bewezen.
Daarom wordt momenteel alleen postcode 08600 ondersteund.
"""

from __future__ import annotations

import os
import re
import time
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from csv_opslaan import opslaan_csv
from logger import logger
from vergelijk import nieuwe_woningen


BASE_URL = "https://www.logic-immo.com"

NAVIGATIE_TIMEOUT_MS = 45_000
WACHT_NA_LADEN_MS = 1_500

HEADLESS = os.getenv("CI", "").lower() == "true"

LOGICIMMO_DIRECTE_ROUTES = {
    "08600": {
        "plaats": "givet",
        "regio": "grand-est",
        "locatiecode": "ad08fr2631",
    },
}


def maak_zoek_url(postcode, woningtype):
    postcode = str(postcode).strip()
    woningtype = str(woningtype).strip().lower()

    if woningtype != "huis":
        raise ValueError(
            f"Logic-Immo ondersteunt momenteel alleen woningtype 'huis', "
            f"niet: {woningtype!r}"
        )

    route = LOGICIMMO_DIRECTE_ROUTES.get(postcode)

    if route is None:
        raise ValueError(
            f"Voor postcode {postcode} is nog geen gevalideerde "
            f"Logic-Immo locatiecode beschikbaar."
        )

    return (
        f"{BASE_URL}/recherche-immo/vente/maison/"
        f"{route['regio']}/{route['plaats']}-{postcode}/"
        f"{route['locatiecode']}"
    )


def handel_cookievenster_af(page):
    selectors = [
        page.get_by_text(
            re.compile(r"Continuer sans accepter", re.I)
        ),
        page.get_by_role(
            "button",
            name=re.compile(r"Continuer sans accepter", re.I),
        ),
        page.get_by_role(
            "button",
            name=re.compile(r"^OK$", re.I),
        ),
    ]

    for selector in selectors:
        try:
            if selector.count() > 0 and selector.first.is_visible():
                selector.first.click(timeout=3_000)
                logger.info(
                    "Logic-Immo cookie-/privacymelding afgehandeld"
                )
                page.wait_for_timeout(500)
                return
        except Exception:
            pass

    logger.info(
        "Logic-Immo: geen actieve cookie-/privacymelding gevonden"
    )


def haal_pagina_op_met_playwright(zoek_url, postcode):
    logger.info(
        "Logic-Immo opent zoekpagina met Playwright (headless=%s)",
        HEADLESS,
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS
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
            NAVIGATIE_TIMEOUT_MS
        )

        try:
            response = page.goto(
                zoek_url,
                wait_until="domcontentloaded",
                timeout=NAVIGATIE_TIMEOUT_MS,
            )

            if response is not None:
                logger.info(
                    "Logic-Immo browser HTTP-status %s voor postcode %s",
                    response.status,
                    postcode,
                )

            handel_cookievenster_af(page)

            try:
                page.locator(
                    '[data-testid="serp-core-classified-card-testid"]'
                ).first.wait_for(
                    state="attached",
                    timeout=20_000,
                )
            except PlaywrightTimeoutError:
                logger.warning(
                    "Logic-Immo woningkaart-selector niet binnen "
                    "20 seconden gevonden"
                )

            page.wait_for_timeout(
                WACHT_NA_LADEN_MS
            )

            logger.info(
                "Logic-Immo paginatitel: %s",
                page.title(),
            )

            html = page.content()

            logger.info(
                "Logic-Immo gerenderde HTML: %s tekens",
                len(html),
            )

            if len(html) < 10_000:
                raise RuntimeError(
                    "Logic-Immo leverde onverwacht weinig HTML op."
                )

            return html

        finally:
            context.close()
            browser.close()

            logger.info(
                "Logic-Immo browser gesloten voor postcode %s",
                postcode,
            )


def is_detail_url(href):
    if not href:
        return False

    if "/detail-annonce/" in href:
        return True

    if re.search(
        r"/detail-vente-\d+\.htm(?:[?#].*)?$",
        href,
        flags=re.I,
    ):
        return True

    return False


def normaliseer_url(href):
    return urljoin(
        BASE_URL,
        href,
    )


def unieke_detail_urls(element):
    gevonden = []
    gezien = set()

    for link in element.find_all(
        "a",
        href=True,
    ):
        href = link.get("href")

        if not is_detail_url(href):
            continue

        url = normaliseer_url(
            href
        )

        if url in gezien:
            continue

        gezien.add(url)
        gevonden.append(url)

    return gevonden


def bepaal_verwacht_aantal(soup):
    titel = ""

    if soup.title:
        titel = soup.title.get_text(
            " ",
            strip=True,
        )

    volledige_tekst = soup.get_text(
        " ",
        strip=True,
    )

    for tekst in (
        titel,
        volledige_tekst[:20_000],
    ):
        match = re.search(
            r"(\d+)\s+annonces?",
            tekst,
            flags=re.I,
        )

        if match:
            return int(
                match.group(1)
            )

    return None


def normaliseer_tekst(tekst):
    if not tekst:
        return ""

    tekst = tekst.replace(
        "\u202f",
        " ",
    ).replace(
        "\xa0",
        " ",
    )

    return re.sub(
        r"\s+",
        " ",
        tekst,
    ).strip()


def haal_prijs_uit_tekst(tekst):
    tekst = normaliseer_tekst(
        tekst
    )

    match = re.search(
        r"(?<!\d)(\d{2,3}(?:[ .]\d{3})+|\d{5,6})\s*€",
        tekst,
    )

    if not match:
        return None

    cijfers = re.sub(
        r"\D",
        "",
        match.group(1),
    )

    if not cijfers:
        return None

    prijs = int(
        cijfers
    )

    if 10_000 <= prijs <= 10_000_000:
        return prijs

    return None


def vind_resultaatkaarten(soup, verwacht_aantal):
    kaarten = soup.find_all(
        attrs={
            "data-testid":
            "serp-core-classified-card-testid"
        }
    )

    geldige_kaarten = []

    for kaart in kaarten:
        urls = unieke_detail_urls(
            kaart
        )

        if len(urls) == 1:
            geldige_kaarten.append(
                kaart
            )

    if geldige_kaarten:
        logger.info(
            "Logic-Immo resultaatkaarten via data-testid: %s",
            len(geldige_kaarten),
        )

        if (
            verwacht_aantal is None
            or len(geldige_kaarten) == verwacht_aantal
        ):
            return geldige_kaarten

    return geldige_kaarten


def haal_prijs(kaart):
    element = kaart.find(
        attrs={
            "data-testid":
            "cardmfe-price-testid"
        }
    )

    if element is not None:
        prijs = haal_prijs_uit_tekst(
            element.get_text(
                " ",
                strip=True,
            )
        )

        if prijs is not None:
            return prijs

    return haal_prijs_uit_tekst(
        kaart.get_text(
            " ",
            strip=True,
        )
    )


def haal_slaapkamers(kaart):
    tekst = normaliseer_tekst(
        kaart.get_text(
            " ",
            strip=True,
        )
    )

    match = re.search(
        r"(\d+)\s+chambres?",
        tekst,
        flags=re.I,
    )

    if match:
        return int(
            match.group(1)
        )

    return "Onbekend"


def haal_oppervlakte(kaart):
    keyfacts = kaart.find(
        attrs={
            "data-testid":
            "cardmfe-keyfacts-testid"
        }
    )

    if keyfacts is not None:
        for item in keyfacts.find_all(
            True,
            recursive=False,
        ):
            feit = normaliseer_tekst(
                item.get_text(
                    " ",
                    strip=True,
                )
            )

            if "terrain" in feit.lower():
                continue

            match = re.fullmatch(
                r"(\d+(?:[.,]\d+)?)\s*m²",
                feit,
                flags=re.I,
            )

            if match:
                waarde = float(
                    match.group(1).replace(
                        ",",
                        ".",
                    )
                )

                return int(waarde) if waarde.is_integer() else waarde

    return "Onbekend"


def haal_perceeloppervlakte(kaart):
    keyfacts = kaart.find(
        attrs={
            "data-testid":
            "cardmfe-keyfacts-testid"
        }
    )

    if keyfacts is None:
        return ""

    tekst = normaliseer_tekst(
        keyfacts.get_text(
            " ",
            strip=True,
        )
    )

    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*m²\s+de\s+terrain",
        tekst,
        flags=re.I,
    )

    if not match:
        return ""

    waarde = float(
        match.group(1).replace(
            ",",
            ".",
        )
    )

    return int(waarde) if waarde.is_integer() else waarde


def haal_plaats_en_postcode(
    kaart,
    detail_url,
    zoek_postcode,
):
    adres_element = kaart.find(
        attrs={
            "data-testid":
            "cardmfe-description-box-address"
        }
    )

    if adres_element is not None:
        adres = normaliseer_tekst(
            adres_element.get_text(
                " ",
                strip=True,
            )
        )

        match = re.search(
            r"(.+?)\s*\((\d{5})\)",
            adres,
        )
        if match:
            plaats = normaliseer_tekst(
                match.group(1)
            )

            # Logic-Immo gebruikt soms wijk-/liggingsaanduidingen
            # zoals "Est, Givet" of "Centre, Givet".
            # Voor de Huizenzoeker willen we de echte plaatsnaam.
            if "," in plaats:
                plaats = plaats.split(",")[-1].strip()

            return (
                plaats,
                match.group(2),
            )
        
    pad = urlparse(
        detail_url
    ).path

    match = re.search(
        r"/([a-z0-9-]+)-(\d{5})(?:/|$)",
        pad,
        flags=re.I,
    )

    if match:
        return (
            match.group(1).replace(
                "-",
                " ",
            ).title(),
            match.group(2),
        )

    tekst = normaliseer_tekst(
        kaart.get_text(
            " ",
            strip=True,
        )
    )

    match = re.search(
        r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]{1,40})\s*\((\d{5})\)",
        tekst,
    )

    if match:
        return (
            normaliseer_tekst(
                match.group(1)
            ),
            match.group(2),
        )

    return (
        "Onbekend",
        zoek_postcode,
    )


def haal_titel(kaart, plaats):
    covering_link = kaart.find(
        "a",
        attrs={
            "data-testid":
            "card-mfe-covering-link-testid"
        },
    )

    if covering_link is not None:
        tekst = normaliseer_tekst(
            covering_link.get(
                "title",
                "",
            )
        )

        match = re.search(
            r"Maison à vendre.*?(\d+)\s+pièces?",
            tekst,
            flags=re.I,
        )

        if match:
            return (
                f"Maison à vendre {match.group(1)} pièces - {plaats}"
            )

    return (
        f"Maison à vendre - {plaats}"
    )


def haal_foto_url(kaart):
    try:
        picture_box = kaart.find(
            attrs={
                "data-testid":
                "cardmfe-picture-box-test-id"
            }
        )

        if picture_box is None:
            return ""

        actieve_slide = picture_box.find(
            attrs={
                "aria-current":
                "true"
            }
        )

        afbeelding = None

        if actieve_slide is not None:
            afbeelding = actieve_slide.find(
                "img"
            )

        if afbeelding is None:
            afbeelding = picture_box.find(
                "img"
            )

        if afbeelding is None:
            return ""

        foto = afbeelding.get(
            "src"
        ) or afbeelding.get(
            "data-src"
        )

        if not foto:
            return ""

        foto = foto.strip()

        if foto.startswith("//"):
            foto = "https:" + foto
        elif foto.startswith("/"):
            foto = urljoin(
                BASE_URL,
                foto,
            )

        return foto

    except Exception:
        logger.exception(
            "Logic-Immo hoofdfoto kon niet worden uitgelezen"
        )
        return ""


def verwerk_kaart(
    kaart,
    zoek_postcode,
):
    urls = unieke_detail_urls(
        kaart
    )

    if len(urls) != 1:
        raise ValueError(
            f"Woningkaart bevat {len(urls)} detail-URL's."
        )

    link = urls[0]

    prijs = haal_prijs(
        kaart
    )

    if prijs is None:
        raise ValueError(
            "Geen geldige vraagprijs gevonden."
        )

    plaats, _postcode = haal_plaats_en_postcode(
        kaart,
        link,
        zoek_postcode,
    )

    return {
        "titel": haal_titel(
            kaart,
            plaats,
        ),
        "prijs": prijs,
        "slaapkamers": haal_slaapkamers(
            kaart
        ),
        "oppervlakte": haal_oppervlakte(
            kaart
        ),
        "perceeloppervlakte": haal_perceeloppervlakte(
            kaart
        ),
        "plaats": plaats,
        "link": link,
        "foto": haal_foto_url(
            kaart
        ),
        "bron": "Logic-Immo",
    }


def zoek_logicimmo(
    postcode,
    woningtype,
    min_prijs,
    max_prijs,
    csv_bestand,
):
    start_totaal = time.perf_counter()

    postcode = str(
        postcode
    ).strip()

    woningtype = str(
        woningtype
    ).strip().lower()

    min_prijs = int(
        min_prijs
    )
    max_prijs = int(
        max_prijs
    )

    logger.info(
        "Zoeken op Logic-Immo gestart: postcode=%s, woningtype=%s",
        postcode,
        woningtype,
    )

    zoek_url = maak_zoek_url(
        postcode,
        woningtype,
    )

    logger.info(
        "Logic-Immo directe zoek-URL: %s",
        zoek_url,
    )

    start_browser = time.perf_counter()

    html = haal_pagina_op_met_playwright(
        zoek_url,
        postcode,
    )

    duur_browser = (
        time.perf_counter()
        - start_browser
    )

    start_parser = time.perf_counter()

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    verwacht_aantal = bepaal_verwacht_aantal(
        soup
    )

    logger.info(
        "Logic-Immo verwacht aantal advertenties: %s",
        verwacht_aantal,
    )

    kaarten = vind_resultaatkaarten(
        soup,
        verwacht_aantal,
    )

    logger.info(
        "Logic-Immo hoofdadvertenties gevonden: %s",
        len(kaarten),
    )

    if (
        verwacht_aantal is not None
        and len(kaarten) != verwacht_aantal
    ):
        raise RuntimeError(
            f"Logic-Immo parser vond {len(kaarten)} hoofdadvertenties, "
            f"maar de pagina meldt {verwacht_aantal} advertenties."
        )

    resultaten = []
    buiten_prijsrange = 0
    kaart_fouten = 0

    for nummer, kaart in enumerate(
        kaarten,
        start=1,
    ):
        try:
            woning = verwerk_kaart(
                kaart,
                postcode,
            )

            prijs = woning[
                "prijs"
            ]

            if not (
                min_prijs
                <= prijs
                <= max_prijs
            ):
                buiten_prijsrange += 1
                continue

            resultaten.append(
                woning
            )

            logger.info(
                "Logic-Immo match %s: €%s | %s | %s m² | %s",
                len(resultaten),
                f"{prijs:,}".replace(",", "."),
                woning["plaats"],
                woning["oppervlakte"],
                woning["link"],
            )

        except Exception:
            kaart_fouten += 1
            logger.exception(
                "Logic-Immo fout bij verwerken woningkaart %s",
                nummer,
            )

    duur_parser = (
        time.perf_counter()
        - start_parser
    )

    logger.info(
        "Logic-Immo samenvatting: %s kaarten, %s buiten prijsrange, "
        "%s kaartfouten, %s passende woningen",
        len(kaarten),
        buiten_prijsrange,
        kaart_fouten,
        len(resultaten),
    )

    logger.info(
        "Logic-Immo: %s woningen uitgelezen",
        len(resultaten),
    )

    start_csv = time.perf_counter()

    nieuw = nieuwe_woningen(
        resultaten,
        csv_bestand=csv_bestand,
    )

    logger.info(
        "Logic-Immo: %s nieuwe woningen",
        len(nieuw),
    )

    opslaan_csv(
        resultaten,
        bestandsnaam=csv_bestand,
    )

    duur_csv = (
        time.perf_counter()
        - start_csv
    )

    duur_totaal = (
        time.perf_counter()
        - start_totaal
    )

    logger.info(
        "Logic-Immo performance: browser %.2f sec | parser %.2f sec | "
        "CSV/vergelijk %.2f sec | totaal %.2f sec",
        duur_browser,
        duur_parser,
        duur_csv,
        duur_totaal,
    )

    return nieuw

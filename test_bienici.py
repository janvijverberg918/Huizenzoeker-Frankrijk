"""
test_bienici.py

Technische test Bien'ici - fase 2.

Doel:
- zoekpagina Givet 08600 openen met Playwright;
- cookies accepteren;
- aantal woningen uit structured data bepalen;
- unieke resultaatkaarten vinden;
- dubbele promoted advertenties dedupliceren;
- per woning basisgegevens uitlezen;
- prijsfilter €80.000 - €220.000 testen.

Nog GEEN:
- productieparser
- CSV
- historie
- AI
- e-mail
"""

import json
import re
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


# ============================================================
# TESTCONFIGURATIE
# ============================================================

POSTCODE = "08600"
PLAATS = "givet"

MIN_PRIJS = 80_000
MAX_PRIJS = 220_000

BASE_URL = "https://www.bienici.com"

ZOEK_URL = (
    f"{BASE_URL}/recherche/achat/"
    f"{PLAATS}-{POSTCODE}/maisonvilla"
)

PLAYWRIGHT_TIMEOUT = 45_000


# ============================================================
# ALGEMENE HELPERS
# ============================================================

def normale_tekst(tekst):
    if not tekst:
        return ""

    tekst = tekst.replace("\xa0", " ")
    tekst = tekst.replace("\u202f", " ")
    tekst = re.sub(r"\s+", " ", tekst)

    return tekst.strip()


def nette_prijs(prijs):
    if prijs is None:
        return "-"

    return f"€{prijs:,}".replace(",", ".")


# ============================================================
# COOKIES
# ============================================================

def accepteer_cookies(page):
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

            print(
                "Cookieknop gevonden: "
                f"{normale_tekst(locator.first.inner_text())}"
            )

            locator.first.click(
                timeout=5000
            )

            page.wait_for_timeout(
                1000
            )

            print(
                "Cookies geaccepteerd."
            )

            return True

        except Exception:
            continue

    print(
        "Geen zichtbare cookieknop gevonden."
    )

    return False


# ============================================================
# STRUCTURED DATA
# ============================================================

def bepaal_verwacht_aantal(soup):
    """
    Bien'ici zet AggregateOffer structured data in de pagina.

    Voorbeeld:
    {
        "@type": "Product",
        "offers": {
            "@type": "AggregateOffer",
            "offerCount": 12
        }
    }
    """

    scripts = soup.find_all(
        "script",
        attrs={
            "type": "application/ld+json"
        },
    )

    for script in scripts:

        inhoud = script.string

        if not inhoud:
            continue

        try:
            data = json.loads(
                inhoud
            )

        except json.JSONDecodeError:
            continue

        if not isinstance(
            data,
            dict,
        ):
            continue

        offers = data.get(
            "offers"
        )

        if not isinstance(
            offers,
            dict,
        ):
            continue

        aantal = offers.get(
            "offerCount"
        )

        if aantal is not None:

            try:
                return int(
                    aantal
                )

            except (TypeError, ValueError):
                pass

    return None


# ============================================================
# KAARTEN
# ============================================================

def zoek_unieke_kaarten(soup):
    """
    Bien'ici gebruikt:

        <article data-id="...">

    Sommige advertenties staan zowel bij 'à la une'
    als later opnieuw in de gewone lijst.

    Daarom dedupliceren we op data-id.
    """

    unieke = {}

    artikelen = soup.find_all(
        "article",
        attrs={
            "data-id": True
        },
    )

    for artikel in artikelen:

        advertentie_id = artikel.get(
            "data-id"
        )

        if not advertentie_id:
            continue

        # Alleen kaarten met echte detail-link.
        link = artikel.find(
            "a",
            class_="detailedSheetLink",
        )

        if link is None:
            continue

        unieke.setdefault(
            advertentie_id,
            artikel,
        )

    return unieke


# ============================================================
# VELDEN UITLEZEN
# ============================================================

def haal_url(kaart):
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

    # Querystring verwijderen.
    href = href.split(
        "?",
        1,
    )[0]

    return urljoin(
        BASE_URL,
        href,
    )


def haal_titel(kaart):
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


def haal_adres(kaart):
    element = kaart.select_one(
        ".real-estate-main-info__address"
    )

    if element is None:
        return None, None

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
        return None, None

    postcode = match.group(1)
    plaats = match.group(2).strip()

    return postcode, plaats


def haal_prijs(kaart):
    element = kaart.select_one(
        ".ad-price__the-price"
    )

    if element is None:
        return None

    tekst = normale_tekst(
        element.get_text(
            " ",
            strip=True,
        )
    )

    cijfers = re.sub(
        r"\D",
        "",
        tekst,
    )

    if not cijfers:
        return None

    try:
        return int(
            cijfers
        )

    except ValueError:
        return None


def haal_woonoppervlakte(kaart):
    """
    Titel ziet er bijvoorbeeld zo uit:

        Maison 5 pièces 180 m²
    """

    titel = haal_titel(
        kaart
    )

    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*m²",
        titel,
        flags=re.I,
    )

    if not match:
        return None

    waarde = match.group(1).replace(
        ",",
        ".",
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


def haal_aantal_kamers(kaart):
    titel = haal_titel(
        kaart
    )

    match = re.search(
        r"(\d+)\s+pièces?",
        titel,
        flags=re.I,
    )

    if match:
        return int(
            match.group(1)
        )

    return None


def haal_foto(kaart):
    foto = kaart.select_one(
        ".ad-overview-photo__image img"
    )

    if foto is None:
        return ""

    src = foto.get(
        "src"
    )

    if not src:
        return ""

    return src.strip()


def haal_omschrijving(kaart):
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


# ============================================================
# EXTRA DIAGNOSTIEK UIT OMSCHRIJVING
# ============================================================

def haal_terrain_uit_omschrijving(omschrijving):
    """
    Voorlopige diagnostische parser.

    Voorbeelden:
        terrain de 577 m²
        terrain de 250 m²
        parcelle d'environ 700 m²
    """

    patronen = [
        r"terrain\s+de\s+(\d+)\s*m²",
        r"terrain\s+d['’]environ\s+(\d+)\s*m²",
        r"parcelle\s+d['’]environ\s+(\d+)\s*m²",
        r"parcelle\s+de\s+(\d+)\s*m²",
    ]

    for patroon in patronen:

        match = re.search(
            patroon,
            omschrijving,
            flags=re.I,
        )

        if match:
            return int(
                match.group(1)
            )

    return None


def herken_dpe(kaart):
    """
    Voorlopig alleen diagnostisch.

    We zoeken naar een energieletter in zichtbare kaartdata
    of beschrijving.
    """

    tekst = normale_tekst(
        kaart.get_text(
            " ",
            strip=True,
        )
    )

    patronen = [
        r"\bDPE\s*[:\-]?\s*([A-G])\b",
        r"classe\s+énergétique\s*[:\-]?\s*([A-G])\b",
        r"classe\s+energie\s*[:\-]?\s*([A-G])\b",
    ]

    for patroon in patronen:

        match = re.search(
            patroon,
            tekst,
            flags=re.I,
        )

        if match:
            return match.group(1).upper()

    return None


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 76)
    print("TECHNISCHE TEST BIEN'ICI - FASE 2")
    print("=" * 76)

    print()
    print(
        f"Postcode       : {POSTCODE}"
    )

    print(
        f"Plaats         : {PLAATS}"
    )

    print(
        f"Minimumprijs   : {nette_prijs(MIN_PRIJS)}"
    )

    print(
        f"Maximumprijs   : {nette_prijs(MAX_PRIJS)}"
    )

    print()
    print(
        "Zoek-URL:"
    )

    print(
        ZOEK_URL
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False,
            slow_mo=100,
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
            PLAYWRIGHT_TIMEOUT
        )

        try:

            start = time.perf_counter()

            # ------------------------------------------------
            # Pagina openen
            # ------------------------------------------------

            response = page.goto(
                ZOEK_URL,
                wait_until="domcontentloaded",
                timeout=PLAYWRIGHT_TIMEOUT,
            )

            status = (
                response.status
                if response is not None
                else None
            )

            print()
            print(
                f"Browser HTTP    : {status}"
            )

            page.wait_for_timeout(
                1000
            )

            accepteer_cookies(
                page
            )

            # ------------------------------------------------
            # Wachten op kaarten
            # ------------------------------------------------

            page.locator(
                "article[data-id]"
            ).first.wait_for(
                state="attached",
                timeout=20_000,
            )

            page.wait_for_timeout(
                2000
            )

            # ------------------------------------------------
            # HTML
            # ------------------------------------------------

            html = page.content()

            soup = BeautifulSoup(
                html,
                "html.parser",
            )

            titel = page.title()

            print(
                f"Pagina titel    : {titel}"
            )

            print(
                f"HTML grootte    : {len(html):,} tekens"
            )

            # ------------------------------------------------
            # Verwacht aantal
            # ------------------------------------------------

            verwacht_aantal = (
                bepaal_verwacht_aantal(
                    soup
                )
            )

            print()
            print(
                f"Bien'ici meldt  : {verwacht_aantal} woningen"
            )

            # ------------------------------------------------
            # Unieke kaarten
            # ------------------------------------------------

            kaarten = zoek_unieke_kaarten(
                soup
            )

            print(
                f"Unieke kaarten  : {len(kaarten)}"
            )

            # ------------------------------------------------
            # Kaarten uitlezen
            # ------------------------------------------------

            woningen = []

            print()
            print("=" * 76)
            print("RESULTAATKAARTEN")
            print("=" * 76)

            for nummer, (
                advertentie_id,
                kaart,
            ) in enumerate(
                kaarten.items(),
                start=1,
            ):

                url = haal_url(
                    kaart
                )

                titel = haal_titel(
                    kaart
                )

                postcode, plaats = (
                    haal_adres(
                        kaart
                    )
                )

                prijs = haal_prijs(
                    kaart
                )

                woonopp = (
                    haal_woonoppervlakte(
                        kaart
                    )
                )

                kamers = (
                    haal_aantal_kamers(
                        kaart
                    )
                )

                foto = haal_foto(
                    kaart
                )

                omschrijving = (
                    haal_omschrijving(
                        kaart
                    )
                )

                terrain = (
                    haal_terrain_uit_omschrijving(
                        omschrijving
                    )
                )

                dpe = herken_dpe(
                    kaart
                )

                binnen_range = (
                    prijs is not None
                    and MIN_PRIJS
                    <= prijs
                    <= MAX_PRIJS
                )

                status_tekst = (
                    "MATCH"
                    if binnen_range
                    else "BUITEN PRIJSRANGE"
                )

                woning = {
                    "id": advertentie_id,
                    "titel": titel,
                    "postcode": postcode,
                    "plaats": plaats,
                    "prijs": prijs,
                    "woonoppervlakte": woonopp,
                    "kamers": kamers,
                    "terrain": terrain,
                    "dpe": dpe,
                    "foto": foto,
                    "url": url,
                }

                woningen.append(
                    woning
                )

                print()
                print(
                    f"[{nummer:02}] {status_tekst}"
                )

                print(
                    f"     ID        : {advertentie_id}"
                )

                print(
                    f"     Titel     : {titel}"
                )

                print(
                    f"     Postcode  : {postcode}"
                )

                print(
                    f"     Plaats    : {plaats}"
                )

                print(
                    f"     Prijs     : {nette_prijs(prijs)}"
                )

                print(
                    f"     Kamers    : {kamers}"
                )

                print(
                    f"     Woonopp.  : {woonopp} m²"
                )

                print(
                    f"     Terrain   : {terrain} m²"
                )

                print(
                    f"     DPE       : {dpe}"
                )

                print(
                    f"     Foto      : {foto}"
                )

                print(
                    f"     URL       : {url}"
                )

            # ------------------------------------------------
            # Matches
            # ------------------------------------------------

            matches = [
                woning
                for woning in woningen
                if (
                    woning["prijs"] is not None
                    and MIN_PRIJS
                    <= woning["prijs"]
                    <= MAX_PRIJS
                )
            ]

            print()
            print("=" * 76)
            print("WONINGEN BINNEN PRIJSRANGE")
            print("=" * 76)

            for nummer, woning in enumerate(
                matches,
                start=1,
            ):

                print()
                print(
                    f"[{nummer}] "
                    f"{nette_prijs(woning['prijs'])} | "
                    f"{woning['plaats']} | "
                    f"{woning['woonoppervlakte']} m²"
                )

                print(
                    f"    {woning['url']}"
                )

            # ------------------------------------------------
            # Samenvatting
            # ------------------------------------------------

            duur = (
                time.perf_counter()
                - start
            )

            print()
            print("=" * 76)
            print("SAMENVATTING FASE 2")
            print("=" * 76)

            print(
                f"HTTP 200              : "
                f"{status == 200}"
            )

            print(
                f"Bien'ici verwacht     : "
                f"{verwacht_aantal}"
            )

            print(
                f"Unieke kaarten        : "
                f"{len(kaarten)}"
            )

            print(
                f"Binnen prijsrange      : "
                f"{len(matches)}"
            )

            print(
                f"Looptijd               : "
                f"{duur:.2f} seconden"
            )

            print()

            if (
                verwacht_aantal is not None
                and len(kaarten)
                == verwacht_aantal
            ):

                print(
                    "RESULTAAT: GESLAAGD"
                )

                print(
                    "Aantal unieke woningkaarten "
                    "komt exact overeen met Bien'ici."
                )

            else:

                print(
                    "RESULTAAT: NOG NIET VOLLEDIG"
                )

                print(
                    "Aantal kaarten komt niet overeen "
                    "met het door Bien'ici gemelde aantal."
                )

            print()
            print("=" * 76)

        finally:

            context.close()
            browser.close()


if __name__ == "__main__":
    main()
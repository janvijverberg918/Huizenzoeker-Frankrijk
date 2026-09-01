"""
test_logicimmo.py

Technische proef Logic-Immo - fase 3.

Doel:
- zoekpagina voor postcode 08600 ophalen;
- vaststellen hoeveel hoofdadvertenties Logic-Immo meldt;
- de HTML-container met precies die hoofdadvertenties vinden;
- aanbevolen woningen buiten beschouwing laten;
- per resultaatkaart één woningrecord maken;
- prijs, postcode, woonoppervlakte, terrein en URL koppelen;
- prijsfilter €80.000 - €220.000 testen.

Nog GEEN:
- CSV
- historie
- detailparser
- AI
- e-mail
- integratie met huizenzoeker.py
"""

import re
import sys
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag


# ============================================================
# TESTCONFIGURATIE
# ============================================================

POSTCODE = "08600"
PLAATS = "givet"

MIN_PRIJS = 80_000
MAX_PRIJS = 220_000

BASE_URL = "https://www.logic-immo.com"

ZOEK_URL = (
    f"{BASE_URL}/recherche-immo/vente/maison/"
    f"grand-est/{PLAATS}-{POSTCODE}/ad08fr2631"
)

TIMEOUT = 30


# ============================================================
# HTTP
# ============================================================

def maak_headers():
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/142.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "fr-FR,fr;q=0.9,nl;q=0.8,en;q=0.7",
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,*/*;q=0.8"
        ),
    }


def maak_session():
    session = requests.Session()
    session.headers.update(maak_headers())
    return session


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
# URLS
# ============================================================

def is_detail_url(url):
    """
    Herkent de twee detail-URL-vormen die we in fase 2 zagen.
    """

    pad = urlparse(url).path.lower()

    if "/detail-annonce/" in pad:
        return True

    if re.search(r"/detail-vente-\d+\.htm$", pad):
        return True

    return False


def detail_urls_in_element(element):
    """
    Geeft unieke Logic-Immo detail-URLs binnen één HTML-element.
    """

    urls = []

    for link in element.find_all("a", href=True):
        href = link.get("href", "").strip()

        if not href:
            continue

        url = urljoin(BASE_URL, href)

        if not is_detail_url(url):
            continue

        if url not in urls:
            urls.append(url)

    return urls


# ============================================================
# BASISWAARDEN UIT TEKST
# ============================================================

def parse_prijs(tekst):
    """
    Probeert een woningprijs te herkennen.

    Voorbeelden:
        115 000 €
        178 500 €
        212000 €
    """

    if not tekst:
        return None

    tekst = normale_tekst(tekst)

    matches = re.findall(
        r"(\d{2,3}(?:[\s.]?\d{3})+|\d{4,6})\s*€",
        tekst
    )

    for waarde in matches:

        waarde = (
            waarde
            .replace(" ", "")
            .replace(".", "")
        )

        try:
            prijs = int(waarde)
        except ValueError:
            continue

        # Plausibele woningprijs.
        if 10_000 <= prijs <= 5_000_000:
            return prijs

    return None


def parse_woonoppervlakte(tekst):
    """
    Probeert woonoppervlakte te herkennen.

    Bijvoorbeeld:
        76 m²
        120 m2
    """

    if not tekst:
        return None

    matches = re.findall(
        r"(\d{1,4}(?:[.,]\d+)?)\s*m[²2]",
        tekst,
        flags=re.IGNORECASE,
    )

    if not matches:
        return None

    waardes = []

    for match in matches:
        try:
            waarde = float(
                match.replace(",", ".")
            )
        except ValueError:
            continue

        if 10 <= waarde <= 1000:
            waardes.append(waarde)

    if not waardes:
        return None

    waarde = waardes[0]

    if waarde.is_integer():
        return int(waarde)

    return waarde


def parse_terrain(tekst):
    """
    Probeert specifiek terreinoppervlak te herkennen.

    Voorbeelden:
        Terrain 577 m²
        Terrain de 400 m²
        400 m² de terrain
    """

    if not tekst:
        return None

    tekst = normale_tekst(tekst)

    patronen = [
        r"terrain\s*(?:de|:)?\s*(\d{1,6})\s*m[²2]",
        r"(\d{1,6})\s*m[²2]\s*(?:de\s*)?terrain",
    ]

    for patroon in patronen:

        match = re.search(
            patroon,
            tekst,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        try:
            waarde = int(match.group(1))
        except ValueError:
            continue

        if 10 <= waarde <= 1_000_000:
            return waarde

    return None


def parse_postcode(tekst):
    """
    Zoekt Franse postcode in de tekst.
    """

    if not tekst:
        return None

    match = re.search(
        r"\b(\d{5})\b",
        tekst,
    )

    if match:
        return match.group(1)

    return None


def parse_plaats_uit_url(url):
    """
    Bij /detail-annonce/ staat plaats meestal in de URL.

    Bijvoorbeeld:
    /givet-08600/...
    """

    match = re.search(
        r"/([^/]+)-(\d{5})/[^/]+/?$",
        url,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    plaats_slug = match.group(1)

    plaats = (
        plaats_slug
        .replace("-", " ")
        .strip()
        .title()
    )

    return plaats


# ============================================================
# AANTAL HOOFDRESULTATEN
# ============================================================

def bepaal_verwacht_aantal(soup):
    """
    Probeert aantal annonces uit titel en zichtbare tekst te halen.
    """

    bronnen = []

    if soup.title:
        bronnen.append(
            normale_tekst(soup.title.get_text())
        )

    bronnen.append(
        normale_tekst(
            soup.get_text(" ", strip=True)
        )
    )

    for tekst in bronnen:

        match = re.search(
            r"(\d+)\s+annonces?",
            tekst,
            flags=re.IGNORECASE,
        )

        if match:
            return int(match.group(1))

    return None


# ============================================================
# RESULTATENCONTAINER VINDEN
# ============================================================

def zoek_resultatencontainers(soup, verwacht_aantal):
    """
    Zoekt HTML-elementen die exact het verwachte aantal
    unieke detail-URLs bevatten.

    Het idee:
    - de hoofdresultaten hebben bijvoorbeeld 11 advertenties;
    - aanbevelingen staan meestal in een andere HTML-container;
    - we zoeken dus een element dat precies 11 detail-links omvat.
    """

    kandidaten = []

    relevante_tags = [
        "main",
        "section",
        "div",
        "ul",
        "ol",
    ]

    for element in soup.find_all(relevante_tags):

        urls = detail_urls_in_element(element)

        if len(urls) != verwacht_aantal:
            continue

        tekst = normale_tekst(
            element.get_text(" ", strip=True)
        )

        kandidaten.append(
            {
                "element": element,
                "tag": element.name,
                "class": element.get("class"),
                "id": element.get("id"),
                "urls": urls,
                "tekstlengte": len(tekst),
            }
        )

    # Kleinste container heeft meestal de minste extra rommel.
    kandidaten.sort(
        key=lambda item: item["tekstlengte"]
    )

    return kandidaten


# ============================================================
# INDIVIDUELE RESULTAATKAART
# ============================================================

def vind_kaart_voor_link(link_tag, resultatencontainer):
    """
    Loopt vanaf een advertentielink omhoog door de HTML.

    We zoeken de kleinste ancestor die:
    - binnen de hoofdresultatencontainer blijft;
    - precies één unieke detail-URL bevat;
    - een woningprijs bevat;
    - voldoende tekst bevat om een resultaatkaart te zijn.
    """

    kandidaat = link_tag

    while kandidaat is not None:

        if not isinstance(kandidaat, Tag):
            kandidaat = kandidaat.parent
            continue

        if kandidaat == resultatencontainer:
            break

        if kandidaat.name in [
            "article",
            "li",
            "div",
            "section",
        ]:

            urls = detail_urls_in_element(kandidaat)

            tekst = normale_tekst(
                kandidaat.get_text(
                    " ",
                    strip=True,
                )
            )

            prijs = parse_prijs(tekst)

            if (
                len(urls) == 1
                and prijs is not None
                and len(tekst) >= 20
            ):
                return kandidaat

        kandidaat = kandidaat.parent

    return None


# ============================================================
# WONINGRECORD
# ============================================================

def maak_woningrecord(kaart, url):
    tekst = normale_tekst(
        kaart.get_text(
            " ",
            strip=True,
        )
    )

    prijs = parse_prijs(tekst)
    postcode = parse_postcode(tekst)

    plaats = parse_plaats_uit_url(url)

    woonoppervlakte = parse_woonoppervlakte(
        tekst
    )

    terrain = parse_terrain(
        tekst
    )

    return {
        "url": url,
        "prijs": prijs,
        "postcode": postcode,
        "plaats": plaats,
        "woonoppervlakte": woonoppervlakte,
        "terrain": terrain,
        "tekst": tekst,
    }


# ============================================================
# HOOFDPROGRAMMA
# ============================================================

def main():

    print("=" * 76)
    print("TECHNISCHE TEST LOGIC-IMMO - FASE 3")
    print("=" * 76)

    print()
    print(f"Postcode       : {POSTCODE}")
    print(f"Plaats         : {PLAATS}")
    print(f"Minimumprijs   : {nette_prijs(MIN_PRIJS)}")
    print(f"Maximumprijs   : {nette_prijs(MAX_PRIJS)}")

    print()
    print("Zoek-URL:")
    print(ZOEK_URL)

    session = maak_session()

    # --------------------------------------------------------
    # 1. PAGINA OPHALEN
    # --------------------------------------------------------

    print()
    print("1. Zoekpagina ophalen...")

    try:
        response = session.get(
            ZOEK_URL,
            timeout=TIMEOUT,
        )

    except requests.RequestException as fout:

        print()
        print("FOUT bij ophalen:")
        print(fout)

        sys.exit(1)

    print(
        f"HTTP-status      : "
        f"{response.status_code}"
    )

    print(
        f"HTML grootte     : "
        f"{len(response.text):,} tekens"
    )

    if response.status_code != 200:
        print()
        print(
            "Zoekpagina kon niet normaal "
            "worden opgehaald."
        )
        sys.exit(1)

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    titel = ""

    if soup.title:
        titel = normale_tekst(
            soup.title.get_text()
        )

    print(
        f"Pagina titel     : "
        f"{titel}"
    )

    # --------------------------------------------------------
    # 2. VERWACHT AANTAL
    # --------------------------------------------------------

    print()
    print("2. Verwacht aantal hoofdadvertenties bepalen...")

    verwacht_aantal = bepaal_verwacht_aantal(
        soup
    )

    print(
        f"Logic-Immo meldt : "
        f"{verwacht_aantal}"
    )

    if verwacht_aantal is None:
        print()
        print(
            "FOUT: aantal advertenties kon "
            "niet worden vastgesteld."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # 3. CONTAINER ZOEKEN
    # --------------------------------------------------------

    print()
    print("3. HTML-container met hoofdresultaten zoeken...")

    kandidaten = zoek_resultatencontainers(
        soup,
        verwacht_aantal,
    )

    print(
        f"Kandidaatcontainers gevonden: "
        f"{len(kandidaten)}"
    )

    if not kandidaten:

        print()
        print(
            "Geen container gevonden met exact "
            f"{verwacht_aantal} detail-links."
        )

        print()
        print(
            "De HTML-structuur moet dan nog "
            "anders worden onderzocht."
        )

        sys.exit(1)

    print()

    for nummer, kandidaat in enumerate(
        kandidaten[:10],
        start=1,
    ):

        print(
            f"[{nummer}] "
            f"<{kandidaat['tag']}> "
            f"id={kandidaat['id']} "
            f"class={kandidaat['class']} "
            f"tekst={kandidaat['tekstlengte']} tekens"
        )

    # Kleinste kandidaat gebruiken.
    gekozen = kandidaten[0]

    resultatencontainer = gekozen[
        "element"
    ]

    hoofd_urls = gekozen[
        "urls"
    ]

    print()
    print("Gekozen container:")

    print(
        f"Tag              : "
        f"{gekozen['tag']}"
    )

    print(
        f"ID               : "
        f"{gekozen['id']}"
    )

    print(
        f"Class            : "
        f"{gekozen['class']}"
    )

    print(
        f"Detail-links     : "
        f"{len(hoofd_urls)}"
    )

    # --------------------------------------------------------
    # 4. RESULTAATKAARTEN
    # --------------------------------------------------------

    print()
    print("=" * 76)
    print("4. Resultaatkaarten analyseren")
    print("=" * 76)

    woningen = []

    for nummer, url in enumerate(
        hoofd_urls,
        start=1,
    ):

        link_tag = None

        for link in resultatencontainer.find_all(
            "a",
            href=True,
        ):

            volledige_url = urljoin(
                BASE_URL,
                link.get("href", ""),
            )

            if volledige_url == url:
                link_tag = link
                break

        if link_tag is None:

            print()
            print(
                f"[{nummer}] Geen link-tag "
                f"teruggevonden voor:"
            )
            print(url)
            continue

        kaart = vind_kaart_voor_link(
            link_tag,
            resultatencontainer,
        )

        if kaart is None:

            print()
            print(
                f"[{nummer}] Geen kaart "
                f"gevonden voor:"
            )
            print(url)
            continue

        record = maak_woningrecord(
            kaart,
            url,
        )

        woningen.append(record)

        binnen_range = (
            record["prijs"] is not None
            and MIN_PRIJS
            <= record["prijs"]
            <= MAX_PRIJS
        )

        status = (
            "MATCH"
            if binnen_range
            else "BUITEN PRIJSRANGE"
        )

        print()
        print(
            f"[{nummer:02}] {status}"
        )

        print(
            f"     Prijs        : "
            f"{nette_prijs(record['prijs'])}"
        )

        print(
            f"     Plaats       : "
            f"{record['plaats']}"
        )

        print(
            f"     Postcode     : "
            f"{record['postcode']}"
        )

        print(
            f"     Woonopp.     : "
            f"{record['woonoppervlakte']} m²"
        )

        print(
            f"     Terrain      : "
            f"{record['terrain']} m²"
        )

        print(
            f"     URL          : "
            f"{record['url']}"
        )

        print(
            f"     Tekst        : "
            f"{record['tekst'][:250]}"
        )

    # --------------------------------------------------------
    # 5. PRIJSFILTER
    # --------------------------------------------------------

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
    print("5. WONINGEN BINNEN PRIJSRANGE")
    print("=" * 76)

    if not matches:

        print()
        print("Geen woningen binnen prijsrange.")

    else:

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

    # --------------------------------------------------------
    # 6. DEBUG HTML
    # --------------------------------------------------------

    debug_bestand = (
        "logicimmo_resultatencontainer.html"
    )

    try:

        with open(
            debug_bestand,
            "w",
            encoding="utf-8",
        ) as bestand:

            bestand.write(
                str(resultatencontainer)
            )

        debug_opgeslagen = True

    except OSError:
        debug_opgeslagen = False

    # --------------------------------------------------------
    # SAMENVATTING
    # --------------------------------------------------------

    print()
    print("=" * 76)
    print("SAMENVATTING FASE 3")
    print("=" * 76)

    print(
        f"HTTP 200                  : "
        f"{response.status_code == 200}"
    )

    print(
        f"Logic-Immo advertenties   : "
        f"{verwacht_aantal}"
    )

    print(
        f"Hoofd-detail-URLs         : "
        f"{len(hoofd_urls)}"
    )

    print(
        f"Woningkaarten gevonden    : "
        f"{len(woningen)}"
    )

    print(
        f"Binnen €80k - €220k       : "
        f"{len(matches)}"
    )

    print(
        f"Debug HTML opgeslagen     : "
        f"{debug_opgeslagen}"
    )

    if debug_opgeslagen:

        print(
            f"Debug bestand             : "
            f"{debug_bestand}"
        )

    print()

    if (
        len(hoofd_urls) == verwacht_aantal
        and len(woningen) == verwacht_aantal
    ):

        print(
            "RESULTAAT: GESLAAGD"
        )

        print(
            "Precies het verwachte aantal "
            "hoofdwoningen is als record herkend."
        )

    else:

        print(
            "RESULTAAT: NOG NIET VOLLEDIG"
        )

        print(
            "De HTML-selectie moet nog "
            "worden aangescherpt."
        )

    print()
    print("=" * 76)


if __name__ == "__main__":
    main()
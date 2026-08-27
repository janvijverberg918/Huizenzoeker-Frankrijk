import time
from urllib.parse import urljoin, urlsplit, urlunsplit

from playwright.sync_api import sync_playwright

from config import (
    HEADLESS,
    PAGE_TIMEOUT,
    SLOW_MO,
)

from immovlan import (
    haal_foto_url_immovlan,
    prijs_naar_getal,
    voer_zoekopdracht_uit,
)


# ============================================================
# TESTINSTELLINGEN
# ============================================================

POSTCODE = "6980"
MUNICIPAL = "la-roche-en-ardenne"

WONINGTYPE = "huis"

MIN_PRIJS = 100000
MAX_PRIJS = 250000

BASE_URL = "https://immovlan.be"


# ============================================================
# URL HULPFUNCTIES
# ============================================================

def maak_directe_url():
    """
    Bouwt rechtstreeks de Immovlan-resultaten-URL.
    """

    return (
        "https://immovlan.be/nl/vastgoed"
        "?transactiontypes=te-koop,in-openbare-verkoop"
        "&propertytypes=huis"
        f"&municipals={MUNICIPAL}"
        f"&minprice={MIN_PRIJS}"
        f"&maxprice={MAX_PRIJS}"
        "&noindex=1"
    )


def normaliseer_url(url):
    """
    Maakt URLs geschikt voor een betrouwbare vergelijking.

    - relatieve URL wordt absoluut;
    - querystring wordt verwijderd;
    - fragment wordt verwijderd;
    - afsluitende slash wordt verwijderd.
    """

    if not url:
        return ""

    volledig = urljoin(
        BASE_URL,
        url,
    )

    delen = urlsplit(
        volledig
    )

    pad = (
        delen.path
        .rstrip("/")
    )

    return urlunsplit(
        (
            delen.scheme.lower(),
            delen.netloc.lower(),
            pad,
            "",
            "",
        )
    )


# ============================================================
# RESULTATEN UITLEZEN
# ============================================================

def lees_resultaten(
    page,
    min_prijs,
    max_prijs,
):
    """
    Leest de Immovlan-resultaatkaarten uit.

    Gebruikt voor zowel:
    - normale formuliermethode;
    - directe URL-methode.

    Daardoor vergelijken we beide methodes
    met exact dezelfde uitleeslogica.
    """

    cards = page.locator(
        "article"
    )

    aantal_cards = cards.count()

    resultaten = []

    aantal_buiten_prijs = 0
    aantal_zonder_prijs = 0
    aantal_zonder_link = 0
    aantal_onbruikbaar = 0

    for i in range(
        aantal_cards
    ):
        card = cards.nth(
            i
        )

        try:
            tekst = (
                card.inner_text()
                .strip()
            )

            if not tekst:
                aantal_onbruikbaar += 1
                continue

            regels = [
                regel.strip()
                for regel in tekst.splitlines()
                if regel.strip()
            ]

            if len(regels) < 3:
                aantal_onbruikbaar += 1
                continue

            prijs_tekst = regels[0]
            titel = regels[1]
            plaats = regels[2]

            # ------------------------------------------------
            # Prijs
            # ------------------------------------------------
            prijs = prijs_naar_getal(
                prijs_tekst
            )

            if prijs is None:
                aantal_zonder_prijs += 1
                continue

            if not (
                min_prijs
                <= prijs
                <= max_prijs
            ):
                aantal_buiten_prijs += 1
                continue

            # ------------------------------------------------
            # Detail-link
            # ------------------------------------------------
            details = card.get_by_text(
                "Details",
                exact=True,
            )

            if details.count() == 0:
                aantal_zonder_link += 1
                continue

            link = (
                details
                .first
                .get_attribute(
                    "href"
                )
            )

            if not link:
                aantal_zonder_link += 1
                continue

            absolute_link = urljoin(
                BASE_URL,
                link,
            )

            # ------------------------------------------------
            # Foto
            # ------------------------------------------------
            foto = haal_foto_url_immovlan(
                card
            )

            resultaten.append(
                {
                    "titel": titel,
                    "prijs": prijs,
                    "plaats": plaats,
                    "link": absolute_link,
                    "genormaliseerde_link": normaliseer_url(
                        absolute_link
                    ),
                    "foto": foto,
                }
            )

        except Exception as fout:
            aantal_onbruikbaar += 1

            print(
                f"Waarschuwing: kaart {i} "
                f"kon niet worden uitgelezen: {fout}"
            )

    return {
        "aantal_cards": aantal_cards,
        "resultaten": resultaten,
        "buiten_prijs": aantal_buiten_prijs,
        "zonder_prijs": aantal_zonder_prijs,
        "zonder_link": aantal_zonder_link,
        "onbruikbaar": aantal_onbruikbaar,
    }


# ============================================================
# NORMALE METHODE
# ============================================================

def test_normale_methode():
    """
    Voert de bestaande Immovlan-zoekmethode uit:

    startpagina
    -> interface
    -> woningtype
    -> postcode
    -> plaats
    -> prijs
    -> zoekknop
    -> resultaten.
    """

    print()
    print("=" * 70)
    print("1. NORMALE IMM0VLAN-METHODE")
    print("=" * 70)

    totaal_start = time.perf_counter()

    with sync_playwright() as p:
        browser_start = time.perf_counter()

        browser = p.chromium.launch(
            headless=HEADLESS,
            slow_mo=(
                0
                if HEADLESS
                else SLOW_MO
            ),
            args=[
                "--deny-permission-prompts",
            ],
        )

        page = browser.new_page()

        browser_tijd = (
            time.perf_counter()
            - browser_start
        )

        try:
            zoek_start = time.perf_counter()

            voer_zoekopdracht_uit(
                page,
                POSTCODE,
                WONINGTYPE,
                MIN_PRIJS,
                MAX_PRIJS,
            )

            zoek_tijd = (
                time.perf_counter()
                - zoek_start
            )

            uitlezen_start = time.perf_counter()

            resultaat = lees_resultaten(
                page,
                MIN_PRIJS,
                MAX_PRIJS,
            )

            uitlezen_tijd = (
                time.perf_counter()
                - uitlezen_start
            )

            werkelijke_url = page.url

        finally:
            browser.close()

    totaal_tijd = (
        time.perf_counter()
        - totaal_start
    )

    resultaat["browser_tijd"] = browser_tijd
    resultaat["zoek_tijd"] = zoek_tijd
    resultaat["uitlezen_tijd"] = uitlezen_tijd
    resultaat["totaal_tijd"] = totaal_tijd
    resultaat["werkelijke_url"] = werkelijke_url

    return resultaat


# ============================================================
# DIRECTE URL-METHODE
# ============================================================

def test_directe_methode():
    """
    Opent rechtstreeks de resultaten-URL.
    """

    print()
    print("=" * 70)
    print("2. DIRECTE URL-METHODE")
    print("=" * 70)

    directe_url = maak_directe_url()

    print()
    print("Directe URL:")
    print(directe_url)

    totaal_start = time.perf_counter()

    with sync_playwright() as p:
        browser_start = time.perf_counter()

        browser = p.chromium.launch(
            headless=HEADLESS,
            slow_mo=(
                0
                if HEADLESS
                else SLOW_MO
            ),
            args=[
                "--deny-permission-prompts",
            ],
        )

        page = browser.new_page()

        browser_tijd = (
            time.perf_counter()
            - browser_start
        )

        try:
            laden_start = time.perf_counter()

            page.goto(
                directe_url,
                wait_until="domcontentloaded",
                timeout=PAGE_TIMEOUT,
            )

            laden_tijd = (
                time.perf_counter()
                - laden_start
            )

            uitlezen_start = time.perf_counter()

            resultaat = lees_resultaten(
                page,
                MIN_PRIJS,
                MAX_PRIJS,
            )

            uitlezen_tijd = (
                time.perf_counter()
                - uitlezen_start
            )

            werkelijke_url = page.url

        finally:
            browser.close()

    totaal_tijd = (
        time.perf_counter()
        - totaal_start
    )

    resultaat["browser_tijd"] = browser_tijd
    resultaat["zoek_tijd"] = laden_tijd
    resultaat["uitlezen_tijd"] = uitlezen_tijd
    resultaat["totaal_tijd"] = totaal_tijd
    resultaat["werkelijke_url"] = werkelijke_url

    return resultaat


# ============================================================
# RESULTAAT TONEN
# ============================================================

def toon_methode_resultaat(
    naam,
    resultaat,
):
    print()
    print("-" * 70)
    print(naam)
    print("-" * 70)

    print(
        f"Article-elementen       : "
        f"{resultaat['aantal_cards']}"
    )

    print(
        f"Passende woningen       : "
        f"{len(resultaat['resultaten'])}"
    )

    print(
        f"Buiten prijsrange       : "
        f"{resultaat['buiten_prijs']}"
    )

    print(
        f"Zonder bruikbare prijs  : "
        f"{resultaat['zonder_prijs']}"
    )

    print(
        f"Zonder detail-link      : "
        f"{resultaat['zonder_link']}"
    )

    print(
        f"Onbruikbare kaarten     : "
        f"{resultaat['onbruikbaar']}"
    )

    print()
    print(
        f"Browser starten         : "
        f"{resultaat['browser_tijd']:.2f} s"
    )

    print(
        f"Zoeken / URL laden      : "
        f"{resultaat['zoek_tijd']:.2f} s"
    )

    print(
        f"Resultaten uitlezen     : "
        f"{resultaat['uitlezen_tijd']:.2f} s"
    )

    print(
        f"TOTAAL                   : "
        f"{resultaat['totaal_tijd']:.2f} s"
    )


# ============================================================
# WONINGEN VERGELIJKEN
# ============================================================

def vergelijk_resultaten(
    normaal,
    direct,
):
    normale_urls = {
        woning[
            "genormaliseerde_link"
        ]
        for woning in normaal[
            "resultaten"
        ]
    }

    directe_urls = {
        woning[
            "genormaliseerde_link"
        ]
        for woning in direct[
            "resultaten"
        ]
    }

    ontbreekt_direct = (
        normale_urls
        - directe_urls
    )

    extra_direct = (
        directe_urls
        - normale_urls
    )

    exact_gelijk = (
        normale_urls
        == directe_urls
    )

    print()
    print("=" * 70)
    print("3. VERGELIJKING WONINGEN")
    print("=" * 70)

    print(
        f"Normale methode         : "
        f"{len(normale_urls)} unieke woning-URLs"
    )

    print(
        f"Directe methode         : "
        f"{len(directe_urls)} unieke woning-URLs"
    )

    print()

    print(
        "Exact dezelfde woningen : "
        + (
            "JA"
            if exact_gelijk
            else "NEE"
        )
    )

    print(
        f"Ontbreken in direct     : "
        f"{len(ontbreekt_direct)}"
    )

    print(
        f"Extra in direct         : "
        f"{len(extra_direct)}"
    )

    if ontbreekt_direct:
        print()
        print(
            "WONINGEN DIE ONTBREKEN "
            "IN DIRECTE METHODE"
        )
        print("-" * 70)

        for url in sorted(
            ontbreekt_direct
        ):
            print(url)

    if extra_direct:
        print()
        print(
            "EXTRA WONINGEN IN "
            "DIRECTE METHODE"
        )
        print("-" * 70)

        for url in sorted(
            extra_direct
        ):
            print(url)

    return exact_gelijk


# ============================================================
# PERFORMANCE VERGELIJKEN
# ============================================================

def vergelijk_performance(
    normaal,
    direct,
):
    oude_tijd = normaal[
        "totaal_tijd"
    ]

    nieuwe_tijd = direct[
        "totaal_tijd"
    ]

    besparing = (
        oude_tijd
        - nieuwe_tijd
    )

    if oude_tijd > 0:
        procent = (
            besparing
            / oude_tijd
            * 100
        )

        factor = (
            oude_tijd
            / nieuwe_tijd
            if nieuwe_tijd > 0
            else 0
        )

    else:
        procent = 0
        factor = 0

    print()
    print("=" * 70)
    print("4. PERFORMANCEVERGELIJKING")
    print("=" * 70)

    print(
        f"Normale methode         : "
        f"{oude_tijd:.2f} seconden"
    )

    print(
        f"Directe methode         : "
        f"{nieuwe_tijd:.2f} seconden"
    )

    print(
        f"Besparing               : "
        f"{besparing:.2f} seconden"
    )

    print(
        f"Besparing procentueel   : "
        f"{procent:.1f}%"
    )

    print(
        f"Snelheidsfactor         : "
        f"{factor:.2f}x"
    )


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("=" * 70)
    print("IMMOVLAN VERGELIJKINGSTEST")
    print("=" * 70)

    print(
        f"Postcode                : "
        f"{POSTCODE}"
    )

    print(
        f"Municipal               : "
        f"{MUNICIPAL}"
    )

    print(
        f"Prijsrange              : "
        f"{MIN_PRIJS} - {MAX_PRIJS}"
    )

    # --------------------------------------------------------
    # Normale methode
    # --------------------------------------------------------
    normaal = test_normale_methode()

    # --------------------------------------------------------
    # Directe methode
    # --------------------------------------------------------
    direct = test_directe_methode()

    # --------------------------------------------------------
    # Resultaten
    # --------------------------------------------------------
    toon_methode_resultaat(
        "NORMALE METHODE",
        normaal,
    )

    toon_methode_resultaat(
        "DIRECTE URL-METHODE",
        direct,
    )

    # --------------------------------------------------------
    # Vergelijk woningen
    # --------------------------------------------------------
    exact_gelijk = vergelijk_resultaten(
        normaal,
        direct,
    )

    # --------------------------------------------------------
    # Vergelijk performance
    # --------------------------------------------------------
    vergelijk_performance(
        normaal,
        direct,
    )

    print()
    print("=" * 70)
    print("EINDCONCLUSIE")
    print("=" * 70)

    if exact_gelijk:
        print(
            "TEST GESLAAGD: beide methodes "
            "vinden exact dezelfde woningen."
        )
    else:
        print(
            "TEST NIET GESLAAGD: "
            "de gevonden woningen verschillen."
        )

    print()
    print(
        "immovlan.py is door deze test "
        "NIET gewijzigd."
    )

    print("=" * 70)


if __name__ == "__main__":
    main()
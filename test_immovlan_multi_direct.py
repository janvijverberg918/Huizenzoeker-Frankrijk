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

WONINGTYPE = "huis"
MIN_PRIJS = 100000
MAX_PRIJS = 250000
BASE_URL = "https://immovlan.be"

TESTGEBIEDEN = [
    {
        "naam": "La Roche-en-Ardenne",
        "postcode": "6980",
        "municipal": "la-roche-en-ardenne",
    },
    {
        "naam": "Vielsalm",
        "postcode": "6690",
        "municipal": "vielsalm",
    },
    {
        "naam": "Saint-Hubert",
        "postcode": "6870",
        "municipal": "saint-hubert",
    },
    {
        "naam": "Bouillon",
        "postcode": "6830",
        "municipal": "bouillon",
    },
    {
        "naam": "Spa",
        "postcode": "4900",
        "municipal": "spa",
    },
]


# ============================================================
# URL HULPFUNCTIES
# ============================================================

def maak_directe_url(municipal):
    return (
        "https://immovlan.be/nl/vastgoed"
        "?transactiontypes=te-koop,in-openbare-verkoop"
        "&propertytypes=huis"
        f"&municipals={municipal}"
        f"&minprice={MIN_PRIJS}"
        f"&maxprice={MAX_PRIJS}"
        "&noindex=1"
    )


def normaliseer_url(url):
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

def lees_resultaten(page):
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
        card = cards.nth(i)

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

            prijs = prijs_naar_getal(
                prijs_tekst
            )

            if prijs is None:
                aantal_zonder_prijs += 1
                continue

            if not (
                MIN_PRIJS
                <= prijs
                <= MAX_PRIJS
            ):
                aantal_buiten_prijs += 1
                continue

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
                f"Waarschuwing kaart {i}: {fout}"
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

def voer_normale_test_uit(gebied):
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
                gebied["postcode"],
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
                page
            )

            uitlezen_tijd = (
                time.perf_counter()
                - uitlezen_start
            )

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

    return resultaat


# ============================================================
# DIRECTE URL-METHODE
# ============================================================

def voer_directe_test_uit(gebied):
    directe_url = maak_directe_url(
        gebied["municipal"]
    )

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
                page
            )

            uitlezen_tijd = (
                time.perf_counter()
                - uitlezen_start
            )

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
    resultaat["directe_url"] = directe_url

    return resultaat


# ============================================================
# VERGELIJKING
# ============================================================

def vergelijk_woningen(normaal, direct):
    normale_urls = {
        woning["genormaliseerde_link"]
        for woning in normaal["resultaten"]
    }

    directe_urls = {
        woning["genormaliseerde_link"]
        for woning in direct["resultaten"]
    }

    ontbreekt_direct = (
        normale_urls
        - directe_urls
    )

    extra_direct = (
        directe_urls
        - normale_urls
    )

    return {
        "normale_urls": normale_urls,
        "directe_urls": directe_urls,
        "ontbreekt_direct": ontbreekt_direct,
        "extra_direct": extra_direct,
        "veilig": (
            len(ontbreekt_direct) == 0
        ),
    }


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("=" * 90)
    print("IMMOVLAN MULTI-POSTCODE VERGELIJKINGSTEST")
    print("=" * 90)

    resultaten_overzicht = []

    totaal_normaal_tijd = 0.0
    totaal_direct_tijd = 0.0

    totaal_normale_woningen = 0
    totaal_directe_woningen = 0

    totaal_ontbrekend = 0
    totaal_extra = 0

    alle_veilig = True

    for nummer, gebied in enumerate(
        TESTGEBIEDEN,
        start=1,
    ):
        print()
        print("=" * 90)
        print(
            f"[{nummer}/{len(TESTGEBIEDEN)}] "
            f"{gebied['naam']} "
            f"({gebied['postcode']})"
        )
        print("=" * 90)

        print()
        print("Normale methode wordt uitgevoerd...")

        normaal = voer_normale_test_uit(
            gebied
        )

        print(
            f"Normaal gevonden: "
            f"{len(normaal['resultaten'])}"
        )

        print(
            f"Normale tijd    : "
            f"{normaal['totaal_tijd']:.2f} s"
        )

        print()
        print("Directe URL-methode wordt uitgevoerd...")

        direct = voer_directe_test_uit(
            gebied
        )

        print(
            f"Direct gevonden : "
            f"{len(direct['resultaten'])}"
        )

        print(
            f"Directe tijd    : "
            f"{direct['totaal_tijd']:.2f} s"
        )

        vergelijking = vergelijk_woningen(
            normaal,
            direct,
        )

        ontbreekt = len(
            vergelijking[
                "ontbreekt_direct"
            ]
        )

        extra = len(
            vergelijking[
                "extra_direct"
            ]
        )

        veilig = vergelijking[
            "veilig"
        ]

        print()
        print(
            f"Ontbreekt direct: {ontbreekt}"
        )

        print(
            f"Extra direct    : {extra}"
        )

        print(
            "Veilig           : "
            + (
                "JA"
                if veilig
                else "NEE"
            )
        )

        if vergelijking[
            "ontbreekt_direct"
        ]:
            print()
            print(
                "ONTBREKENDE WONINGEN"
            )
            print("-" * 90)

            for url in sorted(
                vergelijking[
                    "ontbreekt_direct"
                ]
            ):
                print(url)

        if vergelijking[
            "extra_direct"
        ]:
            print()
            print(
                "EXTRA WONINGEN VIA DIRECT"
            )
            print("-" * 90)

            for url in sorted(
                vergelijking[
                    "extra_direct"
                ]
            ):
                print(url)

        resultaten_overzicht.append(
            {
                "postcode": gebied[
                    "postcode"
                ],
                "naam": gebied[
                    "naam"
                ],
                "normaal": len(
                    normaal[
                        "resultaten"
                    ]
                ),
                "direct": len(
                    direct[
                        "resultaten"
                    ]
                ),
                "ontbreekt": ontbreekt,
                "extra": extra,
                "veilig": veilig,
                "normaal_tijd": normaal[
                    "totaal_tijd"
                ],
                "direct_tijd": direct[
                    "totaal_tijd"
                ],
            }
        )

        totaal_normaal_tijd += normaal[
            "totaal_tijd"
        ]

        totaal_direct_tijd += direct[
            "totaal_tijd"
        ]

        totaal_normale_woningen += len(
            normaal[
                "resultaten"
            ]
        )

        totaal_directe_woningen += len(
            direct[
                "resultaten"
            ]
        )

        totaal_ontbrekend += ontbreekt
        totaal_extra += extra

        if not veilig:
            alle_veilig = False

    print()
    print("=" * 90)
    print("SAMENVATTING")
    print("=" * 90)

    print()
    print(
        f"{'Postcode':<10}"
        f"{'Plaats':<24}"
        f"{'Normaal':>9}"
        f"{'Direct':>9}"
        f"{'Ontbr.':>9}"
        f"{'Extra':>8}"
        f"{'Oud tijd':>12}"
        f"{'Direct':>12}"
    )

    print("-" * 90)

    for item in resultaten_overzicht:
        print(
            f"{item['postcode']:<10}"
            f"{item['naam']:<24}"
            f"{item['normaal']:>9}"
            f"{item['direct']:>9}"
            f"{item['ontbreekt']:>9}"
            f"{item['extra']:>8}"
            f"{item['normaal_tijd']:>10.2f}s"
            f"{item['direct_tijd']:>10.2f}s"
        )

    print("-" * 90)

    aantal_gebieden = len(
        TESTGEBIEDEN
    )

    gemiddeld_normaal = (
        totaal_normaal_tijd
        / aantal_gebieden
    )

    gemiddeld_direct = (
        totaal_direct_tijd
        / aantal_gebieden
    )

    besparing = (
        totaal_normaal_tijd
        - totaal_direct_tijd
    )

    if totaal_normaal_tijd > 0:
        winst_procent = (
            besparing
            / totaal_normaal_tijd
            * 100
        )
    else:
        winst_procent = 0.0

    print()
    print(
        f"Geteste zoekgebieden             : "
        f"{aantal_gebieden}"
    )

    print(
        f"Woningen normale methode         : "
        f"{totaal_normale_woningen}"
    )

    print(
        f"Woningen directe methode         : "
        f"{totaal_directe_woningen}"
    )

    print(
        f"Ontbrekende woningen in direct   : "
        f"{totaal_ontbrekend}"
    )

    print(
        f"Extra woningen via direct        : "
        f"{totaal_extra}"
    )

    print()
    print(
        f"Totale tijd normale methode      : "
        f"{totaal_normaal_tijd:.2f} s"
    )

    print(
        f"Totale tijd directe methode      : "
        f"{totaal_direct_tijd:.2f} s"
    )

    print(
        f"Gemiddelde tijd normaal          : "
        f"{gemiddeld_normaal:.2f} s"
    )

    print(
        f"Gemiddelde tijd direct           : "
        f"{gemiddeld_direct:.2f} s"
    )

    print(
        f"Totale tijdsbesparing            : "
        f"{besparing:.2f} s"
    )

    print(
        f"Performancewinst                 : "
        f"{winst_procent:.1f}%"
    )

    print()
    print("=" * 90)

    if alle_veilig:
        print(
            "DIRECTE METHODE VEILIG: JA"
        )
        print(
            "Geen woning uit de normale methode "
            "ontbreekt in de directe methode."
        )
    else:
        print(
            "DIRECTE METHODE VEILIG: NEE"
        )
        print(
            "Minimaal één woning uit de normale "
            "methode ontbreekt."
        )

    print("=" * 90)

    print()
    print(
        "immovlan.py is door deze test "
        "NIET gewijzigd."
    )


if __name__ == "__main__":
    main()
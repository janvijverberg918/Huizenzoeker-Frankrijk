import time
from urllib.parse import urljoin, urlsplit, urlunsplit

from playwright.sync_api import sync_playwright

from config import (
    HEADLESS,
    PAGE_TIMEOUT,
    SLOW_MO,
)

from immovlan import (
    prijs_naar_getal,
    voer_zoekopdracht_uit,
)


# ============================================================
# INSTELLINGEN
# ============================================================

BASE_URL = "https://immovlan.be"

WONINGTYPE = "huis"
MIN_PRIJS = 100000
MAX_PRIJS = 250000


# Door Immovlan zelf geleerde municipals.
IMMOVLAN_MUNICIPALS = {
    "6940": "durbuy",
    "6980": "la-roche-en-ardenne",
    "6660": "houffalize",
    "6997": "erezee",
    "6960": "manhay",
    "6987": "rendeux",
    "6690": "vielsalm",
    "6670": "gouvy",
    "6600": "bastogne",
    "6680": "sainte-ode",
    "6870": "saint-hubert",
    "6800": "libramont-chevigny",
    "6950": "nassogne",
    "6900": "marche-en-famenne",
    "5580": "rochefort",
    "6927": "tellin",
    "6929": "daverdisse",
    "6890": "libin",
    "6840": "neufchateau",
    "6640": "vaux-sur-sure",
    "6860": "leglise",
    "6637": "fauvillers",
    "6830": "bouillon",
    "6880": "bertrix",
    "6850": "paliseul",
    "6887": "herbeumont",
    "5555": "bievre",
    "5575": "gedinne",
    "5550": "vresse-sur-semois",
}


NAMEN = {
    "6940": "Durbuy",
    "6980": "La Roche-en-Ardenne",
    "6660": "Houffalize",
    "6997": "Érezée",
    "6960": "Manhay",
    "6987": "Rendeux",
    "6690": "Vielsalm",
    "6670": "Gouvy",
    "6600": "Bastogne",
    "6680": "Sainte-Ode",
    "6870": "Saint-Hubert",
    "6800": "Libramont-Chevigny",
    "6950": "Nassogne",
    "6900": "Marche-en-Famenne",
    "5580": "Rochefort",
    "6927": "Tellin",
    "6929": "Daverdisse",
    "6890": "Libin",
    "6840": "Neufchâteau",
    "6640": "Vaux-sur-Sûre",
    "6860": "Léglise",
    "6637": "Fauvillers",
    "6830": "Bouillon",
    "6880": "Bertrix",
    "6850": "Paliseul",
    "6887": "Herbeumont",
    "5555": "Bièvre",
    "5575": "Gedinne",
    "5550": "Vresse-sur-Semois",
}


# Deze twee hebben geen bruikbare municipal opgeleverd.
ALTIJD_FALLBACK = {
    "6630": "Martelange",
    "4900": "Spa",
}


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

    pad = delen.path.rstrip("/")

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

def lees_woning_urls(page):
    """
    Leest de Immovlan-resultaatkaarten uit en geeft alleen
    woningen binnen onze prijsrange terug.

    We vergelijken bewust op detail-URL.
    """

    cards = page.locator(
        "article"
    )

    aantal_cards = cards.count()

    urls = set()

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

            prijs = prijs_naar_getal(
                regels[0]
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

            urls.add(
                normaliseer_url(
                    link
                )
            )

        except Exception as fout:
            aantal_onbruikbaar += 1

            print(
                f"Waarschuwing kaart {i}: "
                f"{fout}"
            )

    return {
        "aantal_cards": aantal_cards,
        "urls": urls,
        "buiten_prijs": aantal_buiten_prijs,
        "zonder_prijs": aantal_zonder_prijs,
        "zonder_link": aantal_zonder_link,
        "onbruikbaar": aantal_onbruikbaar,
    }


# ============================================================
# NORMALE METHODE
# ============================================================

def normale_methode(
    browser,
    postcode,
):
    page = browser.new_page()

    start = time.perf_counter()

    try:
        voer_zoekopdracht_uit(
            page,
            postcode,
            WONINGTYPE,
            MIN_PRIJS,
            MAX_PRIJS,
        )

        resultaat = lees_woning_urls(
            page
        )

    finally:
        page.close()

    resultaat["tijd"] = (
        time.perf_counter()
        - start
    )

    return resultaat


# ============================================================
# DIRECTE METHODE
# ============================================================

def directe_methode(
    browser,
    municipal,
):
    page = browser.new_page()

    start = time.perf_counter()

    url = maak_directe_url(
        municipal
    )

    try:
        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=PAGE_TIMEOUT,
        )

        resultaat = lees_woning_urls(
            page
        )

    finally:
        page.close()

    resultaat["tijd"] = (
        time.perf_counter()
        - start
    )

    resultaat["url"] = url

    return resultaat


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("=" * 100)
    print("IMMOVLAN DIRECTE URL - VALIDATIE 29 POSTCODES")
    print("=" * 100)

    veilig_direct = {}
    fallback = dict(
        ALTIJD_FALLBACK
    )

    overzicht = []

    totale_tijd_normaal = 0.0
    totale_tijd_direct = 0.0

    totaal_normaal = 0
    totaal_direct = 0

    totaal_ontbrekend = 0
    totaal_extra = 0

    totaal_start = time.perf_counter()

    with sync_playwright() as p:
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

        try:
            totaal = len(
                IMMOVLAN_MUNICIPALS
            )

            for nummer, (
                postcode,
                municipal,
            ) in enumerate(
                IMMOVLAN_MUNICIPALS.items(),
                start=1,
            ):
                naam = NAMEN.get(
                    postcode,
                    postcode,
                )

                print()
                print("=" * 100)

                print(
                    f"[{nummer}/{totaal}] "
                    f"{naam} ({postcode})"
                )

                print("=" * 100)

                # ------------------------------------------------
                # Normale methode
                # ------------------------------------------------
                print(
                    "Normale methode..."
                )

                try:
                    normaal = normale_methode(
                        browser,
                        postcode,
                    )

                except Exception as fout:
                    print(
                        "NORMALE METHODE MISLUKT:"
                    )

                    print(fout)

                    fallback[
                        postcode
                    ] = naam

                    overzicht.append(
                        {
                            "postcode": postcode,
                            "naam": naam,
                            "normaal": None,
                            "direct": None,
                            "ontbreekt": None,
                            "extra": None,
                            "normaal_tijd": None,
                            "direct_tijd": None,
                            "status": (
                                "NORMALE TEST MISLUKT"
                            ),
                        }
                    )

                    continue

                # ------------------------------------------------
                # Directe methode
                # ------------------------------------------------
                print(
                    "Directe methode..."
                )

                try:
                    direct = directe_methode(
                        browser,
                        municipal,
                    )

                except Exception as fout:
                    print(
                        "DIRECTE METHODE MISLUKT:"
                    )

                    print(fout)

                    fallback[
                        postcode
                    ] = naam

                    overzicht.append(
                        {
                            "postcode": postcode,
                            "naam": naam,
                            "normaal": len(
                                normaal["urls"]
                            ),
                            "direct": None,
                            "ontbreekt": None,
                            "extra": None,
                            "normaal_tijd": normaal[
                                "tijd"
                            ],
                            "direct_tijd": None,
                            "status": (
                                "DIRECT MISLUKT"
                            ),
                        }
                    )

                    continue

                # ------------------------------------------------
                # Vergelijken
                # ------------------------------------------------
                normale_urls = normaal[
                    "urls"
                ]

                directe_urls = direct[
                    "urls"
                ]

                ontbreekt = (
                    normale_urls
                    - directe_urls
                )

                extra = (
                    directe_urls
                    - normale_urls
                )

                veilig = (
                    len(ontbreekt) == 0
                )

                if veilig:
                    veilig_direct[
                        postcode
                    ] = municipal

                    status = "DIRECT VEILIG"

                else:
                    fallback[
                        postcode
                    ] = naam

                    status = "FALLBACK"

                aantal_normaal = len(
                    normale_urls
                )

                aantal_direct = len(
                    directe_urls
                )

                totaal_normaal += (
                    aantal_normaal
                )

                totaal_direct += (
                    aantal_direct
                )

                totaal_ontbrekend += len(
                    ontbreekt
                )

                totaal_extra += len(
                    extra
                )

                totale_tijd_normaal += normaal[
                    "tijd"
                ]

                totale_tijd_direct += direct[
                    "tijd"
                ]

                overzicht.append(
                    {
                        "postcode": postcode,
                        "naam": naam,
                        "normaal": aantal_normaal,
                        "direct": aantal_direct,
                        "ontbreekt": len(
                            ontbreekt
                        ),
                        "extra": len(
                            extra
                        ),
                        "normaal_tijd": normaal[
                            "tijd"
                        ],
                        "direct_tijd": direct[
                            "tijd"
                        ],
                        "status": status,
                    }
                )

                print()
                print(
                    f"Normaal    : "
                    f"{aantal_normaal}"
                )

                print(
                    f"Direct     : "
                    f"{aantal_direct}"
                )

                print(
                    f"Ontbreekt  : "
                    f"{len(ontbreekt)}"
                )

                print(
                    f"Extra      : "
                    f"{len(extra)}"
                )

                print(
                    f"Normaal tijd: "
                    f"{normaal['tijd']:.2f} s"
                )

                print(
                    f"Direct tijd : "
                    f"{direct['tijd']:.2f} s"
                )

                print(
                    f"Status      : "
                    f"{status}"
                )

                if ontbreekt:
                    print()
                    print(
                        "ONTBREKENDE WONINGEN"
                    )

                    print("-" * 100)

                    for url in sorted(
                        ontbreekt
                    ):
                        print(url)

                if extra:
                    print()
                    print(
                        "EXTRA WONINGEN VIA DIRECT"
                    )

                    print("-" * 100)

                    for url in sorted(
                        extra
                    ):
                        print(url)

        finally:
            browser.close()

    totale_testtijd = (
        time.perf_counter()
        - totaal_start
    )

    # ========================================================
    # OVERZICHT
    # ========================================================

    print()
    print("=" * 100)
    print("SAMENVATTING")
    print("=" * 100)

    print()
    print(
        f"{'Postcode':<10}"
        f"{'Plaats':<24}"
        f"{'Norm':>6}"
        f"{'Dir':>6}"
        f"{'Mist':>6}"
        f"{'Extra':>7}"
        f"{'Norm s':>10}"
        f"{'Dir s':>10}"
        f"  Status"
    )

    print("-" * 100)

    for item in overzicht:
        normaal_tekst = (
            str(item["normaal"])
            if item["normaal"] is not None
            else "-"
        )

        direct_tekst = (
            str(item["direct"])
            if item["direct"] is not None
            else "-"
        )

        ontbreekt_tekst = (
            str(item["ontbreekt"])
            if item["ontbreekt"] is not None
            else "-"
        )

        extra_tekst = (
            str(item["extra"])
            if item["extra"] is not None
            else "-"
        )

        normaal_tijd = (
            f"{item['normaal_tijd']:.2f}"
            if item["normaal_tijd"] is not None
            else "-"
        )

        direct_tijd = (
            f"{item['direct_tijd']:.2f}"
            if item["direct_tijd"] is not None
            else "-"
        )

        print(
            f"{item['postcode']:<10}"
            f"{item['naam']:<24}"
            f"{normaal_tekst:>6}"
            f"{direct_tekst:>6}"
            f"{ontbreekt_tekst:>6}"
            f"{extra_tekst:>7}"
            f"{normaal_tijd:>10}"
            f"{direct_tijd:>10}"
            f"  {item['status']}"
        )

    print("-" * 100)

    # ========================================================
    # PERFORMANCE
    # ========================================================

    print()
    print(
        f"Postcodes getest via mapping    : "
        f"{len(IMMOVLAN_MUNICIPALS)}"
    )

    print(
        f"Direct veilig                   : "
        f"{len(veilig_direct)}"
    )

    print(
        f"Fallback totaal                 : "
        f"{len(fallback)}"
    )

    print(
        f"  waarvan zonder municipal      : "
        f"{len(ALTIJD_FALLBACK)}"
    )

    print()
    print(
        f"Woningen normale methode        : "
        f"{totaal_normaal}"
    )

    print(
        f"Woningen directe methode        : "
        f"{totaal_direct}"
    )

    print(
        f"Ontbrekende woningen direct     : "
        f"{totaal_ontbrekend}"
    )

    print(
        f"Extra woningen direct           : "
        f"{totaal_extra}"
    )

    print()
    print(
        f"Totale tijd normale methode     : "
        f"{totale_tijd_normaal:.2f} s"
    )

    print(
        f"Totale tijd directe methode     : "
        f"{totale_tijd_direct:.2f} s"
    )

    if totale_tijd_normaal > 0:
        besparing = (
            totale_tijd_normaal
            - totale_tijd_direct
        )

        winst = (
            besparing
            / totale_tijd_normaal
            * 100
        )

    else:
        besparing = 0
        winst = 0

    print(
        f"Tijdsbesparing op geteste set   : "
        f"{besparing:.2f} s"
    )

    print(
        f"Performancewinst                : "
        f"{winst:.1f}%"
    )

    print(
        f"Totale duur validatietest       : "
        f"{totale_testtijd:.1f} s"
    )

    # ========================================================
    # PRODUCTIELIJSTEN
    # ========================================================

    print()
    print("=" * 100)
    print("IMMOVLAN_DIRECT_VEILIG")
    print("=" * 100)

    print()
    print(
        "IMMOVLAN_DIRECT_VEILIG = {"
    )

    for postcode in sorted(
        veilig_direct
    ):
        print(
            f'    "{postcode}": '
            f'"{veilig_direct[postcode]}",'
        )

    print("}")

    print()
    print("=" * 100)
    print("IMMOVLAN_NORMALE_FALLBACK")
    print("=" * 100)

    print()
    print(
        "IMMOVLAN_NORMALE_FALLBACK = {"
    )

    for postcode in sorted(
        fallback
    ):
        print(
            f'    "{postcode}": '
            f'"{fallback[postcode]}",'
        )

    print("}")

    print()
    print("=" * 100)
    print("EINDRESULTAAT")
    print("=" * 100)

    if veilig_direct:
        print(
            f"{len(veilig_direct)} postcode(s) "
            f"kunnen de snelle directe route gebruiken."
        )

    if fallback:
        print(
            f"{len(fallback)} postcode(s) "
            f"blijven op de normale veilige route."
        )

    print()
    print(
        "immovlan.py is door deze validatietest "
        "NIET gewijzigd."
    )

    print("=" * 100)


if __name__ == "__main__":
    main()
"""
test_bienici_detail.py

Bien'ici technische detailtest - fase 3A.

Doel:
- één detailadvertentie openen met Playwright;
- cookies accepteren;
- controleren op anti-bot/challenge;
- detailpagina-HTML opslaan;
- inventariseren welke woningkenmerken aanwezig zijn;
- nog geen definitieve detailparser bouwen.

Nog GEEN:
- CSV
- historie
- AI
- e-mail
- integratie in huizenzoeker.py
"""

import re
import time

from bs4 import BeautifulSoup
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


# ============================================================
# TESTCONFIGURATIE
# ============================================================

# Deze woning kwam in fase 2 binnen de prijsrange voor.
DETAIL_URL = (
    "https://www.bienici.com/annonce/vente/givet/maison/"
    "5pieces/iad-france-980261"
)

PLAYWRIGHT_TIMEOUT = 45_000


# ============================================================
# HELPERS
# ============================================================

def normale_tekst(tekst):
    if not tekst:
        return ""

    tekst = tekst.replace("\xa0", " ")
    tekst = tekst.replace("\u202f", " ")
    tekst = re.sub(r"\s+", " ", tekst)

    return tekst.strip()


def herken_mogelijke_blokkade(tekst):
    """
    Alleen diagnostiek.
    Er wordt niets omzeild.
    """

    tekst = normale_tekst(
        tekst
    ).lower()

    signalen = [
        "captcha",
        "robot",
        "verify you are human",
        "vérifier que vous êtes humain",
        "verification",
        "vérification",
        "access denied",
        "accès refusé",
        "forbidden",
        "datadome",
        "cloudflare",
        "security check",
        "challenge",
    ]

    return [
        signaal
        for signaal in signalen
        if signaal in tekst
    ]


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
# INVENTARISATIE
# ============================================================

def zoek_termen(tekst):
    """
    Controleert welke voor Frankrijk relevante termen
    daadwerkelijk in de detailpagina voorkomen.

    Dit is nog geen parser.
    """

    tekst_lower = normale_tekst(
        tekst
    ).lower()

    termen = {
        "dpe": [
            "dpe",
            "diagnostic de performance énergétique",
            "classe énergie",
            "classe energetique",
            "classe énergétique",
        ],

        "ges": [
            "ges",
            "classe climat",
            "gaz à effet de serre",
        ],

        "terrain": [
            "terrain",
            "parcelle",
        ],

        "garage": [
            "garage",
        ],

        "dependances": [
            "dépendance",
            "dépendances",
            "dependance",
            "dependances",
            "annexe",
            "grange",
            "atelier",
        ],

        "assainissement": [
            "assainissement",
            "tout-à-l'égout",
            "tout à l'égout",
            "tout a l'egout",
            "fosse septique",
        ],

        "travaux": [
            "travaux",
            "à rénover",
            "a renover",
            "rénové",
            "renove",
            "rénovation",
            "renovation",
        ],

        "chauffage": [
            "chauffage",
            "radiateur",
            "pompe à chaleur",
            "gaz",
            "fioul",
            "mazout",
            "électrique",
            "electrique",
            "bois",
        ],

        "annee_construction": [
            "année de construction",
            "annee de construction",
            "construit en",
            "construite en",
        ],

        "jardin": [
            "jardin",
        ],

        "terrasse": [
            "terrasse",
        ],

        "parking": [
            "parking",
            "stationnement",
        ],
    }

    resultaten = {}

    for kenmerk, zoektermen in termen.items():

        gevonden = []

        for zoekterm in zoektermen:

            if zoekterm in tekst_lower:
                gevonden.append(
                    zoekterm
                )

        resultaten[
            kenmerk
        ] = gevonden

    return resultaten


def toon_context_rond_term(
    tekst,
    term,
    lengte=180,
):
    """
    Geeft een kort tekstfragment rond een term.

    Handig om te zien of de term echt woninginformatie betreft.
    """

    tekst_normaal = normale_tekst(
        tekst
    )

    positie = tekst_normaal.lower().find(
        term.lower()
    )

    if positie == -1:
        return None

    begin = max(
        0,
        positie - lengte,
    )

    einde = min(
        len(tekst_normaal),
        positie + len(term) + lengte,
    )

    return tekst_normaal[
        begin:einde
    ]


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 76)
    print("TECHNISCHE TEST BIEN'ICI - DETAIL FASE 3A")
    print("=" * 76)

    print()
    print(
        "Detail-URL:"
    )

    print(
        DETAIL_URL
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
            # Detailpagina openen
            # ------------------------------------------------

            response = page.goto(
                DETAIL_URL,
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
                f"Browser HTTP      : {status}"
            )

            print(
                f"Eind-URL          : {page.url}"
            )

            page.wait_for_timeout(
                1000
            )

            # ------------------------------------------------
            # Cookies
            # ------------------------------------------------

            cookies = accepteer_cookies(
                page
            )

            # ------------------------------------------------
            # Wachten op inhoud
            # ------------------------------------------------

            try:

                page.locator(
                    "body"
                ).wait_for(
                    state="attached",
                    timeout=20_000,
                )

            except PlaywrightTimeoutError:

                print(
                    "WAARSCHUWING: body niet tijdig gevonden."
                )

            page.wait_for_timeout(
                3000
            )

            # ------------------------------------------------
            # HTML + tekst
            # ------------------------------------------------

            html = page.content()

            body_tekst = normale_tekst(
                page.locator(
                    "body"
                ).inner_text()
            )

            titel = page.title()

            duur = (
                time.perf_counter()
                - start
            )

            print()
            print(
                f"Pagina titel      : {titel}"
            )

            print(
                f"HTML grootte      : {len(html):,} tekens"
            )

            print(
                f"Body tekst        : {len(body_tekst):,} tekens"
            )

            print(
                f"Cookies           : {cookies}"
            )

            print(
                f"Looptijd          : {duur:.2f} seconden"
            )

            # ------------------------------------------------
            # Anti-bot
            # ------------------------------------------------

            blokkades = herken_mogelijke_blokkade(
                body_tekst
            )

            print(
                f"Blokkadesignalen  : {blokkades}"
            )

            # ------------------------------------------------
            # HTML opslaan
            # ------------------------------------------------

            html_bestand = (
                "bienici_detail.html"
            )

            with open(
                html_bestand,
                "w",
                encoding="utf-8",
            ) as bestand:

                bestand.write(
                    html
                )

            print(
                f"HTML opgeslagen   : {html_bestand}"
            )

            # ------------------------------------------------
            # Basis HTML parser
            # ------------------------------------------------

            soup = BeautifulSoup(
                html,
                "html.parser",
            )

            tekst = normale_tekst(
                soup.get_text(
                    " ",
                    strip=True,
                )
            )

            # ------------------------------------------------
            # Kenmerken inventariseren
            # ------------------------------------------------

            resultaten = zoek_termen(
                tekst
            )

            print()
            print("=" * 76)
            print("KENMERKEN-INVENTARISATIE")
            print("=" * 76)

            for kenmerk, gevonden in (
                resultaten.items()
            ):

                print()
                print(
                    f"{kenmerk:20}: "
                    f"{bool(gevonden)}"
                )

                if gevonden:

                    print(
                        f"    termen: "
                        f"{', '.join(gevonden)}"
                    )

                    context_tekst = (
                        toon_context_rond_term(
                            tekst,
                            gevonden[0],
                        )
                    )

                    if context_tekst:

                        print(
                            f"    context: "
                            f"{context_tekst}"
                        )

            # ------------------------------------------------
            # Foto's inventariseren
            # ------------------------------------------------

            fotos = []

            for afbeelding in soup.find_all(
                "img"
            ):

                src = afbeelding.get(
                    "src"
                )

                if not src:
                    continue

                src = src.strip()

                if (
                    "bienici.com"
                    in src
                    or "file.bienici.com"
                    in src
                ):

                    if src not in fotos:

                        fotos.append(
                            src
                        )

            print()
            print("=" * 76)
            print("FOTO-INVENTARISATIE")
            print("=" * 76)

            print()
            print(
                f"Unieke mogelijke foto's: "
                f"{len(fotos)}"
            )

            for nummer, foto in enumerate(
                fotos[:15],
                start=1,
            ):

                print(
                    f"[{nummer:02}] {foto}"
                )

            # ------------------------------------------------
            # Samenvatting
            # ------------------------------------------------

            print()
            print("=" * 76)
            print("SAMENVATTING DETAIL FASE 3A")
            print("=" * 76)

            print(
                f"HTTP 200              : "
                f"{status == 200}"
            )

            print(
                f"Cookies geaccepteerd  : "
                f"{cookies}"
            )

            print(
                f"Blokkade              : "
                f"{bool(blokkades)}"
            )

            print(
                f"DPE-term aanwezig     : "
                f"{bool(resultaten['dpe'])}"
            )

            print(
                f"GES-term aanwezig     : "
                f"{bool(resultaten['ges'])}"
            )

            print(
                f"Terrain aanwezig      : "
                f"{bool(resultaten['terrain'])}"
            )

            print(
                f"Garage aanwezig       : "
                f"{bool(resultaten['garage'])}"
            )

            print(
                f"Assainissement aanwezig: "
                f"{bool(resultaten['assainissement'])}"
            )

            print(
                f"Foto's gevonden       : "
                f"{len(fotos)}"
            )

            print()
            print("=" * 76)

            print()
            print(
                "Browser blijft 5 seconden "
                "open voor visuele controle..."
            )

            page.wait_for_timeout(
                5000
            )

        finally:

            context.close()
            browser.close()


if __name__ == "__main__":
    main()
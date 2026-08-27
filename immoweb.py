import re

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
    POSTCODE_WAIT,
    RESULTATEN_WAIT,
    SLOW_MO,
)
from csv_opslaan import opslaan_csv
from logger import logger
from vergelijk import nieuwe_woningen


def zoek_immoweb(
    postcode,
    woningtype,
    min_prijs,
    max_prijs,
    csv_bestand,
):
    logger.info(
        "Zoeken op Immoweb gestart: postcode=%s, woningtype=%s",
        postcode,
        woningtype,
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

                # Website openen
                page.goto(
                    "https://www.immoweb.be/nl",
                    wait_until="domcontentloaded",
                    timeout=PAGE_TIMEOUT,
                )

                logger.info("Geopende URL: %s", page.url)
                logger.info("Paginatitel: %s", page.title())

                # Cookies accepteren als de melding zichtbaar is
                cookie_knop = page.get_by_test_id(
                    "uc-accept-all-button"
                )

                try:
                    cookie_knop.click(
                        timeout=COOKIE_TIMEOUT
                    )
                    logger.info("Cookiemelding geaccepteerd")
                except PlaywrightTimeoutError:
                    logger.info(
                        "Geen cookiemelding zichtbaar; doorgaan"
                    )

                # Postcode invullen
                locatie = page.get_by_role(
                    "textbox",
                    name="Locaties",
                    exact=True,
                )

                locatie.wait_for(
                    state="visible",
                    timeout=LOCATIE_TIMEOUT,
                )

                locatie.fill(str(postcode))
                locatie.press("Enter")

                page.wait_for_timeout(POSTCODE_WAIT)

                # Geavanceerd zoeken openen
                page.get_by_role(
                    "link",
                    name="Geavanceerd zoeken",
                ).click()

                page.wait_for_timeout(FORMULIER_WAIT)

                # Prijzen invullen
                page.get_by_role(
                    "textbox",
                    name="minimum prijs",
                ).fill(str(min_prijs))

                page.get_by_role(
                    "textbox",
                    name="maximale prijs",
                ).fill(str(max_prijs))

                # Type woning kiezen
                page.get_by_role(
                    "button",
                    name="Type pand Huis en appartement",
                ).click()

                if woningtype == "huis":
                    page.get_by_role(
                        "option",
                        name="Huis",
                        exact=True,
                    ).click()

                elif woningtype == "appartement":
                    page.get_by_role(
                        "option",
                        name="Appartement",
                        exact=True,
                    ).click()

                elif woningtype == "chalet":
                    logger.warning(
                        "Chalet is nog niet als apart "
                        "Immoweb-filter ingebouwd"
                    )

                else:
                    raise ValueError(
                        f"Onbekend woningtype: {woningtype}"
                    )

                # Zoeken
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

                # Zoekresultaten
                woningen = page.locator(
                    "article[id^='classified_']"
                )

                aantal_woningen = woningen.count()

                logger.info(
                    "%s woningen gevonden op Immoweb "
                    "voor postcode %s",
                    aantal_woningen,
                    postcode,
                )

                print(
                    f"Gevonden woningen: "
                    f"{aantal_woningen}"
                )

                for i in range(aantal_woningen):
                    woning = woningen.nth(i)

                    try:
                        titel = woning.locator(
                            "h2.card__title"
                        ).inner_text()

                        prijs = woning.locator(
                            "span.resizable-text"
                        ).first.inner_text()

                        link = woning.locator(
                            "h2.card__title a"
                        ).get_attribute("href")

                        info_tekst = woning.locator(
                            "div.card__informations"
                        ).inner_text()

                        slaapkamers_match = re.search(
                            r"(\d+)\s*slp\.",
                            info_tekst,
                            re.IGNORECASE,
                        )

                        slaapkamers = (
                            slaapkamers_match.group(1)
                            if slaapkamers_match
                            else "Onbekend"
                        )

                        oppervlakte_match = re.search(
                            r"(\d+)\s*m²",
                            info_tekst,
                        )

                        oppervlakte = (
                            oppervlakte_match.group(1)
                            if oppervlakte_match
                            else "Onbekend"
                        )

                        plaats_match = re.search(
                            r"\b\d{4}\s+"
                            r"[A-ZÀ-ÖØ-Ý]"
                            r"[A-ZÀ-ÖØ-Ý\s'\-]+",
                            info_tekst,
                        )

                        plaats = (
                            plaats_match.group(0).strip()
                            if plaats_match
                            else "Onbekend"
                        )
                        #begin hier
                        resultaten.append({
                            "titel": titel,
                            "prijs": prijs,
                            "slaapkamers": slaapkamers,
                            "oppervlakte": oppervlakte,
                            "plaats": plaats,
                            "link": link,
                            "bron": "Immoweb",
                        })

                    except Exception:
                        logger.exception(
                            "Woning %s kon niet worden gelezen",
                            i,
                        )

                nieuw = nieuwe_woningen(
                    resultaten,
                    csv_bestand=csv_bestand,
                )

                logger.info(
                    "%s nieuwe woningen gevonden "
                    "voor postcode %s",
                    len(nieuw),
                    postcode,
                )

                if nieuw:
                    print(
                        f"Nieuwe woningen gevonden: "
                        f"{len(nieuw)}"
                    )
                else:
                    print(
                        "Geen nieuwe woningen gevonden."
                    )

                # Eerst veilig opslaan; daarna kan
                # huizenzoeker.py eventueel mailen
                opslaan_csv(
                    resultaten,
                    bestandsnaam=csv_bestand,
                )

                logger.info(
                    "CSV-bestand '%s' bijgewerkt",
                    csv_bestand,
                )

            finally:
                browser.close()

                logger.info(
                    "Browser gesloten voor postcode %s",
                    postcode,
                )

    except Exception:
        logger.exception(
            "Immoweb-zoekopdracht voor postcode %s "
            "is mislukt",
            postcode,
        )
        raise

    return nieuw
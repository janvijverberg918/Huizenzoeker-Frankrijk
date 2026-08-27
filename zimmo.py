from playwright.sync_api import sync_playwright

from config import HEADLESS, PAGE_TIMEOUT, SLOW_MO
from logger import logger


def zoek_zimmo(
    postcode,
    woningtype,
    min_prijs,
    max_prijs,
    csv_bestand,
):
    logger.info(
        "Zoeken op Zimmo gestart: postcode=%s, woningtype=%s",
        postcode,
        woningtype,
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS,
            slow_mo=0 if HEADLESS else SLOW_MO,
        )

        try:
            page = browser.new_page()

            page.goto(
                "https://www.zimmo.be/nl/",
                wait_until="domcontentloaded",
                timeout=PAGE_TIMEOUT,
            )

            logger.info("Zimmo URL: %s", page.url)
            logger.info("Zimmo paginatitel: %s", page.title())

            page.screenshot(
                path="zimmo_startpagina.png",
                full_page=True,
            )

            print("Zimmo geopend.")
            print("URL:", page.url)
            print("Titel:", page.title())

            input("Bekijk de Zimmo-pagina en druk daarna op Enter...")

        finally:
            browser.close()
            logger.info(
                "Zimmo-browser gesloten voor postcode %s",
                postcode,
            )

    return []
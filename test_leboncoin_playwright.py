from playwright.sync_api import sync_playwright


URL = (
    "https://www.leboncoin.fr/cl/"
    "ventes_immobilieres/"
    "cp_givet_08600/"
    "real_estate_type%3A1"
)


def main():

    print("=" * 72)
    print("LEBONCOIN PLAYWRIGHT TEST")
    print("=" * 72)

    print()
    print(f"URL: {URL}")

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False,
        )

        context = browser.new_context(
            locale="fr-FR",
            viewport={
                "width": 1440,
                "height": 1000,
            },
        )

        page = context.new_page()

        try:
            response = page.goto(
                URL,
                wait_until="domcontentloaded",
                timeout=60_000,
            )

            print()
            print(
                "HTTP-status :",
                response.status if response else None,
            )

            # Geef JavaScript tijd om de pagina op te bouwen.
            page.wait_for_timeout(
                8_000
            )

            print(
                "Titel       :",
                page.title(),
            )

            print(
                "Eind-URL    :",
                page.url,
            )

            html = page.content()

            print(
                "HTML lengte :",
                f"{len(html):,}",
            )

            bodytekst = page.locator(
                "body"
            ).inner_text()

            print()
            print("-" * 72)
            print("BEGIN BODYTEKST")
            print("-" * 72)

            print(
                bodytekst[:3000]
            )

            print()
            print("-" * 72)
            print("EINDE BODYTEKST")
            print("-" * 72)

            print()
            print(
                "Advertentielinks gevonden:",
                page.locator(
                    'a[href*="/ad/"]'
                ).count(),
            )

            print()
            input(
                "Druk op Enter om de browser te sluiten..."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
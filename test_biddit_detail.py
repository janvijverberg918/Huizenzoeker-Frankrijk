from playwright.sync_api import sync_playwright

from config import (
    HEADLESS,
    PAGE_TIMEOUT,
    SLOW_MO,
)


def main():
    print()
    print("BIDDIT DETAILPAGINA TEST")
    print("=" * 70)
    print()

    url = input(
        "Plak een Biddit advertentielink: "
    ).strip()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS,
            slow_mo=0 if HEADLESS else SLOW_MO,
        )

        try:
            page = browser.new_page()

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=PAGE_TIMEOUT,
            )

            page.wait_for_timeout(2000)

            # Cookie-popup
            try:
                page.get_by_role(
                    "button",
                    name="Alle cookies aanvaarden",
                ).click(
                    timeout=5000
                )

                print(
                    "Cookiemelding geaccepteerd."
                )

                page.wait_for_timeout(
                    1500
                )

            except Exception:
                print(
                    "Geen cookiemelding zichtbaar."
                )

            print()
            print("URL")
            print("-" * 70)
            print(page.url)

            print()
            print("PAGINATITEL")
            print("-" * 70)
            print(page.title())

            print()
            print("H1")
            print("-" * 70)

            h1 = page.locator("h1")

            if h1.count() > 0:
                print(
                    h1.first.inner_text().strip()
                )
            else:
                print(
                    "Geen H1 gevonden"
                )

            print()
            print("PAGINATEKST")
            print("-" * 70)

            body = page.locator("body")

            if body.count() > 0:
                tekst = (
                    body.first
                    .inner_text()
                    .strip()
                )

                print(
                    tekst[:15000]
                )

            else:
                print(
                    "Geen paginatekst gevonden"
                )

            print()
            print("AFBEELDINGEN")
            print("-" * 70)

            afbeeldingen = page.locator(
                "img"
            )

            aantal = afbeeldingen.count()

            print(
                f"Aantal img-elementen: {aantal}"
            )

            for i in range(
                min(aantal, 30)
            ):
                img = afbeeldingen.nth(i)

                print()
                print(
                    f"Afbeelding {i + 1}"
                )

                print(
                    "src     : "
                    f"{img.get_attribute('src')}"
                )

                print(
                    "data-src: "
                    f"{img.get_attribute('data-src')}"
                )

                print(
                    "srcset  : "
                    f"{img.get_attribute('srcset')}"
                )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
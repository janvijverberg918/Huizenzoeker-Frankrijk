from playwright.sync_api import sync_playwright

from config import (
    HEADLESS,
    PAGE_TIMEOUT,
    SLOW_MO,
)


def main():
    print()
    print("IMMOVLAN DETAILPAGINA TEST")
    print("=" * 70)
    print()

    url = input(
        "Plak een Immovlan advertentielink: "
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

            page.wait_for_timeout(3000)

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
                print("Geen H1 gevonden")

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
                    tekst[:12000]
                )
            else:
                print(
                    "Geen paginatekst gevonden"
                )

            print()
            print("AFBEELDINGEN")
            print("-" * 70)

            afbeeldingen = page.locator("img")

            print(
                f"Aantal img-elementen: "
                f"{afbeeldingen.count()}"
            )

            for i in range(
                min(
                    afbeeldingen.count(),
                    30,
                )
            ):
                img = afbeeldingen.nth(i)

                src = img.get_attribute(
                    "src"
                )

                data_src = img.get_attribute(
                    "data-src"
                )

                srcset = img.get_attribute(
                    "srcset"
                )

                print()
                print(
                    f"Afbeelding {i + 1}"
                )
                print(
                    f"src     : {src}"
                )
                print(
                    f"data-src: {data_src}"
                )
                print(
                    f"srcset  : {srcset}"
                )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
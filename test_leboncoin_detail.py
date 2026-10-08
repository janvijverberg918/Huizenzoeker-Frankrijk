from playwright.sync_api import sync_playwright


URL = "https://www.leboncoin.fr/vi/3265392486.htm"


def main():

    print("=" * 72)
    print("LEBONCOIN DETAIL TEST")
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

            page.wait_for_timeout(
                5_000
            )
            # vanaf hier
            print()
            print("=" * 72)
            print("BUTTONS OP PAGINA")
            print("=" * 72)

            buttons = page.locator("button")

            print(
                f"Aantal buttons: {buttons.count()}"
            )

            for i in range(
                min(
                    buttons.count(),
                    50,
                )
            ):
                try:
                    tekst = buttons.nth(
                        i
                    ).inner_text().strip()

                    if tekst:
                        print(
                            f"[{i}] {tekst}"
                        )
                except Exception:
                    pass


            print()
            print("=" * 72)
            print("IFRAMES")
            print("=" * 72)

            print(
                f"Aantal frames: {len(page.frames)}"
            )

            for nummer, frame in enumerate(
                page.frames
            ):
                print()
                print(
                    f"FRAME {nummer}"
                )

                print(
                    f"URL: {frame.url}"
                )

                try:
                    frame_buttons = frame.locator(
                        "button"
                    )

                    print(
                        f"Buttons: {frame_buttons.count()}"
                    )

                    for i in range(
                        min(
                            frame_buttons.count(),
                            30,
                        )
                    ):
                        try:
                            tekst = (
                                frame_buttons.nth(i)
                                .inner_text()
                                .strip()
                            )

                            if tekst:
                                print(
                                    f"    [{i}] {tekst}"
                                )

                        except Exception:
                            pass

                except Exception:
                    pass

            # Cookie-popup afhandelen
            cookie_knoppen = [
                "Tout refuser",
                "Continuer sans accepter",
                "Refuser",
                "Accepter",
                "Tout accepter",
            ]

            cookie_afgehandeld = False

            for tekst in cookie_knoppen:
                try:
                    knop = page.get_by_role(
                        "button",
                        name=tekst,
                        exact=True,
                    )

                    if knop.count() > 0 and knop.first.is_visible():
                        print(
                            f"Cookieknop gevonden: {tekst}"
                        )

                        knop.first.click()

                        page.wait_for_timeout(
                            3_000
                        )

                        print(
                            f"Cookies afgehandeld via: {tekst}"
                        )

                        cookie_afgehandeld = True
                        break

                except Exception:
                    pass

            if not cookie_afgehandeld:
                print(
                    "Geen actieve cookie-popup gevonden."
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

            with open(
                "leboncoin_detail.html",
                "w",
                encoding="utf-8",
            ) as bestand:
                bestand.write(html)

            print(
                "HTML opgeslagen als leboncoin_detail.html"
            )
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
                bodytekst[:5000]
            )

            print()
            print("-" * 72)
            print("EINDE BODYTEKST")
            print("-" * 72)

            input(
                "Druk op Enter om de browser te sluiten..."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
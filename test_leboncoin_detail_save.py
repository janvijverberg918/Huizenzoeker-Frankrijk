from pathlib import Path

from playwright.sync_api import sync_playwright


# ============================================================
# CONFIGURATIE
# ============================================================

# Vervang dit door de Leboncoin-detail-URL waarvan we al bewezen
# hebben dat hij via Playwright opent.


OUTPUT_FILE = Path("leboncoin_detail.html")
DETAIL_URL = "https://www.leboncoin.fr/vi/3268053815.htm#at_medium=email&at_emailtype=retention&at_campaign=fr_lbc_immo_searchp_emllbc_part_click-ad-saved-search-other__alert"

# ============================================================
# TEST
# ============================================================

def main():
    print("=" * 72)
    print("LEBONCOIN DETAIL - HTML OPSLAAN")
    print("=" * 72)

    print(f"\nURL:")
    print(DETAIL_URL)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        context = browser.new_context(
            locale="fr-FR",
            viewport={
                "width": 1400,
                "height": 1000,
            },
        )

        page = context.new_page()

        print("\nPagina openen...")

        response = page.goto(
            DETAIL_URL,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        if response:
            print(f"HTTP status : {response.status}")
        else:
            print("HTTP status : onbekend")

        # Geef dynamische content tijd om geladen te worden.
        page.wait_for_timeout(5000)

        print(f"Titel       : {page.title()}")
        print(f"Eind-URL    : {page.url}")

        html = page.content()

        print(f"HTML grootte: {len(html):,} tekens")

        OUTPUT_FILE.write_text(
            html,
            encoding="utf-8",
        )

        print(f"\nHTML opgeslagen als:")
        print(OUTPUT_FILE.resolve())

        browser.close()

    print("\n" + "=" * 72)
    print("TEST AFGEROND")
    print("=" * 72)


if __name__ == "__main__":
    main()
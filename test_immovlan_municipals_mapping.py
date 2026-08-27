import re
import time
from urllib.parse import urlparse, parse_qs

from playwright.sync_api import sync_playwright

from config import (
    HEADLESS,
    SLOW_MO,
    ZOEKGEBIEDEN,
    ZOEKPROFIELEN,
)

from immovlan import voer_zoekopdracht_uit


def haal_municipal_uit_url(url):
    """
    Haalt de waarde van ?municipals=... uit de
    uiteindelijke Immovlan-resultaten-URL.
    """

    parsed = urlparse(url)

    parameters = parse_qs(
        parsed.query
    )

    waarden = parameters.get(
        "municipals",
        []
    )

    if not waarden:
        return None

    return waarden[0]


def main():
    print()
    print("=" * 80)
    print("IMMOVLAN MUNICIPALS MAPPING")
    print("=" * 80)

    profiel = ZOEKPROFIELEN[0]

    woningtype = profiel[
        "woningtype"
    ]

    min_prijs = profiel[
        "min_prijs"
    ]

    max_prijs = profiel[
        "max_prijs"
    ]

    mapping = {}

    mislukt = []

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
            for nummer, gebied in enumerate(
                ZOEKGEBIEDEN,
                start=1,
            ):
                postcode = gebied[
                    "postcode"
                ]

                naam = gebied[
                    "naam"
                ]

                print()
                print("-" * 80)

                print(
                    f"[{nummer}/{len(ZOEKGEBIEDEN)}] "
                    f"{naam} ({postcode})"
                )

                page = browser.new_page()

                start = time.perf_counter()

                try:
                    voer_zoekopdracht_uit(
                        page,
                        postcode,
                        woningtype,
                        min_prijs,
                        max_prijs,
                    )

                    resultaten_url = page.url

                    municipal = haal_municipal_uit_url(
                        resultaten_url
                    )

                    looptijd = (
                        time.perf_counter()
                        - start
                    )

                    if not municipal:
                        print(
                            "GEEN municipal gevonden in URL:"
                        )

                        print(
                            resultaten_url
                        )

                        mislukt.append(
                            {
                                "postcode": postcode,
                                "naam": naam,
                                "reden": (
                                    "municipals ontbreekt"
                                ),
                            }
                        )

                    else:
                        mapping[
                            postcode
                        ] = municipal

                        print(
                            f"Municipal : {municipal}"
                        )

                        print(
                            f"Looptijd  : "
                            f"{looptijd:.2f} s"
                        )

                except Exception as fout:
                    print(
                        f"MISLUKT: {fout}"
                    )

                    mislukt.append(
                        {
                            "postcode": postcode,
                            "naam": naam,
                            "reden": str(
                                fout
                            ),
                        }
                    )

                finally:
                    try:
                        page.close()
                    except Exception:
                        pass

        finally:
            browser.close()

    totale_tijd = (
        time.perf_counter()
        - totaal_start
    )

    print()
    print("=" * 80)
    print("GEVONDEN MAPPING")
    print("=" * 80)

    print()
    print(
        "IMMOVLAN_MUNICIPALS = {"
    )

    for gebied in ZOEKGEBIEDEN:
        postcode = gebied[
            "postcode"
        ]

        if postcode not in mapping:
            continue

        print(
            f'    "{postcode}": '
            f'"{mapping[postcode]}",'
        )

    print("}")

    print()
    print("=" * 80)
    print("SAMENVATTING")
    print("=" * 80)

    print(
        f"Zoekgebieden totaal     : "
        f"{len(ZOEKGEBIEDEN)}"
    )

    print(
        f"Municipals gevonden     : "
        f"{len(mapping)}"
    )

    print(
        f"Mislukt / ontbrekend    : "
        f"{len(mislukt)}"
    )

    print(
        f"Totale looptijd         : "
        f"{totale_tijd:.1f} seconden"
    )

    if mislukt:
        print()
        print(
            "MISLUKTE / ONVOLLEDIGE GEBIEDEN"
        )

        print("-" * 80)

        for item in mislukt:
            print(
                f"{item['postcode']} "
                f"{item['naam']}: "
                f"{item['reden']}"
            )

    print()
    print("=" * 80)

    if len(mapping) == len(
        ZOEKGEBIEDEN
    ):
        print(
            "MAPPING COMPLEET: JA"
        )
    else:
        print(
            "MAPPING COMPLEET: NEE"
        )

    print("=" * 80)


if __name__ == "__main__":
    main()
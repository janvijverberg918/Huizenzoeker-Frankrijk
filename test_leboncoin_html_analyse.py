from pathlib import Path
import re


HTML_FILE = Path("leboncoin_detail.html")


def zoek_context(html, zoekterm, context=150):
    """
    Zoek alle voorkomens van een term en toon een stukje
    HTML rondom iedere match.
    """
    matches = list(
        re.finditer(
            re.escape(zoekterm),
            html,
            flags=re.IGNORECASE,
        )
    )

    print(f"\n{'=' * 72}")
    print(f"ZOEKTERM: {zoekterm!r}")
    print(f"AANTAL MATCHES: {len(matches)}")
    print("=" * 72)

    # Maximaal eerste 5 matches tonen
    for nummer, match in enumerate(matches[:5], start=1):
        start = max(0, match.start() - context)
        einde = min(len(html), match.end() + context)

        fragment = html[start:einde]

        # Fragment iets leesbaarder maken
        fragment = fragment.replace("\n", " ")
        fragment = re.sub(r"\s+", " ", fragment)

        print(f"\n--- Match {nummer} ---")
        print(fragment)


def main():
    print("=" * 72)
    print("LEBONCOIN - LOKALE HTML ANALYSE")
    print("=" * 72)

    if not HTML_FILE.exists():
        print(f"\nFOUT: bestand niet gevonden:")
        print(HTML_FILE.resolve())
        return

    html = HTML_FILE.read_text(
        encoding="utf-8",
        errors="replace",
    )

    print(f"\nBestand : {HTML_FILE.resolve()}")
    print(f"Grootte : {len(html):,} tekens")

    zoektermen = [
        "3265392486",
        "price",
        "location",
        "zipcode",
        "city",
        "square",
        "surface",
        "rooms",
        "bedrooms",
        "energy",
        "dpe",
        "__NEXT_DATA__",
        "application/ld+json",
    ]

    for zoekterm in zoektermen:
        zoek_context(html, zoekterm)

    print("\n" + "=" * 72)
    print("ANALYSE AFGEROND")
    print("=" * 72)


if __name__ == "__main__":
    main()
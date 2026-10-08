from pathlib import Path
import json
import re


HTML_FILE = Path("leboncoin_detail.html")
OUTPUT_FILE = Path("leboncoin_next_data.json")


def main():
    print("=" * 72)
    print("LEBONCOIN - __NEXT_DATA__ EXTRACTIE")
    print("=" * 72)

    if not HTML_FILE.exists():
        print(f"\nFOUT: bestand niet gevonden:")
        print(HTML_FILE.resolve())
        return

    html = HTML_FILE.read_text(
        encoding="utf-8",
        errors="replace",
    )

    print(f"\nHTML grootte : {len(html):,} tekens")

    # Zoek het __NEXT_DATA__ script
    match = re.search(
        r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if not match:
        print("\nFOUT: __NEXT_DATA__ niet gevonden.")
        return

    json_text = match.group(1)

    print(f"JSON grootte : {len(json_text):,} tekens")

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        print("\nFOUT bij JSON parsing:")
        print(exc)
        return

    print("JSON parsing : OK")

    # Pretty-print opslaan voor lokaal onderzoek
    OUTPUT_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\nJSON opgeslagen als:")
    print(OUTPUT_FILE.resolve())

    # Hoogste niveau bekijken
    print("\nTop-level keys:")
    for key in data.keys():
        print(f"  - {key}")

    props = data.get("props", {})
    print("\nprops keys:")
    for key in props.keys():
        print(f"  - {key}")

    page_props = props.get("pageProps", {})
    print("\npageProps keys:")
    for key in page_props.keys():
        print(f"  - {key}")

    print("\n" + "=" * 72)
    print("EXTRACTIE AFGEROND")
    print("=" * 72)


if __name__ == "__main__":
    main()
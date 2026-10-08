from pathlib import Path
import json


JSON_FILE = Path("leboncoin_next_data.json")
OUTPUT_FILE = Path("leboncoin_ad.json")


def main():
    print("=" * 72)
    print("LEBONCOIN - AD OBJECT ANALYSE")
    print("=" * 72)

    if not JSON_FILE.exists():
        print(f"\nFOUT: bestand niet gevonden:")
        print(JSON_FILE.resolve())
        return

    data = json.loads(
        JSON_FILE.read_text(
            encoding="utf-8"
        )
    )

    page_props = (
        data
        .get("props", {})
        .get("pageProps", {})
    )

    ad = page_props.get("ad")

    if ad is None:
        print("\nFOUT: pageProps['ad'] ontbreekt.")
        return

    print(f"\nType ad : {type(ad).__name__}")

    if isinstance(ad, dict):
        print(f"Aantal keys : {len(ad)}")

        print("\nTop-level ad keys:")
        for key in sorted(ad.keys()):
            value = ad[key]

            if isinstance(value, dict):
                omschrijving = f"dict ({len(value)} keys)"
            elif isinstance(value, list):
                omschrijving = f"list ({len(value)} items)"
            else:
                tekst = repr(value)
                if len(tekst) > 100:
                    tekst = tekst[:100] + "..."
                omschrijving = tekst

            print(f"  {key:30} : {omschrijving}")

    # Volledig ad-object afzonderlijk opslaan
    OUTPUT_FILE.write_text(
        json.dumps(
            ad,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\nAd-object opgeslagen als:")
    print(OUTPUT_FILE.resolve())

    print("\n" + "=" * 72)
    print("ANALYSE AFGEROND")
    print("=" * 72)


if __name__ == "__main__":
    main()
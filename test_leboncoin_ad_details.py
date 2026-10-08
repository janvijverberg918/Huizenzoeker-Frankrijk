from pathlib import Path
import json


JSON_FILE = Path("leboncoin_ad.json")


def toon_dict(titel, data):
    print("\n" + "=" * 72)
    print(titel)
    print("=" * 72)

    if not isinstance(data, dict):
        print(repr(data))
        return

    for key, value in data.items():
        print(f"{key:30} : {repr(value)}")


def main():
    print("=" * 72)
    print("LEBONCOIN - AD DETAILS")
    print("=" * 72)

    if not JSON_FILE.exists():
        print(f"\nFOUT: bestand niet gevonden:")
        print(JSON_FILE.resolve())
        return

    ad = json.loads(
        JSON_FILE.read_text(
            encoding="utf-8"
        )
    )

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    toon_dict(
        "LOCATION",
        ad.get("location")
    )

    # --------------------------------------------------------
    # ATTRIBUTES
    # --------------------------------------------------------

    print("\n" + "=" * 72)
    print("ATTRIBUTES")
    print("=" * 72)

    attributes = ad.get("attributes", [])

    print(f"\nAantal attributes: {len(attributes)}")

    for nummer, attribute in enumerate(attributes, start=1):
        print(f"\n--- Attribute {nummer} ---")

        if isinstance(attribute, dict):
            for key, value in attribute.items():
                print(f"{key:25} : {repr(value)}")
        else:
            print(repr(attribute))

    # --------------------------------------------------------
    # IMAGES
    # --------------------------------------------------------

    toon_dict(
        "IMAGES",
        ad.get("images")
    )

    # --------------------------------------------------------
    # KERNGEGEVENS
    # --------------------------------------------------------

    print("\n" + "=" * 72)
    print("KERNGEGEVENS")
    print("=" * 72)

    print(f"ID          : {ad.get('list_id')}")
    print(f"Titel       : {ad.get('subject')}")
    print(f"Prijs cents : {ad.get('price_cents')}")
    print(f"Prijs       : {ad.get('price')}")
    print(f"URL         : {ad.get('url')}")
    print(f"Beschrijving: {ad.get('body')}")

    print("\n" + "=" * 72)
    print("ANALYSE AFGEROND")
    print("=" * 72)


if __name__ == "__main__":
    main()
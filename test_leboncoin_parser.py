from pathlib import Path
import json
import re


JSON_FILE = Path("leboncoin_ad.json")


def maak_attributes_dict(ad):
    resultaat = {}

    for attr in ad.get("attributes", []):
        key = attr.get("key")

        if key:
            resultaat[key] = attr

    return resultaat


def attribute_value(attributes, key, default=None):
    attr = attributes.get(key)

    if not attr:
        return default

    return attr.get("value")


def attribute_label(attributes, key, default=None):
    attr = attributes.get(key)

    if not attr:
        return default

    return attr.get("value_label") or attr.get("value") or default


def naar_int(value):
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def zoek_perceeloppervlakte(body):
    if not body:
        return None

    patronen = [
        r"surface\s+terrain\s*:\s*(?:sur\s*)?([\d\s]+)\s*m[²2]",
        r"terrain\s+(?:de\s+)?([\d\s]+)\s*m[²2]",
    ]

    for patroon in patronen:
        match = re.search(
            patroon,
            body,
            flags=re.IGNORECASE,
        )

        if match:
            waarde = match.group(1).replace(" ", "")

            try:
                return int(waarde)
            except ValueError:
                pass

    return None

def zoek_slaapkamers(body):
    if not body:
        return None

    patronen = [
        r"(\d+)\s*chambres?",
        r"(\d+)\s*ch\.",
    ]

    for patroon in patronen:
        match = re.search(
            patroon,
            body,
            flags=re.IGNORECASE,
        )

        if match:
            return int(match.group(1))

    return None


def zoek_badkamers(body):
    if not body:
        return None

    body_lower = body.lower()

    termen = [
        "salle de bain",
        "salle de bains",
        "salle d'eau",
        "salle d’eau",
    ]

    for term in termen:
        if term in body_lower:
            return 1

    return None


def zoek_verwarming(body):
    if not body:
        return None

    body_lower = body.lower()

    if "chauffage central gaz" in body_lower:
        return "Gaz"

    if "cc gaz" in body_lower:
        return "Gaz"

    if "chauffage gaz" in body_lower:
        return "Gaz"

    if "chauffage électrique" in body_lower:
        return "Électrique"

    if "chauffage electrique" in body_lower:
        return "Électrique"

    if "pompe à chaleur" in body_lower:
        return "Pompe à chaleur"

    if "fioul" in body_lower or "fuel" in body_lower:
        return "Fioul"

    return None

def bevat_woord(body, woorden):
    if not body:
        return False

    body_lower = body.lower()

    return any(
        woord.lower() in body_lower
        for woord in woorden
    )


def main():
    print("=" * 72)
    print("LEBONCOIN - EERSTE LOKALE PARSER")
    print("=" * 72)

    if not JSON_FILE.exists():
        print(f"\nFOUT: {JSON_FILE.resolve()} bestaat niet.")
        return

    ad = json.loads(
        JSON_FILE.read_text(encoding="utf-8")
    )

    attributes = maak_attributes_dict(ad)

    location = ad.get("location") or {}
    images = ad.get("images") or {}
    body = ad.get("body") or ""

    prijs = None

    if ad.get("price"):
        prijs = naar_int(ad["price"][0])

    if prijs is None and ad.get("price_cents") is not None:
        prijs = int(ad["price_cents"] / 100)

    woning = {
        "bron": "Leboncoin",
        "advertentie_id": ad.get("list_id"),
        "titel": ad.get("subject"),
        "prijs": prijs,
        "plaats": location.get("city"),
        "postcode": location.get("zipcode"),

        "woonoppervlakte": naar_int(
            attribute_value(attributes, "square")
        ),

        "perceeloppervlakte": zoek_perceeloppervlakte(body),

        "kamers": naar_int(
            attribute_value(attributes, "rooms")
        ),

        "slaapkamers": (
            naar_int(attribute_value(attributes, "bedrooms"))
            or zoek_slaapkamers(body)
        ),

        "badkamers": (
            naar_int(attribute_value(attributes, "nb_bathrooms"))
            or zoek_badkamers(body)
        ),

                "verwarming": (
            attribute_label(attributes, "heating_mode")
            or zoek_verwarming(body)
            or "geen informatie"
        ),

        "dpe": attribute_label(
            attributes,
            "energy_rate",
            "geen informatie",
        ),

        "ges": attribute_label(
            attributes,
            "ges",
            "geen informatie",
        ),

        "staat": attribute_label(
            attributes,
            "global_condition",
            "geen informatie",
        ),

        "garage": bevat_woord(
            body,
            ["garage"]
        ),

        "tuin": bevat_woord(
            body,
            ["jardin", "terrain arboré"]
        ),

        "aantal_fotos": images.get("nb_images", 0),

        "foto_url": (
            images.get("urls_large", [None])[0]
            if images.get("urls_large")
            else None
        ),

        "url": ad.get("url"),
        "beschrijving": body,
    }

    print()

    for key, value in woning.items():
        if key == "beschrijving":
            continue

        print(f"{key:22} : {value}")

    print("\n" + "=" * 72)
    print("PARSER TEST AFGEROND")
    print("=" * 72)


if __name__ == "__main__":
    main()
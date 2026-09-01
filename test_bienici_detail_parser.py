from bs4 import BeautifulSoup
from pathlib import Path
import json
import re
from urllib.parse import urlsplit, urlunsplit


HTML_BESTAND = Path("bienici_detail.html")


def schoon_tekst(tekst):
    """Normaliseer spaties en non-breaking spaces."""
    if tekst is None:
        return None

    tekst = tekst.replace("\xa0", " ")
    tekst = re.sub(r"\s+", " ", tekst)
    return tekst.strip()


def eerste_getal(tekst):
    """Geeft het eerste gehele getal uit tekst terug."""
    if not tekst:
        return None

    match = re.search(r"(\d[\d\s.]*)", tekst)

    if not match:
        return None

    waarde = match.group(1)
    waarde = waarde.replace(" ", "").replace(".", "")

    try:
        return int(waarde)
    except ValueError:
        return None


def vind_regex(tekst, patroon, flags=re.IGNORECASE):
    match = re.search(patroon, tekst, flags)

    if match:
        return schoon_tekst(match.group(1))

    return None


def normaliseer_foto_url(url):
    """
    Verwijder resize-queryparameters zodat dezelfde foto
    niet meerdere keren wordt geteld.
    """
    if not url:
        return None

    url = url.replace("&amp;", "&")

    delen = urlsplit(url)

    return urlunsplit(
        (
            delen.scheme,
            delen.netloc,
            delen.path,
            "",
            "",
        )
    )


def lees_json_ld(soup):
    """
    Lees bruikbare JSON-LD objecten uit de pagina.
    Deze gebruiken we als fallback voor enkele basisgegevens.
    """
    objecten = []

    for script in soup.find_all("script", type="application/ld+json"):
        inhoud = script.string

        if not inhoud:
            continue

        try:
            data = json.loads(inhoud)
        except (json.JSONDecodeError, TypeError):
            continue

        if isinstance(data, list):
            objecten.extend(data)
        elif isinstance(data, dict):
            objecten.append(data)

    return objecten


def parse_bienici_detail(html):
    soup = BeautifulSoup(html, "html.parser")

    body_tekst = schoon_tekst(soup.get_text(" ", strip=True))

    resultaat = {
        "titel": None,
        "prijs": None,
        "plaats": None,
        "postcode": None,
        "woonoppervlakte": None,
        "perceeloppervlakte": None,
        "kamers": None,
        "slaapkamers": None,
        "badkamers": None,
        "wc": None,
        "bouwjaar": None,
        "verwarming": None,
        "dpe_klasse": None,
        "dpe_verbruik": None,
        "ges_klasse": None,
        "ges_uitstoot": None,
        "garage": False,
        "tuin": False,
        "terras": False,
        "parking": False,
        "renovatiestatus": None,
        "omschrijving": None,
        "foto_url": None,
        "aantal_fotos": 0,
        "fotos": [],
    }

    # ============================================================
    # TITEL
    # ============================================================

    h1 = soup.find("h1")

    if h1:
        resultaat["titel"] = schoon_tekst(h1.get_text(" ", strip=True))
    elif soup.title:
        resultaat["titel"] = schoon_tekst(soup.title.get_text())


    # ============================================================
    # STRUCTURELE WONINGDETAILS
    # ============================================================

    details_section = soup.select_one(
        "section.detailsSection_aboutThisProperty"
    )

    if details_section:
        detail_elementen = details_section.select(".labelInfo")

        details = [
            schoon_tekst(element.get_text(" ", strip=True))
            for element in detail_elementen
        ]

        details = [d for d in details if d]

        for regel in details:

            regel_lower = regel.lower()

            # Prijs
            if regel_lower.startswith("prix"):
                resultaat["prijs"] = eerste_getal(regel)

            # Perceel
            elif "m² de terrain" in regel_lower:
                resultaat["perceeloppervlakte"] = eerste_getal(regel)

            # Woonoppervlak:
            # een losse regel zoals "92 m²"
            elif re.fullmatch(r"[\d\s.,]+\s*m²", regel_lower):
                resultaat["woonoppervlakte"] = eerste_getal(regel)

            # Kamers
            elif "pièce" in regel_lower:
                resultaat["kamers"] = eerste_getal(regel)

            # Slaapkamers
            elif "chambre" in regel_lower:
                resultaat["slaapkamers"] = eerste_getal(regel)

            # Badkamers
            elif "salle de bain" in regel_lower:
                resultaat["badkamers"] = eerste_getal(regel)

            # WC
            elif re.search(r"\bwc\b", regel_lower):
                resultaat["wc"] = eerste_getal(regel)

            # Bouwjaar
            elif "construit en" in regel_lower:
                resultaat["bouwjaar"] = eerste_getal(regel)

            # Verwarming
            elif regel_lower.startswith("chauffage"):
                delen = regel.split(":", 1)

                if len(delen) == 2:
                    resultaat["verwarming"] = schoon_tekst(delen[1])

            # Boolean kenmerken
            if regel_lower == "jardin":
                resultaat["tuin"] = True

            if regel_lower == "terrasse":
                resultaat["terras"] = True

            if "place de parking" in regel_lower:
                resultaat["parking"] = True


    # ============================================================
    # OMSCHRIJVING
    # ============================================================

    description_section = soup.select_one("section.description")

    if description_section:
        content = description_section.select_one(
            ".see-more-description__content"
        )

        if content:
            resultaat["omschrijving"] = schoon_tekst(
                content.get_text(" ", strip=True)
            )


    # ============================================================
    # PLAATS + POSTCODE
    # ============================================================

    # Eerst proberen via JSON-LD
    json_ld = lees_json_ld(soup)

    for item in json_ld:

        if item.get("@type") == "Accommodation":

            adres = item.get("address", {})

            if isinstance(adres, dict):

                resultaat["plaats"] = (
                    resultaat["plaats"]
                    or adres.get("addressLocality")
                )

                resultaat["postcode"] = (
                    resultaat["postcode"]
                    or adres.get("postalCode")
                )

            floor_size = item.get("floorSize")

            if (
                resultaat["woonoppervlakte"] is None
                and isinstance(floor_size, dict)
            ):
                resultaat["woonoppervlakte"] = floor_size.get("value")

            if resultaat["kamers"] is None:
                resultaat["kamers"] = item.get("numberOfRooms")


        if item.get("@type") == "Product":

            offers = item.get("offers", {})

            if isinstance(offers, dict):

                prijs_specificatie = offers.get(
                    "priceSpecification", {}
                )

                if (
                    resultaat["prijs"] is None
                    and isinstance(prijs_specificatie, dict)
                ):
                    resultaat["prijs"] = prijs_specificatie.get("price")

            image = item.get("image")

            if image and resultaat["foto_url"] is None:
                resultaat["foto_url"] = normaliseer_foto_url(image)


    # Fallback postcode/plaats uit H1
    if h1:

        h1_tekst = schoon_tekst(h1.get_text(" ", strip=True))

        match = re.search(
            r"\b(\d{5})\s+([A-Za-zÀ-ÿ' -]+)",
            h1_tekst
        )

        if match:

            if resultaat["postcode"] is None:
                resultaat["postcode"] = match.group(1)

            if resultaat["plaats"] is None:
                resultaat["plaats"] = schoon_tekst(match.group(2))


    # ============================================================
    # GARAGE / RENOVATIE
    # ============================================================

    omschrijving_lower = (
        resultaat["omschrijving"] or ""
    ).lower()

    resultaat["garage"] = bool(
        re.search(r"\bgarage\b", omschrijving_lower)
    )

    renovatie_patronen = [
        ("volledig te renoveren", r"\bà rénover entièrement\b"),
        ("te renoveren", r"\bà rénover\b"),
        ("gerenoveerd", r"\brénovée?\b"),
        ("goede staat", r"\bbon état\b"),
    ]

    for nederlandse_status, patroon in renovatie_patronen:

        if re.search(patroon, omschrijving_lower):
            resultaat["renovatiestatus"] = nederlandse_status
            break


    # ============================================================
    # DPE / GES
    # ============================================================

    energy_section = soup.select_one("section.energySection")

    if energy_section:

        energy_text = schoon_tekst(
            energy_section.get_text(" ", strip=True)
        )

        # DPE verbruik
        dpe_match = re.search(
            r"(\d+)\s*kWh/m",
            energy_text,
            re.IGNORECASE
        )

        if dpe_match:
            resultaat["dpe_verbruik"] = int(dpe_match.group(1))

        # GES uitstoot
        ges_match = re.search(
            r"(\d+)\s*kg\s*CO",
            energy_text,
            re.IGNORECASE
        )

        if ges_match:
            resultaat["ges_uitstoot"] = int(ges_match.group(1))

        # Zoek energieklasse via actieve DPE-regel
        actieve_dpe = energy_section.select_one(".dpe-line.active")

        if actieve_dpe:
            actieve_tekst = schoon_tekst(
                actieve_dpe.get_text(" ", strip=True)
            )

            klasse_match = re.search(
                r"\b([A-G])\b",
                actieve_tekst
            )

            if klasse_match:
                resultaat["dpe_klasse"] = klasse_match.group(1)

        # Zoek GES klasse via actieve GES-regel
        mogelijke_ges = energy_section.select(
            ".ges-line.active, .greenhouse-gas-line.active"
        )

        for element in mogelijke_ges:

            tekst = schoon_tekst(
                element.get_text(" ", strip=True)
            )

            klasse_match = re.search(r"\b([A-G])\b", tekst)

            if klasse_match:
                resultaat["ges_klasse"] = klasse_match.group(1)
                break


    # ============================================================
    # FOTO'S
    # ============================================================

    fotos = []

    for img in soup.find_all("img"):

        kandidaten = [
            img.get("src"),
            img.get("src2"),
        ]

        for url in kandidaten:

            if not url:
                continue

            if "file.bienici.com/photo/" not in url:
                continue

            foto = normaliseer_foto_url(url)

            if foto and foto not in fotos:
                fotos.append(foto)

    resultaat["fotos"] = fotos
    resultaat["aantal_fotos"] = len(fotos)

    if fotos:
        resultaat["foto_url"] = fotos[0]


    return resultaat


def toon_resultaat(data):

    print()
    print("=" * 72)
    print("BIEN'ICI DETAIL PARSER - FASE 3B")
    print("=" * 72)
    print()

    velden = [
        ("Titel", "titel"),
        ("Prijs", "prijs"),
        ("Plaats", "plaats"),
        ("Postcode", "postcode"),
        ("Woonoppervlakte", "woonoppervlakte"),
        ("Perceeloppervlakte", "perceeloppervlakte"),
        ("Kamers", "kamers"),
        ("Slaapkamers", "slaapkamers"),
        ("Badkamers", "badkamers"),
        ("WC", "wc"),
        ("Bouwjaar", "bouwjaar"),
        ("Verwarming", "verwarming"),
        ("DPE klasse", "dpe_klasse"),
        ("DPE verbruik", "dpe_verbruik"),
        ("GES klasse", "ges_klasse"),
        ("GES uitstoot", "ges_uitstoot"),
        ("Garage", "garage"),
        ("Tuin", "tuin"),
        ("Terras", "terras"),
        ("Parking", "parking"),
        ("Renovatiestatus", "renovatiestatus"),
        ("Aantal foto's", "aantal_fotos"),
        ("Foto URL", "foto_url"),
    ]

    for label, sleutel in velden:
        print(f"{label:<22}: {data.get(sleutel)}")

    print()
    print("-" * 72)
    print("OMSCHRIJVING")
    print("-" * 72)
    print(data.get("omschrijving"))

    print()
    print("-" * 72)
    print("FOTO'S")
    print("-" * 72)

    for nummer, foto in enumerate(data.get("fotos", []), start=1):
        print(f"[{nummer:02}] {foto}")

    print()
    print("=" * 72)


def main():

    if not HTML_BESTAND.exists():
        print(f"FOUT: {HTML_BESTAND} niet gevonden.")
        return

    html = HTML_BESTAND.read_text(
        encoding="utf-8",
        errors="replace"
    )

    data = parse_bienici_detail(html)

    toon_resultaat(data)


if __name__ == "__main__":
    main()
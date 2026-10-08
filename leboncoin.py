import json
import re

from playwright.sync_api import sync_playwright


# ============================================================
# HULPFUNCTIES
# ============================================================

def maak_attributes_dict(ad):
    """
    Zet de lijst met Leboncoin attributes om naar een dictionary
    met de attribute-key als sleutel.
    """
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


# ============================================================
# BODY FALLBACKS
# ============================================================

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


# ============================================================
# NEXT_DATA
# ============================================================

def extract_next_data(html):
    """
    Haal __NEXT_DATA__ JSON uit de Leboncoin HTML.
    """

    match = re.search(
        r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if not match:
        raise ValueError(
            "Leboncoin __NEXT_DATA__ niet gevonden."
        )

    try:
        return json.loads(match.group(1))

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Leboncoin __NEXT_DATA__ bevat ongeldige JSON: {exc}"
        ) from exc


def extract_ad(next_data):
    """
    Haal het advertentie-object uit __NEXT_DATA__.
    """

    ad = (
        next_data
        .get("props", {})
        .get("pageProps", {})
        .get("ad")
    )

    if not isinstance(ad, dict):
        raise ValueError(
            "Leboncoin advertentie-object niet gevonden."
        )

    return ad


# ============================================================
# ADVERTENTIE → WONING
# ============================================================

def parse_ad(ad):
    """
    Zet een Leboncoin ad-object om naar een gestandaardiseerd
    woningrecord.
    """

    attributes = maak_attributes_dict(ad)

    location = ad.get("location") or {}
    images = ad.get("images") or {}
    body = ad.get("body") or ""

    # --------------------------------------------------------
    # PRIJS
    # --------------------------------------------------------

    prijs = None

    if ad.get("price"):
        prijs = naar_int(ad["price"][0])

    if prijs is None and ad.get("price_cents") is not None:
        prijs = int(ad["price_cents"] / 100)

    # --------------------------------------------------------
    # FOTO'S
    # --------------------------------------------------------

    fotos = []

    urls_large = images.get("urls_large")

    if isinstance(urls_large, list):
        fotos = [
            url
            for url in urls_large
            if url
        ]

    # Fallback als urls_large ontbreekt.
    if not fotos:
        urls = images.get("urls")

        if isinstance(urls, list):
            fotos = [
                url
                for url in urls
                if url
            ]

    foto_url = (
        fotos[0]
        if fotos
        else None
    )

    
    # --------------------------------------------------------
    # WONINGRECORD
    # --------------------------------------------------------

    woning = {
        "bron": "Leboncoin",

        "advertentie_id": ad.get("list_id"),

        "titel": ad.get("subject"),

        "prijs": prijs,

        "plaats": location.get("city"),

        "postcode": location.get("zipcode"),

        "woonoppervlakte": naar_int(
            attribute_value(
                attributes,
                "square",
            )
        ),

        "perceeloppervlakte": zoek_perceeloppervlakte(
            body
        ),

        "kamers": naar_int(
            attribute_value(
                attributes,
                "rooms",
            )
        ),

        "slaapkamers": (
            naar_int(
                attribute_value(
                    attributes,
                    "bedrooms",
                )
            )
            or zoek_slaapkamers(body)
        ),

        "badkamers": (
            naar_int(
                attribute_value(
                    attributes,
                    "nb_bathrooms",
                )
            )
            or zoek_badkamers(body)
        ),

        "verwarming": (
            attribute_label(
                attributes,
                "heating_mode",
            )
            or zoek_verwarming(body)
            or "geen informatie"
        ),

        "dpe": attribute_label(
            attributes,
            "energy_rate",
            None,
        ),

        "ges": attribute_label(
            attributes,
            "ges",
            None,
        ),

        "staat": attribute_label(
            attributes,
            "global_condition",
            "geen informatie",
        ),
        ## vanaf hier
        "garage": zoek_explicit_boolean(
            body,
            positief=[
                r"\bgarage\b",
            ],
            negatief=[
                r"\bsans\s+garage\b",
                r"\bpas\s+de\s+garage\b",
                r"\baucun\s+garage\b",
            ],
        ),

        "tuin": zoek_explicit_boolean(
            body,
            positief=[
                r"\bjardin\b",
                r"\bjardinet\b",
                r"\bterrain arbor[ée]\b",
            ],
            negatief=[
                r"\bsans\s+jardin\b",
                r"\bpas\s+de\s+jardin\b",
                r"\baucun\s+jardin\b",
            ],
        ),

        "aantal_fotos": images.get(
            "nb_images",
            0,
        ),

        "fotos": fotos,

        "foto_url": foto_url,

        "url": ad.get("url"),

        "beschrijving": body,
    }

    return woning


# ============================================================
# HTML → WONING
# ============================================================

def parse_html(html):
    """
    Volledige parser:
    HTML → __NEXT_DATA__ → ad → woning.
    """

    next_data = extract_next_data(html)

    ad = extract_ad(next_data)

    return parse_ad(ad)


# ============================================================
# DETAILPAGINA OPENEN
# ============================================================

def haal_detail_op(url):
    """
    Open een Leboncoin detail-URL via Playwright en retourneer
    het geparste woningrecord.

    Voorlopig bedoeld voor links afkomstig uit Leboncoin
    alertmails.
    """

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

        response = page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        status = response.status if response else None

        if status != 200:
            browser.close()

            raise RuntimeError(
                f"Leboncoin detailpagina gaf HTTP status {status}"
            )

        page.wait_for_timeout(5000)

        html = page.content()

        browser.close()

    # Extra beveiliging tegen een blokkadepagina.
    if len(html) < 100_000:
        raise RuntimeError(
            "Leboncoin detailpagina bevat onverwacht weinig HTML "
            f"({len(html):,} tekens)."
        )

    return parse_html(html)

def start_leboncoin_browser():
    """
    Start één Playwright browser/context voor meerdere
    Leboncoin-detailpagina's binnen dezelfde run.

    Retourneert:
        playwright, browser, context
    """

    playwright = sync_playwright().start()

    browser = playwright.chromium.launch(
        headless=False
    )

    context = browser.new_context(
        locale="fr-FR",
        viewport={
            "width": 1400,
            "height": 1000,
        },
    )

    return (
        playwright,
        browser,
        context,
    )


def haal_detail_op_met_context(
    context,
    url,
):
    """
    Haalt één Leboncoin-detailpagina op binnen een reeds
    bestaande Playwright browsercontext.

    Print diagnostische informatie om HTTP 200 en HTTP 403
    responses met elkaar te kunnen vergelijken.
    """

    page = context.new_page()

    try:
        print()
        print("-" * 72)
        print("LEBONCOIN REQUEST")
        print("-" * 72)
        print(f"Request URL : {url}")

        response = page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        status = (
            response.status
            if response
            else None
        )

        final_url = page.url

        try:
            title = page.title()
        except Exception:
            title = "<niet beschikbaar>"

        print(f"HTTP status : {status}")
        print(f"Final URL   : {final_url}")
        print(f"Page title  : {title}")

        if response is not None:
            try:
                print(
                    f"Resp. URL    : {response.url}"
                )
            except Exception:
                pass

        # Bij een fout willen we eerst de diagnostiek hebben.
        if status != 200:

            try:
                html = page.content()
                html_lengte = len(html)
            except Exception:
                html_lengte = None

            print(
                f"HTML lengte : {html_lengte}"
            )

            raise RuntimeError(
                "Leboncoin detailpagina gaf "
                f"HTTP status {status}"
            )

        # Alleen bij HTTP 200 verder wachten.
        page.wait_for_timeout(
            5000
        )

        html = page.content()

        print(
            f"HTML lengte : {len(html):,}"
        )

    finally:
        page.close()

    if len(html) < 100_000:
        raise RuntimeError(
            "Leboncoin detailpagina bevat onverwacht "
            f"weinig HTML ({len(html):,} tekens)."
        )

    return parse_html(
        html
    )

def zoek_explicit_boolean(body, positief, negatief):
    """
    Geeft:
    True  -> expliciet aanwezig
    False -> expliciet afwezig
    None  -> geen informatie
    """

    if not body:
        return None

    tekst = body.lower()

    for patroon in negatief:
        if re.search(patroon, tekst, re.IGNORECASE):
            return False

    for patroon in positief:
        if re.search(patroon, tekst, re.IGNORECASE):
            return True

    return None
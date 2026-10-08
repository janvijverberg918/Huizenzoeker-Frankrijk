import re
import json

from pathlib import Path
from datetime import datetime, timedelta, timezone


# ============================================================
# CONFIGURATIE / STATUSBESTANDEN
# ============================================================

VERWERKT_FILE = Path("leboncoin_verwerkt.json")
ONBESCHIKBAAR_FILE = Path("leboncoin_onbeschikbaar.json")
RETRY_FILE = Path("leboncoin_retry.json")

RETRY_COOLDOWN_UREN = 12


# ============================================================
# ALGEMENE HELPERS
# ============================================================

def prijs_naar_int(tekst):
    if not tekst:
        return None

    cijfers = re.findall(
        r"\d+",
        tekst,
    )

    if not cijfers:
        return None

    return int(
        "".join(cijfers)
    )


def eerste_getal(tekst):
    if not tekst:
        return None

    match = re.search(
        r"(\d[\d\s.]*)",
        tekst,
    )

    if not match:
        return None

    waarde = (
        match.group(1)
        .replace(" ", "")
        .replace(".", "")
    )

    try:
        return int(waarde)

    except ValueError:
        return None


def extract_advertentie_id(url):
    if not url:
        return None

    patronen = [
        r"/vi/(\d+)\.htm",
        r"/ad/ventes_immobilieres/(\d+)",
    ]

    for patroon in patronen:
        match = re.search(
            patroon,
            url,
        )

        if match:
            return int(
                match.group(1)
            )

    return None


# ============================================================
# DEDUPLICATIE
# ============================================================

def dedupliceer_advertenties(advertenties):
    """
    Dedupliceert Leboncoin-alertrecords op advertentie_id.

    Als dezelfde advertentie meerdere keren voorkomt,
    bewaren we het record met de meeste ingevulde
    basisgegevens.
    """

    beste_per_id = {}

    for advertentie in advertenties:
        advertentie_id = advertentie.get(
            "advertentie_id"
        )

        if advertentie_id is None:
            continue

        score = sum(
            1
            for key in [
                "prijs",
                "woonoppervlakte",
                "perceeloppervlakte",
                "plaats",
                "postcode",
            ]
            if advertentie.get(key)
            not in (None, "")
        )

        bestaand = beste_per_id.get(
            advertentie_id
        )

        if bestaand is None:
            beste_per_id[
                advertentie_id
            ] = (
                score,
                advertentie,
            )

            continue

        bestaand_score, _ = bestaand

        if score > bestaand_score:
            beste_per_id[
                advertentie_id
            ] = (
                score,
                advertentie,
            )

    return [
        advertentie
        for _, advertentie
        in beste_per_id.values()
    ]

def extract_foto_url(tekst):
    """
    Zoekt een Leboncoin-afbeeldings-URL in een stuk
    alertmailtekst.

    Ondersteunt zowel Markdown-afbeeldingen als losse
    img.leboncoin.fr URL's.
    """

    if not tekst:
        return None

    patronen = [
        # Markdown:
        # ![...](https://img.leboncoin.fr/...)
        r'!\[[^\]]*\]\((https://img\.leboncoin\.fr/[^)\s]+)\)',

        # Losse Leboncoin image URL
        r'(https://img\.leboncoin\.fr/[^\s)"\']+)',
    ]

    for patroon in patronen:
        match = re.search(
            patroon,
            tekst,
            re.IGNORECASE,
        )

        if match:
            return match.group(1)

    return None

# ============================================================
# ALERT PARSER
# ============================================================

def parse_leboncoin_alert(body):
    """
    Parseert de tekstinhoud van één Leboncoin-alertmail.

    Retourneert een lijst met basisrecords.

    Dubbele advertentielinks in dezelfde mail worden
    automatisch gededupliceerd op advertentie_id.
    """

    if not body:
        return []

    patroon = re.compile(
        r"\[(?P<inhoud>.*?)\]"
        r"\((?P<url>"
        r"https://www\.leboncoin\.fr/"
        r"vi/\d+\.htm"
        r"[^)]*)\)",
        re.DOTALL | re.IGNORECASE,
    )

    resultaten = []

    for match in patroon.finditer(body):
        inhoud = match.group(
            "inhoud"
        )

        url = match.group(
            "url"
        )

        advertentie_id = (
            extract_advertentie_id(
                url
            )
        )

        if advertentie_id is None:
            continue

        foto_url = extract_foto_url(
            inhoud
        )

        # ----------------------------------------------------
        # PRIJS
        # ----------------------------------------------------

        prijs_match = re.search(
            r"([\d\s]+)\s*€",
            inhoud,
        )

        # ----------------------------------------------------
        # WOONOPPERVLAKTE
        # ----------------------------------------------------

        oppervlakte_match = re.search(
            r"Maison\s*·\s*"
            r"\d+\s*pièces?\s*·\s*"
            r"([\d\s]+)\s*m²",
            inhoud,
            re.IGNORECASE,
        )

        # ----------------------------------------------------
        # PERCEELOPPERVLAKTE
        # ----------------------------------------------------

        terrein_match = re.search(
            r"Terrain\s*:\s*"
            r"([\d\s]+)\s*m²",
            inhoud,
            re.IGNORECASE,
        )

        # ----------------------------------------------------
        # PLAATS + POSTCODE
        # ----------------------------------------------------

        locatie_match = re.search(
            r"\b"
            r"([A-Za-zÀ-ÿ'’ -]+)"
            r"\s+"
            r"(\d{5})"
            r"\b",
            inhoud,
        )

        record = {
            "advertentie_id": advertentie_id,

            "prijs": (
                prijs_naar_int(
                    prijs_match.group(1)
                )
                if prijs_match
                else None
            ),

            "woonoppervlakte": (
                eerste_getal(
                    oppervlakte_match.group(1)
                )
                if oppervlakte_match
                else None
            ),

            "perceeloppervlakte": (
                eerste_getal(
                    terrein_match.group(1)
                )
                if terrein_match
                else None
            ),

            "plaats": (
                locatie_match.group(1).strip()
                if locatie_match
                else None
            ),

            "postcode": (
                locatie_match.group(2)
                if locatie_match
                else None
            ),
            
            "foto_url": foto_url,
            "url": url,
        }

        resultaten.append(
            record
        )

    return dedupliceer_advertenties(
        resultaten
    )


# ============================================================
# ALERT + DETAIL COMBINEREN
# ============================================================

def combineer_alert_en_detail(
    alert,
    detail,
):
    """
    Combineert gegevens uit een Leboncoin-alertmail
    met gegevens van de detailpagina.

    Strategie:
    - detailpagina heeft voorrang;
    - ontbrekende detailwaarden worden aangevuld
      vanuit de alert;
    - False is een geldige detailwaarde;
    - de oorspronkelijke alert-URL blijft bewaard.
    """

    resultaat = dict(
        alert
    )

    resultaat[
        "alert_url"
    ] = alert.get(
        "url"
    )

    for key, value in detail.items():

        if (
            value is not None
            and value != ""
        ):
            resultaat[
                key
            ] = value

        elif key not in resultaat:
            resultaat[
                key
            ] = value

    return resultaat


# ============================================================
# SUCCESVOL VERWERKT
# ============================================================

def laad_verwerkte_ids():
    """
    Leest de reeds succesvol verwerkte
    Leboncoin advertentie-ID's.
    """

    if not VERWERKT_FILE.exists():
        return set()

    try:
        data = json.loads(
            VERWERKT_FILE.read_text(
                encoding="utf-8"
            )
        )

        return {
            int(advertentie_id)
            for advertentie_id in data
        }

    except (
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ) as exc:
        raise RuntimeError(
            f"Kan {VERWERKT_FILE} niet lezen: {exc}"
        ) from exc


def is_al_verwerkt(advertentie_id):
    return (
        int(advertentie_id)
        in laad_verwerkte_ids()
    )


def markeer_als_verwerkt(advertentie_id):
    verwerkt = laad_verwerkte_ids()

    verwerkt.add(
        int(advertentie_id)
    )

    VERWERKT_FILE.write_text(
        json.dumps(
            sorted(verwerkt),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# ============================================================
# DEFINITIEF ONBESCHIKBAAR
# ============================================================

def laad_onbeschikbare_ids():
    """
    Leest Leboncoin advertentie-ID's die definitief
    niet meer beschikbaar zijn.
    """

    if not ONBESCHIKBAAR_FILE.exists():
        return set()

    try:
        data = json.loads(
            ONBESCHIKBAAR_FILE.read_text(
                encoding="utf-8"
            )
        )

        return {
            int(advertentie_id)
            for advertentie_id in data
        }

    except (
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ) as exc:
        raise RuntimeError(
            f"Kan {ONBESCHIKBAAR_FILE} niet lezen: {exc}"
        ) from exc


def markeer_als_onbeschikbaar(advertentie_id):
    onbeschikbaar = laad_onbeschikbare_ids()

    onbeschikbaar.add(
        int(advertentie_id)
    )

    ONBESCHIKBAAR_FILE.write_text(
        json.dumps(
            sorted(onbeschikbaar),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # Eventuele tijdelijke fout is niet meer relevant.
    verwijder_retry(
        advertentie_id
    )


def is_onbeschikbaar(advertentie_id):
    return (
        int(advertentie_id)
        in laad_onbeschikbare_ids()
    )


# ============================================================
# RETRY / COOLDOWN
# ============================================================

def laad_retries():
    """
    Leest tijdelijke foutstatussen.

    Structuur:

    {
        "123456789": {
            "pogingen": 2,
            "laatste_fout": "HTTP status 403",
            "laatste_poging": "2026-09-14T..."
        }
    }
    """

    if not RETRY_FILE.exists():
        return {}

    try:
        data = json.loads(
            RETRY_FILE.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                "Retry-bestand bevat geen dictionary."
            )

        return data

    except (
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ) as exc:
        raise RuntimeError(
            f"Kan {RETRY_FILE} niet lezen: {exc}"
        ) from exc


def sla_retries_op(retries):
    RETRY_FILE.write_text(
        json.dumps(
            retries,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def registreer_retry(
    advertentie_id,
    fout,
):
    """
    Registreert een tijdelijke fout.
    """

    retries = laad_retries()

    sleutel = str(
        int(advertentie_id)
    )

    bestaand = retries.get(
        sleutel,
        {},
    )

    pogingen = (
        int(
            bestaand.get(
                "pogingen",
                0,
            )
        )
        + 1
    )

    retries[sleutel] = {
        "pogingen": pogingen,
        "laatste_fout": str(fout),
        "laatste_poging": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    }

    sla_retries_op(
        retries
    )


def verwijder_retry(advertentie_id):
    """
    Verwijdert een retry-record na succes of wanneer
    een advertentie definitief onbeschikbaar is.
    """

    retries = laad_retries()

    sleutel = str(
        int(advertentie_id)
    )

    if sleutel not in retries:
        return

    del retries[
        sleutel
    ]

    sla_retries_op(
        retries
    )


def mag_opnieuw_proberen(
    advertentie_id,
    cooldown_uren=RETRY_COOLDOWN_UREN,
):
    """
    True wanneer:
    - geen tijdelijke fout geregistreerd is; of
    - de cooldown is verstreken.
    """

    retries = laad_retries()

    sleutel = str(
        int(advertentie_id)
    )

    retry = retries.get(
        sleutel
    )

    if retry is None:
        return True

    laatste_poging = retry.get(
        "laatste_poging"
    )

    if not laatste_poging:
        return True

    try:
        tijdstip = datetime.fromisoformat(
            laatste_poging
        )

    except ValueError:
        return True

    if tijdstip.tzinfo is None:
        tijdstip = tijdstip.replace(
            tzinfo=timezone.utc
        )

    volgende_poging = (
        tijdstip
        + timedelta(
            hours=cooldown_uren
        )
    )

    return (
        datetime.now(
            timezone.utc
        )
        >= volgende_poging
    )


# ============================================================
# FILTER NIEUWE ADVERTENTIES
# ============================================================

def filter_nieuwe_advertenties(advertenties):
    """
    Retourneert advertenties die nu verwerkt
    mogen worden.

    Overslaan als:
    - succesvol verwerkt;
    - definitief onbeschikbaar;
    - tijdelijke fout en cooldown nog actief.
    """

    verwerkt = laad_verwerkte_ids()
    onbeschikbaar = laad_onbeschikbare_ids()

    resultaat = []

    for advertentie in advertenties:
        advertentie_id = advertentie.get(
            "advertentie_id"
        )

        if advertentie_id is None:
            continue

        if advertentie_id in verwerkt:
            continue

        if advertentie_id in onbeschikbaar:
            continue

        if not mag_opnieuw_proberen(
            advertentie_id
        ):
            continue

        resultaat.append(
            advertentie
        )

    return resultaat
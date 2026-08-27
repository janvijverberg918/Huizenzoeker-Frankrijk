import re

from logger import logger


# ---------------------------------------------------------
# Instellingen voor deduplicatie
# ---------------------------------------------------------

PRIJS_TOLERANTIE = 5000
OPPERVLAKTE_TOLERANTIE = 3


def normaliseer_getal(waarde):
    """
    Zet een waarde om naar een geheel getal.

    Voorbeelden:
    '€ 225.000' -> 225000
    '225 000 €' -> 225000
    '141 m²'    -> 141
    """

    if waarde is None:
        return None

    cijfers = re.findall(
        r"\d+",
        str(waarde),
    )

    if not cijfers:
        return None

    return int(
        "".join(cijfers)
    )


def haal_postcode(plaats):
    """
    Haalt alleen de postcode van 4 cijfers uit het plaatsveld.

    Voorbeelden:
    '6980 LA ROCHE-EN-ARDENNE' -> '6980'
    '6980 La Roche-en-Ardenne' -> '6980'
    """

    if not plaats:
        return None

    match = re.search(
        r"\b(\d{4})\b",
        str(plaats),
    )

    if match:
        return match.group(1)

    return None


def haal_kenmerken(woning):
    """
    Haalt de kenmerken op waarmee woningen worden vergeleken.
    """

    return {
        "postcode": haal_postcode(
            woning.get("plaats", "")
        ),
        "prijs": normaliseer_getal(
            woning.get("prijs", "")
        ),
        "slaapkamers": normaliseer_getal(
            woning.get("slaapkamers", "")
        ),
        "oppervlakte": normaliseer_getal(
            woning.get("oppervlakte", "")
        ),
    }


def heeft_voldoende_gegevens(kenmerken):
    """
    Controleert of alle noodzakelijke kenmerken bekend zijn.
    """

    return all(
        waarde is not None
        for waarde in kenmerken.values()
    )


def zijn_dezelfde_woning(
    woning_a,
    woning_b,
):
    """
    Bepaalt of twee advertenties waarschijnlijk
    dezelfde woning voorstellen.

    Regels:
    - exact dezelfde link = altijd dezelfde advertentie
    - anders:
        - postcode moet exact gelijk zijn
        - slaapkamers moeten exact gelijk zijn
        - prijs mag maximaal PRIJS_TOLERANTIE verschillen
        - oppervlakte mag maximaal
          OPPERVLAKTE_TOLERANTIE verschillen
    """

    # -----------------------------------------------------
    # Exact dezelfde link
    # -----------------------------------------------------
    link_a = str(
        woning_a.get(
            "link",
            "",
        )
    ).strip()

    link_b = str(
        woning_b.get(
            "link",
            "",
        )
    ).strip()

    if (
        link_a
        and link_b
        and link_a == link_b
    ):
        logger.info(
            "Exact dezelfde advertentielink gevonden: %s",
            link_a,
        )

        return True

    # -----------------------------------------------------
    # Kenmerken ophalen
    # -----------------------------------------------------
    kenmerken_a = haal_kenmerken(
        woning_a
    )

    kenmerken_b = haal_kenmerken(
        woning_b
    )

    # Niet gokken wanneer belangrijke gegevens ontbreken
    if not heeft_voldoende_gegevens(
        kenmerken_a
    ):
        return False

    if not heeft_voldoende_gegevens(
        kenmerken_b
    ):
        return False

    # -----------------------------------------------------
    # Postcode
    # -----------------------------------------------------
    if (
        kenmerken_a["postcode"]
        != kenmerken_b["postcode"]
    ):
        return False

    # -----------------------------------------------------
    # Slaapkamers
    # -----------------------------------------------------
    if (
        kenmerken_a["slaapkamers"]
        != kenmerken_b["slaapkamers"]
    ):
        return False

    # -----------------------------------------------------
    # Prijs
    # -----------------------------------------------------
    prijsverschil = abs(
        kenmerken_a["prijs"]
        - kenmerken_b["prijs"]
    )

    if prijsverschil > PRIJS_TOLERANTIE:
        return False

    # -----------------------------------------------------
    # Oppervlakte
    # -----------------------------------------------------
    oppervlakteverschil = abs(
        kenmerken_a["oppervlakte"]
        - kenmerken_b["oppervlakte"]
    )

    if (
        oppervlakteverschil
        > OPPERVLAKTE_TOLERANTIE
    ):
        return False

    logger.info(
        "Waarschijnlijke dubbele woning gevonden: "
        "postcode=%s, prijsverschil=%s, "
        "oppervlakteverschil=%s",
        kenmerken_a["postcode"],
        prijsverschil,
        oppervlakteverschil,
    )

    return True


def maak_brongegevens(woning):
    """
    Maakt een bronrecord voor gebruik in de e-mail.
    """

    return {
        "bron": woning.get(
            "bron",
            "Onbekend",
        ),
        "link": woning.get(
            "link",
            "",
        ),
    }


def voeg_bron_toe(
    bestaande_woning,
    nieuwe_woning,
):
    """
    Voegt de bron van een dubbele woning toe
    aan de bestaande samengevoegde woning.

    Dezelfde bron + dezelfde link wordt niet
    opnieuw toegevoegd.
    """

    brongegevens = maak_brongegevens(
        nieuwe_woning
    )

    bestaande_bronnen = bestaande_woning.get(
        "bronnen",
        [],
    )

    bron_bestaat_al = any(
        bron.get("bron")
        == brongegevens["bron"]
        and
        bron.get("link")
        == brongegevens["link"]
        for bron in bestaande_bronnen
    )

    if not bron_bestaat_al:
        bestaande_bronnen.append(
            brongegevens
        )

        logger.info(
            "Bron '%s' toegevoegd aan samengevoegde woning",
            brongegevens["bron"],
        )

    bestaande_woning["bronnen"] = (
        bestaande_bronnen
    )


def voeg_dubbele_woningen_samen(
    woningen,
):
    """
    Voegt dubbele advertenties samen.

    Strategie:

    1. Exact dezelfde link:
       altijd samenvoegen.

    2. Verschillende websites:
       tolerant vergelijken op:
       - postcode
       - slaapkamers
       - prijs
       - oppervlakte

    3. Dezelfde website met verschillende links:
       niet op basis van tolerantie samenvoegen.

    Dit is belangrijk voor Biddit, omdat hetzelfde
    object via meerdere zoekpostcodes kan terugkomen.
    """

    samengevoegde_woningen = []

    aantal_dubbelen = 0

    for woning in woningen:

        logger.info(
            "Controle deduplicatie: "
            "%s | %s | %s | %s m² | bron=%s",
            woning.get(
                "plaats",
                "Onbekend",
            ),
            woning.get(
                "prijs",
                "Onbekend",
            ),
            woning.get(
                "slaapkamers",
                "Onbekend",
            ),
            woning.get(
                "oppervlakte",
                "Onbekend",
            ),
            woning.get(
                "bron",
                "Onbekend",
            ),
        )

        gevonden_dubbel = None

        # -------------------------------------------------
        # Vergelijk met alle reeds gevonden woningen
        # -------------------------------------------------
        for bestaande_woning in samengevoegde_woningen:

            bron_nieuw = woning.get(
                "bron",
                "Onbekend",
            )

            bron_bestaand = bestaande_woning.get(
                "bron",
                "Onbekend",
            )

            link_nieuw = str(
                woning.get(
                    "link",
                    "",
                )
            ).strip()

            link_bestaand = str(
                bestaande_woning.get(
                    "link",
                    "",
                )
            ).strip()

            dezelfde_link = (
                link_nieuw
                and link_bestaand
                and link_nieuw == link_bestaand
            )

            # -------------------------------------------------
            # Zelfde website + andere link
            #
            # Niet tolerant samenvoegen.
            # Een website kan twee verschillende objecten
            # hebben die toevallig bijna dezelfde kenmerken
            # hebben.
            # -------------------------------------------------
            if (
                bron_nieuw == bron_bestaand
                and not dezelfde_link
            ):
                continue

            if zijn_dezelfde_woning(
                bestaande_woning,
                woning,
            ):
                gevonden_dubbel = (
                    bestaande_woning
                )

                break

        # -------------------------------------------------
        # Geen dubbel gevonden
        # -------------------------------------------------
        if gevonden_dubbel is None:
            nieuwe_woning = dict(
                woning
            )

            nieuwe_woning["bronnen"] = [
                maak_brongegevens(
                    woning
                )
            ]

            samengevoegde_woningen.append(
                nieuwe_woning
            )

            continue

        # -------------------------------------------------
        # Dubbele advertentie gevonden
        # -------------------------------------------------
        aantal_dubbelen += 1

        logger.info(
            "DUBBEL GEVONDEN: %s (%s) "
            "samengevoegd met %s (%s)",
            woning.get(
                "titel",
                "Onbekend",
            ),
            woning.get(
                "bron",
                "Onbekend",
            ),
            gevonden_dubbel.get(
                "titel",
                "Onbekend",
            ),
            gevonden_dubbel.get(
                "bron",
                "Onbekend",
            ),
        )

        voeg_bron_toe(
            gevonden_dubbel,
            woning,
        )

    logger.info(
        "Samenvoegen afgerond: "
        "%s advertenties gecontroleerd, "
        "%s dubbel(en) samengevoegd, "
        "%s unieke woningen over",
        len(woningen),
        aantal_dubbelen,
        len(samengevoegde_woningen),
    )

    return samengevoegde_woningen


def verwijder_dubbele_woningen(
    woningen,
):
    """
    Compatibiliteitsfunctie voor huizenzoeker.py.

    De functienaam stamt uit v2.1.
    Vanaf v2.2 worden advertenties samengevoegd
    in plaats van verwijderd.
    """

    return voeg_dubbele_woningen_samen(
        woningen
    )
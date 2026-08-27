from time import perf_counter

from ardenneimmo import zoek_ardenneimmo
from config import (
    ACTIEVE_ZOEKGEBIEDEN,
    APP_NAME,
    APP_VERSION,
    TEST_MODUS,
    ZOEKGEBIEDEN,
    ZOEKPROFIELEN,
    maak_csv_bestandsnaam,
)
from deduplicatie import verwijder_dubbele_woningen
from emailer import stuur_nieuwe_woningen
from immovlan import zoek_immovlan
from immoweb import zoek_immoweb
from biddit import zoek_biddit
from logger import logger

from advertentie_analyse import haal_immoweb_advertentie_op
from advertentie_analyse_ardenneimmo import (
    haal_ardenneimmo_advertentie_op,
)
from advertentie_analyse_immovlan import (
    haal_immovlan_advertentie_op,
)
from advertentie_analyse_biddit import (
    haal_biddit_advertentie_op,
)
from ai_analyse import analyseer_woning

def bepaal_bron(woning):
    """
    Geeft voor een woning een gestandaardiseerde bronnaam terug.
    """

    bron = str(
        woning.get(
            "bron",
            "",
        )
    ).lower()

    link = str(
        woning.get(
            "link",
            "",
        )
    ).lower()

    if (
        "immoweb" in bron
        or "immoweb.be" in link
    ):
        return "Immoweb"

    if (
        "immovlan" in bron
        or "immovlan.be" in link
    ):
        return "Immovlan"

    if (
        "ardenne" in bron
        or "ardenneimmo.be" in link
    ):
        return "Ardenne Immo"

    if (
        "biddit" in bron
        or "biddit.be" in link
    ):
        return "Biddit"

    return "Onbekend"

def verrijk_met_ai_huizencoach(woningen):
    """
    Verrijkt nieuwe woningen met een analyse
    van de AI Huizencoach.

    Momenteel ondersteund:
    - Immoweb
    - Ardenne Immo
    - Immovlan
    - Biddit

  
    Een fout bij één woning mag de overige woningen
    niet tegenhouden.
    """

    totaal = len(woningen)
    geanalyseerd = 0
    overgeslagen = 0
    mislukt = 0

    logger.info(
        "AI Huizencoach gestart voor %s unieke woning(en)",
        totaal,
    )

    print()
    print("=" * 60)
    print("AI HUIZENCOACH")
    print("=" * 60)

    for nummer, woning in enumerate(
        woningen,
        start=1,
    ):
        bron = str(
            woning.get(
                "bron",
                "",
            )
        ).lower()

        link = str(
            woning.get(
                "link",
                "",
            )
        ).strip()

        titel = woning.get(
            "titel",
            "Onbekende woning",
        )

        # -----------------------------------------------------
        # Bron bepalen
        # -----------------------------------------------------
        is_immoweb = (
            "immoweb" in bron
            or "immoweb.be" in link.lower()
        )

        is_ardenneimmo = (
            "ardenne" in bron
            or "ardenneimmo.be" in link.lower()
        )

        is_immovlan = (
            "immovlan" in bron
            or "immovlan.be" in link.lower()
        )
        is_biddit = (
            "biddit" in bron
            or "biddit.be" in link.lower()
        )
        # -----------------------------------------------------
        # Alleen ondersteunde bronnen analyseren
        # -----------------------------------------------------
        if not (
            is_immoweb
            or is_ardenneimmo
            or is_immovlan
            or is_biddit
        ):
            overgeslagen += 1

            logger.info(
                "AI-analyse overgeslagen voor "
                "nog niet ondersteunde bron: %s",
                link,
            )

            continue

        if not link:
            overgeslagen += 1

            logger.warning(
                "AI-analyse overgeslagen: woning heeft "
                "geen link"
            )

            continue

        print()
        print(
            f"[{nummer}/{totaal}] "
            f"AI analyseert: {titel}"
        )

        try:
            # -------------------------------------------------
            # Detailpagina uitlezen
            # -------------------------------------------------
            if is_immoweb:
                logger.info(
                    "Immoweb-detailanalyse gestart voor %s",
                    link,
                )

                advertentie = haal_immoweb_advertentie_op(
                    link
                )
            
            elif is_ardenneimmo:
                logger.info(
                    "Ardenne Immo-detailanalyse gestart voor %s",
                    link,
                )

                advertentie = haal_ardenneimmo_advertentie_op(
                    link
                )

            elif is_immovlan:
                logger.info(
                    "Immovlan-detailanalyse gestart voor %s",
                    link,
                )

                advertentie = haal_immovlan_advertentie_op(
                    link
                )
            elif is_biddit:
                logger.info(
                    "Biddit-detailanalyse gestart voor %s",
                    link,
                )

                advertentie = haal_biddit_advertentie_op(
                    link
                )
            else:
                # Dit zou door bovenstaande controle
                # niet bereikbaar moeten zijn.
                overgeslagen += 1
                continue

            # -------------------------------------------------
            # Gegevens uit het zoekresultaat behouden
            #
            # Als de detailpagina een waarde niet heeft,
            # gebruiken we de reeds bekende waarde uit
            # het zoekresultaat.
            # -------------------------------------------------
            for sleutel, waarde in woning.items():
                if (
                    sleutel not in advertentie
                    or advertentie.get(sleutel) in (
                        None,
                        "",
                        [],
                        {},
                    )
                ):
                    advertentie[sleutel] = waarde

            # -------------------------------------------------
            # AI-analyse
            # -------------------------------------------------
            analyse = analyseer_woning(
                advertentie
            )

            # -------------------------------------------------
            # AI-resultaat aan oorspronkelijke woning toevoegen
            # -------------------------------------------------
            woning["ai_score"] = analyse.get(
                "score"
            )

            woning["ai_advies"] = analyse.get(
                "advies",
                "",
            )

            woning["ai_samenvatting"] = analyse.get(
                "samenvatting",
                "",
            )

            woning["ai_sterke_punten"] = analyse.get(
                "sterke_punten",
                [],
            )

            woning["ai_aandachtspunten"] = analyse.get(
                "aandachtspunten",
                [],
            )

            woning["ai_ontbrekende_informatie"] = analyse.get(
                "ontbrekende_informatie",
                [],
            )

            woning["ai_betrouwbaarheid"] = analyse.get(
                "betrouwbaarheid",
                "",
            )

            # -------------------------------------------------
            # Detailinformatie bewaren
            # -------------------------------------------------
            woning["advertentie_details"] = advertentie

            # -------------------------------------------------
            # Gestructureerde detailkenmerken ook op
            # woningniveau beschikbaar maken.
            # -------------------------------------------------
            kenmerken = advertentie.get(
                "kenmerken",
                {},
            )

            if kenmerken:
                woning["kenmerken"] = kenmerken

            # -------------------------------------------------
            # Hoofdfoto
            # -------------------------------------------------
            fotos = advertentie.get(
                "fotos",
                [],
            )

            if fotos:
                woning["hoofdfoto"] = fotos[0]

            geanalyseerd += 1

            print(
                f"    Bron   : "
                f"{advertentie.get('bron', 'Onbekend')}"
            )

            print(
                f"    Score  : "
                f"{woning['ai_score']} / 10"
            )

            print(
                f"    Advies : "
                f"{woning['ai_advies']}"
            )

            logger.info(
                "AI Huizencoach afgerond voor %s: "
                "score=%s, advies=%s",
                link,
                woning["ai_score"],
                woning["ai_advies"],
            )

        except Exception:
            mislukt += 1

            logger.exception(
                "AI Huizencoach mislukt voor woning: %s",
                link,
            )

            # -------------------------------------------------
            # De woning blijft gewoon in de resultaten staan.
            #
            # Een mislukte AI-analyse mag nooit betekenen dat
            # we de woning niet meer per e-mail ontvangen.
            # -------------------------------------------------
            woning["ai_score"] = None
            woning["ai_advies"] = ""
            woning["ai_samenvatting"] = ""
            woning["ai_sterke_punten"] = []
            woning["ai_aandachtspunten"] = []
            woning["ai_ontbrekende_informatie"] = []
            woning["ai_betrouwbaarheid"] = ""

    print()
    print(
        f"AI-analyses voltooid : {geanalyseerd}"
    )

    print(
        f"AI overgeslagen      : {overgeslagen}"
    )

    print(
        f"AI mislukt            : {mislukt}"
    )

    print("=" * 60)

    logger.info(
        "AI Huizencoach afgerond: "
        "%s geanalyseerd, %s overgeslagen, %s mislukt",
        geanalyseerd,
        overgeslagen,
        mislukt,
    )

    return woningen

def main():
    starttijd = perf_counter()

    print("=" * 60)
    print(f"{APP_NAME} {APP_VERSION}")
    print("=" * 60)

    if TEST_MODUS:
        print("TESTMODUS ACTIEF")
        print(
            f"Actieve zoekgebieden: {len(ACTIEVE_ZOEKGEBIEDEN)}"
        )
        print("=" * 60)

    logger.info("Huizenzoeker gestart")

    if TEST_MODUS:
        logger.info(
            "TESTMODUS actief: %s van %s zoekgebieden worden gebruikt",
            len(ACTIEVE_ZOEKGEBIEDEN),
            len(ZOEKGEBIEDEN),
        )

    alle_nieuwe_woningen = []

    geslaagde_zoekopdrachten = 0
    mislukte_zoekopdrachten = 0
    totaal_zoekopdrachten = 0

    # ---------------------------------------------------------
    # Performance-metingen
    # ---------------------------------------------------------
    zoektijd_per_bron = {
        "immoweb": 0.0,
        "immovlan": 0.0,
        "ardenneimmo": 0.0,
        "biddit": 0.0,
    }

    ai_looptijd = 0.0
    email_looptijd = 0.0

    # ---------------------------------------------------------
    # Alle zoekprofielen doorlopen
    # ---------------------------------------------------------
    for profiel in ZOEKPROFIELEN:
        profielnaam = profiel["naam"]

        logger.info(
            "Zoekprofiel '%s' gestart",
            profielnaam,
        )

        print()
        print("=" * 60)
        print(f"Zoekprofiel: {profielnaam}")
        print("=" * 60)

        # -----------------------------------------------------
        # Alleen de actieve zoekgebieden doorlopen
        # -----------------------------------------------------
        for gebied in ACTIEVE_ZOEKGEBIEDEN:
            gebied_naam = gebied["naam"]
            postcode = gebied["postcode"]

            print()
            print(
                f"Zoekgebied: {gebied_naam} ({postcode})"
            )
            print("-" * 60)

            logger.info(
                "Zoekgebied '%s' (%s) gestart",
                gebied_naam,
                postcode,
            )

            # -------------------------------------------------
            # Alle websites voor dit profiel doorlopen
            # -------------------------------------------------
            for website in profiel["websites"]:
                totaal_zoekopdrachten += 1
                website_starttijd = perf_counter()

                csv_bestand = maak_csv_bestandsnaam(
                    gebied,
                    website,
                )

                logger.info(
                    "Website '%s' gestart voor "
                    "zoekgebied '%s' (%s)",
                    website,
                    gebied_naam,
                    postcode,
                )

                logger.info(
                    "CSV-bestand voor deze zoekopdracht: %s",
                    csv_bestand,
                )

                try:
                    # -----------------------------------------
                    # Immoweb
                    # -----------------------------------------
                    if website == "immoweb":
                        resultaten_website = zoek_immoweb(
                            postcode,
                            profiel["woningtype"],
                            profiel["min_prijs"],
                            profiel["max_prijs"],
                            csv_bestand,
                        )

                    # -----------------------------------------
                    # Immovlan
                    # -----------------------------------------
                    elif website == "immovlan":
                        resultaten_website = zoek_immovlan(
                            postcode,
                            profiel["woningtype"],
                            profiel["min_prijs"],
                            profiel["max_prijs"],
                            csv_bestand,
                        )

                    # -----------------------------------------
                    # Ardenne Immo
                    # -----------------------------------------
                    elif website == "ardenneimmo":
                        resultaten_website = zoek_ardenneimmo(
                            postcode,
                            profiel["woningtype"],
                            profiel["min_prijs"],
                            profiel["max_prijs"],
                            csv_bestand,
                        )

                    # -----------------------------------------
                    # Biddit
                    # -----------------------------------------
                    elif website == "biddit":
                        resultaten_website = zoek_biddit(
                            postcode,
                            profiel["woningtype"],
                            profiel["min_prijs"],
                            profiel["max_prijs"],
                            csv_bestand,
                        )

                    # -----------------------------------------
                    # Onbekende website
                    # -----------------------------------------
                    else:
                        logger.warning(
                            "Onbekende website '%s' "
                            "voor zoekgebied '%s'",
                            website,
                            gebied_naam,
                        )
                        continue

                    # -----------------------------------------
                    # Zoekgebied toevoegen aan iedere woning
                    # -----------------------------------------
                    for woning in resultaten_website:
                        woning["zoekprofiel"] = profielnaam
                        woning["zoekgebied"] = gebied_naam
                        woning["postcode_zoekgebied"] = postcode

                    alle_nieuwe_woningen.extend(
                        resultaten_website
                    )

                    geslaagde_zoekopdrachten += 1

                    logger.info(
                        "Website '%s' afgerond voor "
                        "zoekgebied '%s' met %s "
                        "nieuwe woning(en)",
                        website,
                        gebied_naam,
                        len(resultaten_website),
                    )

                except Exception:
                    mislukte_zoekopdrachten += 1

                    logger.exception(
                        "Website '%s' is mislukt voor "
                        "zoekgebied '%s' (%s)",
                        website,
                        gebied_naam,
                        postcode,
                    )

                    # Een fout op één website/gebied
                    # mag de rest van de Ardennen niet stoppen.

                finally:
                    website_looptijd = (
                        perf_counter()
                        - website_starttijd
                    )

                    if website in zoektijd_per_bron:
                        zoektijd_per_bron[
                            website
                        ] += website_looptijd

                    logger.info(
                        "Looptijd website '%s' voor "
                        "zoekgebied '%s': %.1f seconden",
                        website,
                        gebied_naam,
                        website_looptijd,
                    )

            logger.info(
                "Zoekgebied '%s' afgerond",
                gebied_naam,
            )

        logger.info(
            "Zoekprofiel '%s' afgerond",
            profielnaam,
        )

    # ---------------------------------------------------------
    # Deduplicatie
    # ---------------------------------------------------------
    aantal_voor_deduplicatie = len(
        alle_nieuwe_woningen
    )

    unieke_nieuwe_woningen = verwijder_dubbele_woningen(
        alle_nieuwe_woningen
    )

    aantal_na_deduplicatie = len(
        unieke_nieuwe_woningen
    )

    aantal_dubbelen = (
        aantal_voor_deduplicatie
        - aantal_na_deduplicatie
    )

    nieuwe_per_bron = {
        "Immoweb": 0,
        "Immovlan": 0,
        "Ardenne Immo": 0,
        "Biddit": 0,
        "Onbekend": 0,
    }

    for woning in alle_nieuwe_woningen:
        bron = bepaal_bron(
            woning
        )

        nieuwe_per_bron[bron] += 1

    logger.info(
        "Deduplicatie afgerond: "
        "%s advertenties -> %s unieke woningen",
        aantal_voor_deduplicatie,
        aantal_na_deduplicatie,
    )

    logger.info(
        "Dubbele advertenties samengevoegd: %s",
        aantal_dubbelen,
    )

    # ---------------------------------------------------------
    # AI-statistieken per bron
    # Altijd initialiseren, ook als er 0 nieuwe woningen zijn.
    # ---------------------------------------------------------
    ai_per_bron = {
        "Immoweb": 0,
        "Immovlan": 0,
        "Ardenne Immo": 0,
        "Biddit": 0,
        "Onbekend": 0,
    }

    # ---------------------------------------------------------
    # AI Huizencoach
    #
    # Pas NA deduplicatie zodat dezelfde woning niet
    # meerdere keren door de AI wordt beoordeeld.
    # ---------------------------------------------------------
    if unieke_nieuwe_woningen:
        ai_starttijd = perf_counter()

        unieke_nieuwe_woningen = verrijk_met_ai_huizencoach(
            unieke_nieuwe_woningen
        )

        ai_looptijd = (
            perf_counter()
            - ai_starttijd
        )

        for woning in unieke_nieuwe_woningen:
            if woning.get(
                "ai_score"
            ) is not None:
                bron = bepaal_bron(
                    woning
                )

                ai_per_bron[bron] += 1

    # ---------------------------------------------------------
    # Eén gecombineerde e-mail
    # ---------------------------------------------------------
    if unieke_nieuwe_woningen:
        email_starttijd = perf_counter()

        try:
            stuur_nieuwe_woningen(
                unieke_nieuwe_woningen
            )

            logger.info(
                "Gecombineerde e-mail verstuurd met "
                "%s unieke nieuwe woning(en)",
                len(unieke_nieuwe_woningen),
            )

        except Exception:
            logger.exception(
                "Gecombineerde e-mail kon "
                "niet worden verstuurd"
            )

        finally:
            email_looptijd = (
                perf_counter()
                - email_starttijd
            )

    else:
        print()
        print(
            "Geen unieke nieuwe woningen gevonden."
        )

        logger.info(
            "Geen unieke nieuwe woningen; "
            "geen e-mail verstuurd"
        )

    # ---------------------------------------------------------
    # Samenvatting
    # ---------------------------------------------------------
    looptijd = perf_counter() - starttijd

    logger.info("=" * 60)

    logger.info(
        "Samenvatting Huizenzoeker %s",
        APP_VERSION,
    )

    logger.info(
        "Testmodus                   : %s",
        "AAN" if TEST_MODUS else "UIT",
    )

    logger.info(
        "Zoekprofielen              : %s",
        len(ZOEKPROFIELEN),
    )

    logger.info(
        "Zoekgebieden beschikbaar   : %s",
        len(ZOEKGEBIEDEN),
    )

    logger.info(
        "Zoekgebieden actief        : %s",
        len(ACTIEVE_ZOEKGEBIEDEN),
    )

    logger.info(
        "Zoekopdrachten totaal      : %s",
        totaal_zoekopdrachten,
    )

    logger.info(
        "Zoekopdrachten geslaagd    : %s",
        geslaagde_zoekopdrachten,
    )

    logger.info(
        "Zoekopdrachten mislukt     : %s",
        mislukte_zoekopdrachten,
    )

    logger.info(
        "Nieuwe advertenties        : %s",
        aantal_voor_deduplicatie,
    )

    logger.info(
        "Dubbele advertenties "
        "samengevoegd : %s",
        aantal_dubbelen,
    )

    logger.info(
        "Unieke nieuwe woningen     : %s",
        aantal_na_deduplicatie,
    )

    logger.info("-" * 60)

    logger.info(
        "Nieuwe advertenties per bron"
    )

    for bron in (
        "Immoweb",
        "Immovlan",
        "Ardenne Immo",
        "Biddit",
    ):
        logger.info(
            "%-30s : %s",
            bron,
            nieuwe_per_bron[bron],
        )

    if nieuwe_per_bron["Onbekend"]:
        logger.info(
            "%-30s : %s",
            "Onbekend",
            nieuwe_per_bron["Onbekend"],
        )

    logger.info("-" * 60)

    logger.info(
        "AI-analyses per bron"
    )

    for bron in (
        "Immoweb",
        "Immovlan",
        "Ardenne Immo",
        "Biddit",
    ):
        logger.info(
            "%-30s : %s",
            bron,
            ai_per_bron[bron],
        )

    if ai_per_bron["Onbekend"]:
        logger.info(
            "%-30s : %s",
            "Onbekend",
            ai_per_bron["Onbekend"],
        )

    logger.info("-" * 60)

    logger.info(
        "Looptijd per bron"
    )

    logger.info(
        "%-30s : %.1f seconden",
        "Immoweb",
        zoektijd_per_bron["immoweb"],
    )

    logger.info(
        "%-30s : %.1f seconden",
        "Immovlan",
        zoektijd_per_bron["immovlan"],
    )

    logger.info(
        "%-30s : %.1f seconden",
        "Ardenne Immo",
        zoektijd_per_bron["ardenneimmo"],
    )

    logger.info(
        "%-30s : %.1f seconden",
        "Biddit",
        zoektijd_per_bron["biddit"],
    )

    totale_zoektijd = sum(
        zoektijd_per_bron.values()
    )

    logger.info(
        "%-30s : %.1f seconden",
        "Totaal zoeken",
        totale_zoektijd,
    )

    logger.info(
        "%-30s : %.1f seconden",
        "AI Huizencoach",
        ai_looptijd,
    )

    logger.info(
        "%-30s : %.1f seconden",
        "E-mail",
        email_looptijd,
    )

    logger.info("-" * 60)

    logger.info(
        "Totale looptijd            : %.1f seconden",
        looptijd,
    )

    logger.info("=" * 60)
    logger.info("Huizenzoeker afgerond")


if __name__ == "__main__":
    main()

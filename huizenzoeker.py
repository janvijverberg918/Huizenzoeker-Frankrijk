from time import perf_counter

from bienici import (
    haal_bienici_advertentie_op,
    zoek_bienici,
)

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
from logger import logger
from ai_analyse import analyseer_woning
from logicimmo import zoek_logicimmo


# ============================================================
# HUIZENZOEKER FRANKRIJK
# ============================================================
#
# Architectuur
# ------------
#
# Dit bestand is de centrale "regisseur" van de Huizenzoeker.
#
# Het weet NIET hoe een specifieke woningsite technisch werkt.
# Dat hoort thuis in aparte bronmodules, bijvoorbeeld:
#
#   seloger.py
#   leboncoin.py
#   bienici.py
#   logicimmo.py
#
# De bronmodules worden hieronder geregistreerd zodra ze
# ontwikkeld en getest zijn.
#
# Daardoor blijft huizenzoeker.py zoveel mogelijk
# bron-onafhankelijk.
# ============================================================


# ============================================================
# BRONREGISTRATIE
# ============================================================
#
# Iedere zoekfunctie moet uiteindelijk hetzelfde contract
# gebruiken:
#
# def zoek_bron(
#     postcode,
#     woningtype,
#     min_prijs,
#     max_prijs,
#     csv_bestand,
# ):
#     ...
#     return lijst_met_nieuwe_woningen
#
#
# Iedere detailfunctie krijgt een URL en retourneert een
# dictionary met de uitgelezen woningdetails:
#
# def haal_bron_advertentie_op(url):
#     ...
#     return advertentie
#
#
# Tijdens fase 1.0.0-dev zijn de registers nog leeg.
# ============================================================


ZOEKFUNCTIES = {
    "bienici": zoek_bienici,
}


DETAILFUNCTIES = {
    "bienici": haal_bienici_advertentie_op,#
}
# Mooie namen voor logging en e-mail/statistieken.
#
# Zodra een bron wordt toegevoegd, komt hier ook de
# gebruikersvriendelijke naam te staan.
BRONNAMEN = {
     "bienici": "Bien'ici",
  }


# ============================================================
# HULPFUNCTIES BRONNEN
# ============================================================


def actieve_websites_bepalen():
    """
    Geeft alle unieke websites terug die in de actieve
    zoekprofielen zijn geconfigureerd.

    Voorbeeld:

    [
        "seloger",
        "bienici",
    ]

    Een website wordt maar één keer opgenomen, ook wanneer
    deze later in meerdere zoekprofielen zou voorkomen.
    """

    websites = []

    for profiel in ZOEKPROFIELEN:
        for website in profiel.get(
            "websites",
            [],
        ):
            if website not in websites:
                websites.append(
                    website
                )

    return websites


def mooie_bronnaam(bron_sleutel):
    """
    Zet een interne bronsleutel om naar een leesbare naam.

    Bijvoorbeeld:

        "seloger" -> "SeLoger"

    Als een bron nog niet in BRONNAMEN staat, wordt de
    interne sleutel gebruikt.
    """

    if not bron_sleutel:
        return "Onbekend"

    return BRONNAMEN.get(
        bron_sleutel,
        str(bron_sleutel),
    )


def bepaal_bron_sleutel(woning):
    """
    Bepaalt van welke bron een woning afkomstig is.

    Nieuwe Franse bronmodules moeten bij voorkeur het veld

        bron_sleutel

    aan iedere woning toevoegen.

    Bijvoorbeeld:

        woning["bron_sleutel"] = "seloger"

    huizenzoeker.py voegt dit veld ook automatisch toe als
    een zoekmodule dit vergeet.
    """

    bron_sleutel = woning.get(
        "bron_sleutel"
    )

    if bron_sleutel:
        return str(
            bron_sleutel
        ).strip().lower()

    bron = str(
        woning.get(
            "bron",
            "",
        )
    ).strip().lower()

    # Eerst kijken of de leesbare bronnaam overeenkomt.
    for sleutel, naam in BRONNAMEN.items():
        if bron == naam.lower():
            return sleutel

        if bron == sleutel.lower():
            return sleutel

    return ""


def bepaal_bronnaam(woning):
    """
    Geeft een leesbare bronnaam terug voor logging en
    samenvattingen.
    """

    bron_sleutel = bepaal_bron_sleutel(
        woning
    )

    if bron_sleutel:
        return mooie_bronnaam(
            bron_sleutel
        )

    bron = woning.get(
        "bron"
    )

    if bron:
        return str(bron)

    return "Onbekend"


# ============================================================
# AI HUIZENCOACH
# ============================================================


def verrijk_met_ai_huizencoach(
    woningen,
):
    """
    Verrijkt unieke nieuwe woningen met:

    1. detailinformatie van de oorspronkelijke website;
    2. analyse van de AI Huizencoach.

    BELANGRIJK
    ----------
    De AI wordt pas uitgevoerd NA centrale deduplicatie.

    Daardoor analyseren we dezelfde woning niet meerdere
    keren wanneer deze via verschillende zoekgebieden of
    bronnen wordt gevonden.

    Een fout bij één woning mag de overige woningen nooit
    tegenhouden.
    """

    totaal = len(
        woningen
    )

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

        bron_sleutel = bepaal_bron_sleutel(
            woning
        )

        bronnaam = bepaal_bronnaam(
            woning
        )

        # ----------------------------------------------------
        # Link controleren
        # ----------------------------------------------------

        if not link:
            overgeslagen += 1

            logger.warning(
                "AI-analyse overgeslagen: woning heeft "
                "geen advertentielink"
            )

            continue

        # ----------------------------------------------------
        # Detailparser zoeken
        # ----------------------------------------------------

        detailfunctie = DETAILFUNCTIES.get(
            bron_sleutel
        )

        if detailfunctie is None:
            overgeslagen += 1

            logger.info(
                "AI-analyse overgeslagen voor bron '%s': "
                "nog geen detailparser geregistreerd",
                bronnaam,
            )

            continue

        print()
        print(
            f"[{nummer}/{totaal}] "
            f"AI analyseert: {titel}"
        )

        print(
            f"    Bron   : {bronnaam}"
        )

        try:
            # ------------------------------------------------
            # Detailpagina uitlezen
            # ------------------------------------------------

            logger.info(
                "%s-detailanalyse gestart voor %s",
                bronnaam,
                link,
            )

            advertentie = detailfunctie(
                link
            )

            if not isinstance(
                advertentie,
                dict,
            ):
                raise ValueError(
                    f"Detailparser van {bronnaam} "
                    f"heeft geen dictionary teruggegeven"
                )

            # ------------------------------------------------
            # Basisgegevens uit zoekresultaat behouden
            # ------------------------------------------------
            #
            # Als de detailpagina een waarde niet bevat,
            # gebruiken we de waarde die we al vanuit de
            # zoekresultaatkaart hadden.
            # ------------------------------------------------

            for sleutel, waarde in woning.items():
                if (
                    sleutel not in advertentie
                    or advertentie.get(
                        sleutel
                    ) in (
                        None,
                        "",
                        [],
                        {},
                    )
                ):
                    advertentie[
                        sleutel
                    ] = waarde

            # ------------------------------------------------
            # AI-analyse
            # ------------------------------------------------

            analyse = analyseer_woning(
                advertentie
            )

            if not isinstance(
                analyse,
                dict,
            ):
                raise ValueError(
                    "AI Huizencoach heeft geen "
                    "dictionary teruggegeven"
                )

            # ------------------------------------------------
            # AI-resultaten opslaan
            # ------------------------------------------------

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

            woning[
                "ai_ontbrekende_informatie"
            ] = analyse.get(
                "ontbrekende_informatie",
                [],
            )

            woning[
                "ai_betrouwbaarheid"
            ] = analyse.get(
                "betrouwbaarheid",
                "",
            )

            # ------------------------------------------------
            # Detaildata bewaren
            # ------------------------------------------------

            woning[
                "advertentie_details"
            ] = advertentie

            kenmerken = advertentie.get(
                "kenmerken",
                {},
            )

            if kenmerken:
                woning[
                    "kenmerken"
                ] = kenmerken

            # ------------------------------------------------
            # Hoofdfoto
            # ------------------------------------------------

            fotos = advertentie.get(
                "fotos",
                [],
            )

            if fotos:
                woning[
                    "hoofdfoto"
                ] = fotos[0]

            geanalyseerd += 1

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

            # ------------------------------------------------
            # Woning NIET verwijderen
            # ------------------------------------------------
            #
            # Een mislukte AI-analyse mag nooit betekenen
            # dat de gebruiker de woning niet ontvangt.
            # ------------------------------------------------

            woning["ai_score"] = None
            woning["ai_advies"] = ""
            woning["ai_samenvatting"] = ""
            woning["ai_sterke_punten"] = []
            woning["ai_aandachtspunten"] = []

            woning[
                "ai_ontbrekende_informatie"
            ] = []

            woning[
                "ai_betrouwbaarheid"
            ] = ""

    print()
    print(
        f"AI-analyses voltooid : "
        f"{geanalyseerd}"
    )

    print(
        f"AI overgeslagen      : "
        f"{overgeslagen}"
    )

    print(
        f"AI mislukt            : "
        f"{mislukt}"
    )

    print("=" * 60)

    logger.info(
        "AI Huizencoach afgerond: "
        "%s geanalyseerd, "
        "%s overgeslagen, "
        "%s mislukt",
        geanalyseerd,
        overgeslagen,
        mislukt,
    )

    return woningen


# ============================================================
# MAIN
# ============================================================


def main():
    """
    Hoofdprogramma van Huizenzoeker Frankrijk.

    Proces:

    1. configuratie gebruiken;
    2. zoekprofielen doorlopen;
    3. zoekgebieden doorlopen;
    4. actieve bronnen uitvoeren;
    5. nieuwe advertenties verzamelen;
    6. centrale deduplicatie;
    7. detailanalyse + AI;
    8. e-mail;
    9. samenvatting en performance.
    """

    starttijd = perf_counter()

    print("=" * 60)
    print(
        f"{APP_NAME} {APP_VERSION}"
    )
    print("=" * 60)

    actieve_websites = (
        actieve_websites_bepalen()
    )

    if TEST_MODUS:
        print(
            "TESTMODUS ACTIEF"
        )

        print(
            f"Actieve zoekgebieden: "
            f"{len(ACTIEVE_ZOEKGEBIEDEN)}"
        )

        print("=" * 60)

    logger.info(
        "Huizenzoeker gestart"
    )

    if TEST_MODUS:
        logger.info(
            "TESTMODUS actief: "
            "%s van %s zoekgebieden worden gebruikt",
            len(ACTIEVE_ZOEKGEBIEDEN),
            len(ZOEKGEBIEDEN),
        )

    logger.info(
        "Actieve websites: %s",
        len(actieve_websites),
    )

    if actieve_websites:
        logger.info(
            "Websites in deze run: %s",
            ", ".join(
                actieve_websites
            ),
        )
    else:
        logger.info(
            "Geen websites geconfigureerd "
            "voor deze run"
        )

    # ========================================================
    # Centrale statistieken
    # ========================================================

    alle_nieuwe_woningen = []

    geslaagde_zoekopdrachten = 0
    mislukte_zoekopdrachten = 0
    totaal_zoekopdrachten = 0

    # Performance per actieve bron.
    zoektijd_per_bron = {
        website: 0.0
        for website in actieve_websites
    }

    ai_looptijd = 0.0
    email_looptijd = 0.0

    # ========================================================
    # Alle zoekprofielen
    # ========================================================

    for profiel in ZOEKPROFIELEN:
        profielnaam = profiel[
            "naam"
        ]

        websites_profiel = profiel.get(
            "websites",
            [],
        )

        logger.info(
            "Zoekprofiel '%s' gestart",
            profielnaam,
        )

        print()
        print("=" * 60)
        print(
            f"Zoekprofiel: "
            f"{profielnaam}"
        )
        print("=" * 60)

        # ====================================================
        # Zoekgebieden
        # ====================================================

        for gebied in ACTIEVE_ZOEKGEBIEDEN:
            gebied_naam = gebied[
                "naam"
            ]

            postcode = gebied[
                "postcode"
            ]

            departement = gebied.get(
                "departement",
                "",
            )

            print()
            print(
                f"Zoekgebied: "
                f"{gebied_naam} "
                f"({postcode})"
            )

            if departement:
                print(
                    f"Departement: "
                    f"{departement}"
                )

            print("-" * 60)

            logger.info(
                "Zoekgebied '%s' (%s) gestart",
                gebied_naam,
                postcode,
            )

            # ================================================
            # Websites binnen dit profiel
            # ================================================

            for website in websites_profiel:
                totaal_zoekopdrachten += 1

                website_starttijd = (
                    perf_counter()
                )

                csv_bestand = (
                    maak_csv_bestandsnaam(
                        gebied,
                        website,
                    )
                )

                logger.info(
                    "Website '%s' gestart voor "
                    "zoekgebied '%s' (%s)",
                    website,
                    gebied_naam,
                    postcode,
                )

                logger.info(
                    "CSV-bestand voor deze "
                    "zoekopdracht: %s",
                    csv_bestand,
                )

                try:
                    # ----------------------------------------
                    # Geregistreerde zoekfunctie zoeken
                    # ----------------------------------------

                    zoekfunctie = (
                        ZOEKFUNCTIES.get(
                            website
                        )
                    )

                    if zoekfunctie is None:
                        raise ValueError(
                            f"Website '{website}' staat "
                            f"in config.py maar heeft nog "
                            f"geen geregistreerde "
                            f"zoekfunctie."
                        )

                    # ----------------------------------------
                    # Website uitvoeren
                    # ----------------------------------------

                    resultaten_website = (
                        zoekfunctie(
                            postcode,
                            profiel[
                                "woningtype"
                            ],
                            profiel[
                                "min_prijs"
                            ],
                            profiel[
                                "max_prijs"
                            ],
                            csv_bestand,
                        )
                    )

                    if resultaten_website is None:
                        resultaten_website = []

                    if not isinstance(
                        resultaten_website,
                        list,
                    ):
                        raise ValueError(
                            f"Zoekfunctie van "
                            f"'{website}' heeft geen "
                            f"lijst teruggegeven."
                        )

                    # ----------------------------------------
                    # Centrale metadata toevoegen
                    # ----------------------------------------

                    for woning in resultaten_website:
                        woning[
                            "zoekprofiel"
                        ] = profielnaam

                        woning[
                            "zoekgebied"
                        ] = gebied_naam

                        woning[
                            "postcode_zoekgebied"
                        ] = postcode

                        woning[
                            "departement"
                        ] = departement

                        # Dit maakt de bron later altijd
                        # eenduidig herkenbaar.
                        if not woning.get(
                            "bron_sleutel"
                        ):
                            woning[
                                "bron_sleutel"
                            ] = website

                        if not woning.get(
                            "bron"
                        ):
                            woning[
                                "bron"
                            ] = mooie_bronnaam(
                                website
                            )

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
                        len(
                            resultaten_website
                        ),
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

                    # Een fout op één bron/postcode
                    # mag de rest van Frankrijk niet stoppen.

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
                        "zoekgebied '%s': "
                        "%.1f seconden",
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

    # ========================================================
    # Deduplicatie
    # ========================================================

    aantal_voor_deduplicatie = len(
        alle_nieuwe_woningen
    )

    unieke_nieuwe_woningen = (
        verwijder_dubbele_woningen(
            alle_nieuwe_woningen
        )
    )

    aantal_na_deduplicatie = len(
        unieke_nieuwe_woningen
    )

    aantal_dubbelen = (
        aantal_voor_deduplicatie
        - aantal_na_deduplicatie
    )

    logger.info(
        "Deduplicatie afgerond: "
        "%s advertenties -> "
        "%s unieke woningen",
        aantal_voor_deduplicatie,
        aantal_na_deduplicatie,
    )

    logger.info(
        "Dubbele advertenties "
        "samengevoegd: %s",
        aantal_dubbelen,
    )

    # ========================================================
    # Nieuwe advertenties per bron
    # ========================================================

    nieuwe_per_bron = {
        website: 0
        for website in actieve_websites
    }

    onbekende_bronnen = 0

    for woning in alle_nieuwe_woningen:
        bron_sleutel = bepaal_bron_sleutel(
            woning
        )

        if bron_sleutel in nieuwe_per_bron:
            nieuwe_per_bron[
                bron_sleutel
            ] += 1
        else:
            onbekende_bronnen += 1

    # ========================================================
    # AI-statistieken
    # ========================================================

    ai_per_bron = {
        website: 0
        for website in actieve_websites
    }

    ai_onbekende_bronnen = 0

    # ========================================================
    # AI Huizencoach
    # ========================================================

    if unieke_nieuwe_woningen:
        ai_starttijd = perf_counter()

        unieke_nieuwe_woningen = (
            verrijk_met_ai_huizencoach(
                unieke_nieuwe_woningen
            )
        )

        ai_looptijd = (
            perf_counter()
            - ai_starttijd
        )

        for woning in unieke_nieuwe_woningen:
            if woning.get(
                "ai_score"
            ) is not None:
                bron_sleutel = (
                    bepaal_bron_sleutel(
                        woning
                    )
                )

                if bron_sleutel in ai_per_bron:
                    ai_per_bron[
                        bron_sleutel
                    ] += 1
                else:
                    ai_onbekende_bronnen += 1

    # ========================================================
    # E-mail
    # ========================================================

    if unieke_nieuwe_woningen:
        email_starttijd = perf_counter()

        try:
            stuur_nieuwe_woningen(
                unieke_nieuwe_woningen
            )

            logger.info(
                "Gecombineerde e-mail verstuurd "
                "met %s unieke nieuwe woning(en)",
                len(
                    unieke_nieuwe_woningen
                ),
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

    # ========================================================
    # Samenvatting
    # ========================================================

    looptijd = (
        perf_counter()
        - starttijd
    )

    logger.info(
        "=" * 60
    )

    logger.info(
        "Samenvatting Huizenzoeker %s",
        APP_VERSION,
    )

    logger.info(
        "Testmodus                   : %s",
        "AAN"
        if TEST_MODUS
        else "UIT",
    )

    logger.info(
        "Zoekprofielen              : %s",
        len(
            ZOEKPROFIELEN
        ),
    )

    logger.info(
        "Zoekgebieden beschikbaar   : %s",
        len(
            ZOEKGEBIEDEN
        ),
    )

    logger.info(
        "Zoekgebieden actief        : %s",
        len(
            ACTIEVE_ZOEKGEBIEDEN
        ),
    )

    logger.info(
        "Actieve websites           : %s",
        len(
            actieve_websites
        ),
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

    # ========================================================
    # Nieuwe woningen per bron
    # ========================================================

    if actieve_websites:
        logger.info(
            "-" * 60
        )

        logger.info(
            "Nieuwe advertenties per bron"
        )

        for website in actieve_websites:
            logger.info(
                "%-30s : %s",
                mooie_bronnaam(
                    website
                ),
                nieuwe_per_bron.get(
                    website,
                    0,
                ),
            )

        if onbekende_bronnen:
            logger.info(
                "%-30s : %s",
                "Onbekend",
                onbekende_bronnen,
            )

    # ========================================================
    # AI per bron
    # ========================================================

    if actieve_websites:
        logger.info(
            "-" * 60
        )

        logger.info(
            "AI-analyses per bron"
        )

        for website in actieve_websites:
            logger.info(
                "%-30s : %s",
                mooie_bronnaam(
                    website
                ),
                ai_per_bron.get(
                    website,
                    0,
                ),
            )

        if ai_onbekende_bronnen:
            logger.info(
                "%-30s : %s",
                "Onbekend",
                ai_onbekende_bronnen,
            )

    # ========================================================
    # Performance
    # ========================================================

    logger.info(
        "-" * 60
    )

    logger.info(
        "Looptijd per bron"
    )

    if actieve_websites:
        for website in actieve_websites:
            logger.info(
                "%-30s : %.1f seconden",
                mooie_bronnaam(
                    website
                ),
                zoektijd_per_bron.get(
                    website,
                    0.0,
                ),
            )
    else:
        logger.info(
            "%-30s : %s",
            "Geen actieve websites",
            "-",
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

    logger.info(
        "-" * 60
    )

    logger.info(
        "Totale looptijd            : "
        "%.1f seconden",
        looptijd,
    )

    logger.info(
        "=" * 60
    )

    logger.info(
        "Huizenzoeker afgerond"
    )


# ============================================================
# PROGRAMMA STARTEN
# ============================================================

if __name__ == "__main__":
    main()
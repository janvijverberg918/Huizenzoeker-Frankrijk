"""
Leboncoin productie-runner voor Huizenzoeker Frankrijk.

Flow:
Gmail alerts
→ advertenties extraheren
→ dedupliceren
→ statusfilter
→ Leboncoin detailpagina
→ Huizencoach-adapter
→ AI-analyse
→ gecombineerde e-mail
→ succesvol markeren

Belangrijk:
Een advertentie wordt pas als verwerkt gemarkeerd nadat
de gecombineerde e-mail succesvol is verstuurd.
"""
import time

from gmail_leboncoin import (
    gmail_service,
    zoek_leboncoin_alerts,
    haal_email_op,
    haal_email_body_op,
)

from leboncoin import (
    start_leboncoin_browser,
    haal_detail_op_met_context,
)

from leboncoin_alerts import (
    parse_leboncoin_alert,
    dedupliceer_advertenties,
    combineer_alert_en_detail,
    filter_nieuwe_advertenties,
    markeer_als_verwerkt,
    markeer_als_onbeschikbaar,
    registreer_retry,
    verwijder_retry,
)

from leboncoin_huizencoach import (
    maak_huizencoach_woning,
    voeg_ai_analyse_toe,
)

from ai_analyse import (
    analyseer_woning,
)

from emailer import (
    stuur_nieuwe_woningen,
)


MAX_ALERTMAILS = 50

# Bescherming tegen te veel Leboncoin-detailrequests in één run.
MAX_ADVERTENTIES_PER_RUN = 3

# Pauze tussen twee Leboncoin-detailrequests.
DETAIL_WACHTTIJD_SECONDEN = 4

def is_http_410(exc):
    """
    Controleert of een fout aangeeft dat de advertentie
    definitief verdwenen is.
    """

    tekst = str(exc).lower()

    return (
        "http status 410" in tekst
        or "status 410" in tekst
    )

def is_http_403(exc):
    """
    Controleert of Leboncoin de detailpagina blokkeert
    met HTTP 403.
    """

    tekst = str(exc).lower()

    return (
        "http status 403" in tekst
        or "status 403" in tekst
    )

def main():

    print("=" * 72)
    print("HUIZENZOEKER FRANKRIJK - LEBONCOIN")
    print("=" * 72)

    # ========================================================
    # STAP 1 - Gmail verbinden
    # ========================================================

    print()
    print("Gmail verbinden...")

    try:
        service = gmail_service()
    #Start hier
    except Exception as exc:
        print()
        print("FOUT bij Gmail verbinding:")
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return

    print("Gmail verbinding: OK")

    # ========================================================
    # STAP 2 - Leboncoin-alertmails ophalen
    # ========================================================

    print()
    print(
        f"Maximaal {MAX_ALERTMAILS} "
        "Leboncoin-alertmails ophalen..."
    )

    try:
        mails = zoek_leboncoin_alerts(
            service,
            max_results=MAX_ALERTMAILS,
        )

    except Exception as exc:
        print()
        print("FOUT bij ophalen Gmail-alerts:")
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return

    print(
        f"Gevonden alertmails: {len(mails)}"
    )

    if not mails:
        print()
        print(
            "Geen Leboncoin-alertmails gevonden."
        )
        return

    # ========================================================
    # STAP 3 - Alle advertenties uit alle mails verzamelen
    # ========================================================

    alle_advertenties = []
    #start hier met for
    for nummer, mail in enumerate(
        mails,
        start=1,
    ):

        print()
        print("-" * 72)
        print(
            f"MAIL {nummer} VAN {len(mails)}"
        )
        print("-" * 72)

        message_id = mail.get("id")

        # ----------------------------------------------------
        # Volledige Gmail-mail ophalen
        # ----------------------------------------------------

        try:
            email = haal_email_op(
                service,
                message_id,
            )

            body = haal_email_body_op(
                email
            )

        except Exception as exc:
            print(
                f"Mail kon niet worden gelezen: "
                f"{type(exc).__name__}: {exc}"
            )
            continue

        subject = email.get(
            "subject",
            "",
        )

        print(
            f"Message ID : {message_id}"
        )
        print(
            f"Subject    : {subject}"
        )

        # ----------------------------------------------------
        # Leboncoin-advertenties uit mail halen
        # ----------------------------------------------------

        try:
            advertenties = (
                parse_leboncoin_alert(
                    body
                )
            )

        except Exception as exc:
            print(
                f"Parserfout: "
                f"{type(exc).__name__}: {exc}"
            )
            continue

        print(
            "Advertenties gevonden: "
            f"{len(advertenties)}"
        )

        alle_advertenties.extend(
            advertenties
        )
        #hier moet het haakje staan
    # ========================================================
    # STAP 4 - Dedupliceren
    # ========================================================

    print()
    print("=" * 72)
    print("ADVERTENTIES VERZAMELD")
    print("=" * 72)

    aantal_voor = len(
        alle_advertenties
    )

    unieke_advertenties = (
        dedupliceer_advertenties(
            alle_advertenties
        )
    )

    print(
        f"Totaal vóór deduplicatie : "
        f"{aantal_voor}"
    )

    print(
        f"Uniek na deduplicatie     : "
        f"{len(unieke_advertenties)}"
    )

    # ========================================================
    # STAP 5 - Statusfilter
    # ========================================================

    try:
        nieuwe_advertenties = (
            filter_nieuwe_advertenties(
                unieke_advertenties
            )
        )

    except Exception as exc:
        print()
        print("FOUT bij statusfilter:")
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return

    
    ### start here

    aantal_beschikbaar = len(
    nieuwe_advertenties
    )

    print(
        f"Beschikbaar voor verwerking: "
        f"{aantal_beschikbaar}"
    )

    if not nieuwe_advertenties:
        print()
        print(
            "Geen nieuwe Leboncoin-advertenties "
            "om te verwerken."
        )

        print()
        print("=" * 72)
        print("RUN AFGEROND")
        print("=" * 72)

        return


    # ========================================================
    # BATCHLIMIET
    # ========================================================

    nieuwe_advertenties = (
        nieuwe_advertenties[
            :MAX_ADVERTENTIES_PER_RUN
        ]
    )

    print(
        f"Deze run verwerkt maximaal : "
        f"{MAX_ADVERTENTIES_PER_RUN}"
    )

    print(
        f"Deze run te verwerken      : "
        f"{len(nieuwe_advertenties)}"
    )

    resterend = (
        aantal_beschikbaar
        - len(nieuwe_advertenties)
    )

    if resterend > 0:
        print(
            f"Doorgeschoven naar later   : "
            f"{resterend}"
        )
        
        print(
            f"Te verwerken              : "
            f"{len(nieuwe_advertenties)}"
        )

        if not nieuwe_advertenties:
            print()
            print(
                "Geen nieuwe Leboncoin-advertenties "
                "om te verwerken."
            )
        
            print()
            print("=" * 72)
            print("RUN AFGEROND")
            print("=" * 72)

            return
        
    # ========================================================
    # STAP 6 - Detail + AI
    # ========================================================
    
    email_woningen = []

    succesvolle_ids = []
    onbeschikbare_ids = []
    mislukte_ids = []
    fallback_403_ids = []


    # ========================================================
    # Eén Leboncoin browsersessie voor de volledige batch
    # ========================================================

    playwright = None
    browser = None
    context = None

    try:
        print()
        print("Leboncoin browser starten...")

        playwright, browser, context = (
            start_leboncoin_browser()
        )

        print("Leboncoin browser: OK")

    except Exception as exc:
        print()
        print("FOUT bij starten Leboncoin browser:")
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return


    for nummer, alert in enumerate(
        nieuwe_advertenties,
        start=1,
    ):
    

        advertentie_id = alert.get(
            "advertentie_id"
        )

        alert_url = alert.get(
            "url"
        )

        print()
        print("=" * 72)
        print(
            f"ADVERTENTIE {nummer} "
            f"VAN {len(nieuwe_advertenties)}"
        )
        print("=" * 72)

        print(
            f"Advertentie ID : {advertentie_id}"
        )

        print(
            f"Alert URL      : {alert_url}"
        )

        # ----------------------------------------------------
        # Detailpagina
        # ----------------------------------------------------

        # ----------------------------------------------------
        # Rust tussen Leboncoin detailrequests
        # ----------------------------------------------------

        if nummer > 1:
            print()
            print(
                f"{DETAIL_WACHTTIJD_SECONDEN} seconden "
                "wachten voor volgende detailrequest..."
            )

            time.sleep(
                DETAIL_WACHTTIJD_SECONDEN
            )


        print()
        print("Detailpagina ophalen...")

        try:
            detail = haal_detail_op_met_context(
                context,
                alert_url,
            )
        #start hier
        except Exception as exc:

            print()
            print("FOUT bij detailpagina:")
            print(
                f"{type(exc).__name__}: {exc}"
            )

            # ------------------------------------------------
            # HTTP 410 - advertentie definitief verdwenen
            # ------------------------------------------------

            if is_http_410(exc):

                print()
                print(
                    "Advertentie is definitief "
                    "niet meer beschikbaar."
                )

                markeer_als_onbeschikbaar(
                    advertentie_id
                )

                onbeschikbare_ids.append(
                    advertentie_id
                )

                continue

            # ------------------------------------------------
            # HTTP 403 - verder met gegevens uit alertmail
            # ------------------------------------------------

            if is_http_403(exc):

                print()
                print(
                    "Leboncoin detailpagina niet toegankelijk "
                    "(HTTP 403)."
                )

                print(
                    "Verder met beschikbare gegevens "
                    "uit de alertmail."
                )

                detail = {}
                fallback_403_ids.append(
                    advertentie_id
                )

            # ------------------------------------------------
            # Andere fout - later opnieuw proberen
            # ------------------------------------------------

            else:

                registreer_retry(
                    advertentie_id,
                    (
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    ),
                )

                mislukte_ids.append(
                    advertentie_id
                )

                print()
                print(
                    "Tijdelijke fout geregistreerd. "
                    "Advertentie wordt later opnieuw geprobeerd."
                )

                continue
            
                if advertentie_id in fallback_403_ids:
                    print(
                        "Detailpagina: niet beschikbaar - "
                        "alertgegevens worden gebruikt"
                    )
                else:
                    print("Detailpagina: OK")

        # ----------------------------------------------------
        # Alert + detail
        # ----------------------------------------------------

        try:
            gecombineerd = (
                combineer_alert_en_detail(
                    alert,
                    detail,
                )
            )

        except Exception as exc:

            print()
            print(
                "FOUT bij combineren:"
            )

            print(
                f"{type(exc).__name__}: {exc}"
            )

            registreer_retry(
                advertentie_id,
                (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            )

            mislukte_ids.append(
                advertentie_id
            )

            continue

        # ----------------------------------------------------
        # Huizencoach adapter
        # ----------------------------------------------------

        try:
            woning = (
                maak_huizencoach_woning(
                    gecombineerd
                )
            )

        except Exception as exc:

            print()
            print(
                "FOUT bij Huizencoach-adapter:"
            )

            print(
                f"{type(exc).__name__}: {exc}"
            )

            registreer_retry(
                advertentie_id,
                (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            )

            mislukte_ids.append(
                advertentie_id
            )

            continue

        # ----------------------------------------------------
        # AI
        # ----------------------------------------------------

        print()
        print("AI Huizencoach analyse...")

        try:
            analyse = analyseer_woning(
                woning
            )

        except Exception as exc:

            print()
            print(
                "FOUT bij AI-analyse:"
            )

            print(
                f"{type(exc).__name__}: {exc}"
            )

            registreer_retry(
                advertentie_id,
                (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            )

            mislukte_ids.append(
                advertentie_id
            )

            continue

        print(
            f"AI score  : "
            f"{analyse.get('score')}"
        )

        print(
            f"AI advies : "
            f"{analyse.get('advies')}"
        )

        # ----------------------------------------------------
        # E-mailrecord
        # ----------------------------------------------------

        try:
            email_woning = (
                voeg_ai_analyse_toe(
                    woning,
                    analyse,
                )
            )

        except Exception as exc:

            print()
            print(
                "FOUT bij maken e-mailrecord:"
            )

            print(
                f"{type(exc).__name__}: {exc}"
            )

            registreer_retry(
                advertentie_id,
                (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            )

            mislukte_ids.append(
                advertentie_id
            )

            continue

        email_woningen.append(
            email_woning
        )

        succesvolle_ids.append(
            advertentie_id
        )

        print(
            "Woning gereed voor e-mail."
        )

    # ========================================================
    # Leboncoin browser sluiten
    # ========================================================

    print()
    print("Leboncoin browser sluiten...")

    try:
        if context is not None:
            context.close()

        if browser is not None:
            browser.close()

    finally:
        if playwright is not None:
            playwright.stop()

    print("Leboncoin browser gesloten.")

    # ========================================================
    # STAP 7 - Gecombineerde e-mail
    # ========================================================

    print()
    print("=" * 72)
    print("E-MAIL")
    print("=" * 72)

    if email_woningen:

        print(
            f"Woningen in e-mail: "
            f"{len(email_woningen)}"
        )

        try:

            stuur_nieuwe_woningen(
                email_woningen,
                bron_titel="Leboncoin",
            )

        except Exception as exc:

            print()
            print(
                "FOUT bij versturen gecombineerde e-mail:"
            )

            print(
                f"{type(exc).__name__}: {exc}"
            )

            # Geen van deze advertenties als verwerkt markeren.
            # Ze moeten later opnieuw kunnen worden aangeboden.

            for advertentie_id in succesvolle_ids:

                registreer_retry(
                    advertentie_id,
                    (
                        "E-mailfout: "
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    ),
                )

            print()
            print(
                "Geen advertenties als verwerkt gemarkeerd."
            )

            return

        print()
        print(
            "Gecombineerde e-mail succesvol verstuurd."
        )

        # ====================================================
        # STAP 8 - Pas NU markeren als verwerkt
        # ====================================================

        print()
        print(
            "Advertenties als verwerkt markeren..."
        )

        for advertentie_id in succesvolle_ids:

            markeer_als_verwerkt(
                advertentie_id
            )

            verwijder_retry(
                advertentie_id
            )

            print(
                f"  {advertentie_id}: verwerkt"
            )

    else:

        print(
            "Geen woningen beschikbaar voor e-mail."
        )

    # ========================================================
    # EINDRAPPORT
    # ========================================================

    print()
    print("=" * 72)
    print("EINDRAPPORT")
    print("=" * 72)

    print(
        f"Gmail-alertmails gelezen : "
        f"{len(mails)}"
    )

    print(
        f"Advertenties aangetroffen: "
        f"{aantal_voor}"
    )

    print(
        f"Unieke advertenties      : "
        f"{len(unieke_advertenties)}"
    )

    print(
        f"Beschikbaar              : "
        f"{aantal_beschikbaar}"
    )

    print(
        f"Deze run geprobeerd      : "
        f"{len(nieuwe_advertenties)}"
    )

    print(
        f"Doorgeschoven            : "
        f"{resterend}"
    )

    print(
        f"In e-mail verzonden      : "
        f"{len(email_woningen)}"
    )

    print(
        f"Onbeschikbaar            : "
        f"{len(onbeschikbare_ids)}"
    )

    print(
        f"Mislukt                  : "
        f"{len(mislukte_ids)}"
    )

    if onbeschikbare_ids:
        print()
        print(
            "Definitief onbeschikbare ID's:"
        )

        for advertentie_id in onbeschikbare_ids:
            print(
                f"  - {advertentie_id}"
            )

    if mislukte_ids:
        print()
        print(
            "Tijdelijk mislukte ID's:"
        )

        for advertentie_id in mislukte_ids:
            print(
                f"  - {advertentie_id}"
            )

    print()
    print("=" * 72)
    print("LEBONCOIN RUN AFGEROND")
    print("=" * 72)
    print(
        f"Via alertdata (HTTP 403) : "
        f"{len(fallback_403_ids)}"
    )


if __name__ == "__main__":
    main()
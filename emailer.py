import smtplib
from email.message import EmailMessage
from html import escape

from config import (
    APP_VERSION,
    EMAIL_ADDRESS,
    EMAIL_PASSWORD,
    EMAIL_TO,
)
from logger import logger


def controleer_emailinstellingen():
    ontbreekt = []

    if not EMAIL_ADDRESS:
        ontbreekt.append("EMAIL_ADDRESS")

    if not EMAIL_PASSWORD:
        ontbreekt.append("EMAIL_PASSWORD")

    if not EMAIL_TO:
        ontbreekt.append("EMAIL_TO")

    if ontbreekt:
        namen = ", ".join(ontbreekt)

        raise ValueError(
            f"Deze instellingen ontbreken in .env: {namen}"
        )


def stuur_testmail():
    """
    Stuurt een eenvoudige testmail om de Gmail-verbinding
    te controleren.
    """

    controleer_emailinstellingen()

    bericht = EmailMessage()
    bericht["From"] = EMAIL_ADDRESS
    bericht["To"] = EMAIL_TO
    bericht["Subject"] = "[Huizenzoeker] Testmail"

    bericht.set_content(
        "Dit is een testmail van de Python Huizenzoeker.\n\n"
        "Als je deze mail ontvangt, werkt de e-mailverbinding."
    )

    try:
        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
            timeout=30,
        ) as smtp:
            smtp.login(
                EMAIL_ADDRESS,
                EMAIL_PASSWORD,
            )

            smtp.send_message(
                bericht
            )

        print(
            "Testmail succesvol verstuurd."
        )

    except smtplib.SMTPAuthenticationError:
        logger.exception(
            "Gmail heeft de aanmelding geweigerd"
        )

        print(
            "Gmail heeft de aanmelding geweigerd."
        )

        print(
            "Controleer het Gmail-adres "
            "en het app-wachtwoord."
        )

    except Exception:
        logger.exception(
            "Testmail kon niet worden verstuurd"
        )

        raise

def formatteer_prijs(prijs):
    """
    Formatteert een woningprijs voor weergave in de e-mail.

    Voorbeelden:
    245000     -> € 245.000
    "245000"   -> € 245.000
    155000.0   -> € 155.000

    Onbekende of niet-numerieke waarden blijven leesbaar.
    """

    if prijs in (
        None,
        "",
        "Onbekend",
    ):
        return "Onbekend"

    try:
        bedrag = int(
            float(
                str(prijs)
                .replace("€", "")
                .replace(".", "")
                .replace(",", ".")
                .replace(" ", "")
                .strip()
            )
        )

        bedrag_tekst = (
            f"{bedrag:,}"
            .replace(",", ".")
        )

        return f"€ {bedrag_tekst}"

    except (
        ValueError,
        TypeError,
    ):
        return str(prijs)

def haal_bronnen_op(woning):
    """
    Geeft alle bronnen van een woning terug.

    Voor woningen die op meerdere websites voorkomen,
    kan dit bijvoorbeeld zijn:
    - Immoweb
    - Immovlan
    - Ardenne Immo
    - Biddit

    Voor woningen zonder 'bronnen'-lijst wordt automatisch
    het bestaande bron/link-paar gebruikt.
    """

    bronnen = woning.get(
        "bronnen"
    )

    if bronnen:
        return bronnen

    return [
        {
            "bron": woning.get(
                "bron",
                "Onbekend",
            ),
            "link": woning.get(
                "link",
                "",
            ),
        }
    ]


def haal_foto_op(woning):
    """
    Geeft de beste beschikbare foto-URL van een woning terug.

    Volgorde:
    1. hoofdfoto uit advertentie-analyse
    2. bestaande foto op woningniveau
    3. foto uit een van de bronnen
    """

    hoofdfoto = woning.get(
        "hoofdfoto",
        "",
    )

    if hoofdfoto:
        return str(
            hoofdfoto
        ).strip()

    foto = woning.get(
        "foto",
        "",
    )

    if foto:
        return str(
            foto
        ).strip()

    bronnen = woning.get(
        "bronnen",
        [],
    )

    for bron in bronnen:
        foto = bron.get(
            "foto",
            "",
        )

        if foto:
            return str(
                foto
            ).strip()

    return ""

def maak_ai_html(woning):
    """
    Maakt het AI Huizencoach-blok voor de HTML-e-mail.

    Geeft een lege string terug als de woning
    niet door de AI Huizencoach is geanalyseerd.
    """

    score = woning.get(
        "ai_score"
    )

    advies = woning.get(
        "ai_advies",
        "",
    )

    if score is None or not advies:
        return ""

    samenvatting = escape(
        str(
            woning.get(
                "ai_samenvatting",
                "",
            )
        )
    )

    betrouwbaarheid = escape(
        str(
            woning.get(
                "ai_betrouwbaarheid",
                "",
            )
        )
    )

    sterke_punten = woning.get(
        "ai_sterke_punten",
        [],
    )

    aandachtspunten = woning.get(
        "ai_aandachtspunten",
        [],
    )

    ontbrekende_informatie = woning.get(
        "ai_ontbrekende_informatie",
        [],
    )

    sterke_html = ""

    if sterke_punten:
        items = "".join(
            f"<li>{escape(str(punt))}</li>"
            for punt in sterke_punten
        )

        sterke_html = f"""
            <div style="margin-top: 14px;">
                <strong>Sterke punten</strong>
                <ul style="
                    margin: 6px 0 0 20px;
                    padding: 0;
                ">
                    {items}
                </ul>
            </div>
        """

    aandacht_html = ""

    if aandachtspunten:
        items = "".join(
            f"<li>{escape(str(punt))}</li>"
            for punt in aandachtspunten
        )

        aandacht_html = f"""
            <div style="margin-top: 14px;">
                <strong>Aandachtspunten</strong>
                <ul style="
                    margin: 6px 0 0 20px;
                    padding: 0;
                ">
                    {items}
                </ul>
            </div>
        """

    ontbrekend_html = ""

    if ontbrekende_informatie:
        items = "".join(
            f"<li>{escape(str(punt))}</li>"
            for punt in ontbrekende_informatie
        )

        ontbrekend_html = f"""
            <div style="margin-top: 14px;">
                <strong>Nog uitzoeken</strong>
                <ul style="
                    margin: 6px 0 0 20px;
                    padding: 0;
                ">
                    {items}
                </ul>
            </div>
        """

    return f"""
        <div style="
            margin: 18px 0 4px 0;
            padding: 16px;
            background-color: #f5f7fa;
            border: 1px solid #d8dde6;
            border-radius: 8px;
        ">
            <div style="
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
            ">
                AI Huizencoach
            </div>

            <p style="margin: 5px 0;">
                <strong>Score:</strong>
                {escape(str(score))} / 10
            </p>

            <p style="margin: 5px 0;">
                <strong>Advies:</strong>
                {escape(str(advies))}
            </p>

            <p style="margin: 5px 0;">
                <strong>Betrouwbaarheid:</strong>
                {betrouwbaarheid}
            </p>

            <p style="
                margin: 14px 0 0 0;
                line-height: 1.5;
            ">
                {samenvatting}
            </p>

            {sterke_html}
            {aandacht_html}
            {ontbrekend_html}
        </div>
    """

def stuur_nieuwe_woningen(
    nieuwe_woningen
):
    """
    Stuurt één HTML-e-mail, gegroepeerd per zoekprofiel.

    Eén woning kan meerdere bronnen bevatten.
    Perceeloppervlakte wordt alleen getoond als deze bekend is.
    Indien beschikbaar wordt de hoofdfoto bovenaan de
    woningkaart weergegeven.
    """

    if not nieuwe_woningen:
        print(
            "Geen nieuwe woningen, dus geen e-mail verstuurd."
        )
        return

    controleer_emailinstellingen()

    # ---------------------------------------------------------
    # Woningen groeperen per zoekprofiel
    # ---------------------------------------------------------
    profielen = {}

    for woning in nieuwe_woningen:
        profielnaam = woning.get(
            "zoekprofiel",
            "Overig",
        )

        if profielnaam not in profielen:
            profielen[
                profielnaam
            ] = []

        profielen[
            profielnaam
        ].append(
            woning
        )
        # ---------------------------------------------------------
    # Woningen per zoekprofiel sorteren op AI-score
    # Hoogste score eerst.
    # Woningen zonder AI-score komen onderaan.
    # ---------------------------------------------------------
    for profielnaam in profielen:
        profielen[
            profielnaam
        ].sort(
            key=lambda woning: (
                woning.get("ai_score") is not None,
                woning.get("ai_score")
                if woning.get("ai_score") is not None
                else -1,
            ),
            reverse=True,
        )

    totaal_aantal = len(
        nieuwe_woningen
    )
    aantal_profielen = len(
        profielen
    )

    # ---------------------------------------------------------
    # E-mailbasis
    # ---------------------------------------------------------
    bericht = EmailMessage()

    bericht["From"] = EMAIL_ADDRESS
    bericht["To"] = EMAIL_TO

    bericht["Subject"] = (
        f"[Huizenzoeker] {totaal_aantal} nieuwe "
        f"woning{'en' if totaal_aantal != 1 else ''} "
        f"in {aantal_profielen} zoekprofiel"
        f"{'en' if aantal_profielen != 1 else ''}"
    )

    # ---------------------------------------------------------
    # Platte tekstversie
    # ---------------------------------------------------------
    tekstregels = [
        f"Huizenzoeker {APP_VERSION}",
        "",
        f"Totaal: {totaal_aantal} nieuwe "
        f"woning{'en' if totaal_aantal != 1 else ''}.",
        "",
    ]

    for profielnaam, woningen in profielen.items():
        tekstregels.extend(
            [
                "=" * 60,
                profielnaam,
                f"{len(woningen)} nieuwe "
                f"woning{'en' if len(woningen) != 1 else ''}",
                "",
            ]
        )

        for woning in woningen:
            tekstregels.extend(
                [
                    f"Type: {woning.get('titel', 'Onbekend')}",
                    f"Prijs: {formatteer_prijs(woning.get('prijs'))}",
                    f"Slaapkamers: "
                    f"{woning.get('slaapkamers', 'Onbekend')}",
                    f"Oppervlakte: "
                    f"{woning.get('oppervlakte', 'Onbekend')} m²",
                ]
            )

            perceeloppervlakte = woning.get(
                "perceeloppervlakte",
                "",
            )

            if perceeloppervlakte not in (
                "",
                None,
                "Onbekend",
            ):
                tekstregels.append(
                    f"Perceeloppervlakte: "
                    f"{perceeloppervlakte} m²"
                )

            tekstregels.extend(
                [
                    f"Plaats: {woning.get('plaats', 'Onbekend')}",
                    "Bronnen:",
                ]
            )

            bronnen = haal_bronnen_op(
                woning
            )

            for bron in bronnen:
                bronnaam = bron.get(
                    "bron",
                    "Onbekend",
                )

                link = bron.get(
                    "link",
                    "",
                )

                tekstregels.append(
                    f"- {bronnaam}: {link}"
                )

            tekstregels.append(
                ""
            )

    bericht.set_content(
        "\n".join(
            tekstregels
        )
    )

    # ---------------------------------------------------------
    # HTML-opbouw
    # ---------------------------------------------------------
    profielblokken = []

    for profielnaam, woningen in profielen.items():
        woningblokken = []

        for woning in woningen:
            titel = escape(
                str(
                    woning.get(
                        "titel",
                        "Onbekend",
                    )
                )
            )

            prijs = escape(
                formatteer_prijs(
                    woning.get(
                        "prijs"
                    )
                )
            )
            
            kenmerken = woning.get(
                "kenmerken",
                {},
            )

            slaapkamers = woning.get(
                "slaapkamers"
            )

            if slaapkamers in (
                None,
                "",
                "Onbekend",
            ):
                slaapkamers = kenmerken.get(
                    "slaapkamers"
                )

            if slaapkamers in (
                None,
                "",
            ):
                slaapkamers = "Onbekend"

            slaapkamers = str(
                slaapkamers
            )

            oppervlakte = woning.get(
                "oppervlakte"
            )

            if oppervlakte in (
                None,
                "",
                "Onbekend",
            ):
                oppervlakte = kenmerken.get(
                    "woonoppervlakte"
                )

            if oppervlakte in (
                None,
                "",
            ):
                oppervlakte = "Onbekend"

            oppervlakte = str(
                oppervlakte
            )

            perceeloppervlakte = woning.get(
                "perceeloppervlakte"
            )

            if perceeloppervlakte in (
                None,
                "",
                "Onbekend",
            ):
                perceeloppervlakte = kenmerken.get(
                    "perceeloppervlakte"
                )

            if perceeloppervlakte in (
                None,
                "",
            ):
                perceeloppervlakte = "Onbekend"

            perceeloppervlakte = str(
                perceeloppervlakte
            ) 

            plaats = escape(
                str(
                    woning.get(
                        "plaats",
                        "Onbekend",
                    )
                )
            )

            slaapkamers_tekst = (
                slaapkamers
                if slaapkamers != "Onbekend"
                else "Niet vermeld"
            )

            oppervlakte_tekst = (
                f"{oppervlakte} m²"
                if oppervlakte != "Onbekend"
                else "Niet vermeld"
            )

            # -------------------------------------------------
            # Perceeloppervlakte
            # -------------------------------------------------
            perceel_html = ""

            if perceeloppervlakte not in (
                "",
                "None",
                "Onbekend",
            ):
                perceel_html = f"""
                    <p style="
                        margin: 6px 0;
                    ">
                        <strong>Perceeloppervlakte:</strong>
                        {escape(perceeloppervlakte)} m²
                    </p>
                """
            
            # -------------------------------------------------
            # Hoofdfoto
            # -------------------------------------------------
            foto = haal_foto_op(
                woning
            )

            foto_html = ""

            if foto:
                veilige_foto = escape(
                    foto,
                    quote=True,
                )

                foto_html = f"""
                    <div style="
                        margin: -18px -18px 18px -18px;
                    ">
                        <img
                            src="{veilige_foto}"
                            alt="Foto van de woning"
                            style="
                                display: block;
                                width: 100%;
                                max-width: 100%;
                                height: auto;
                                max-height: 420px;
                                object-fit: cover;
                                border-radius: 8px 8px 0 0;
                            "
                        >
                    </div>
                """

            # -------------------------------------------------
            # Bronknoppen maken
            # -------------------------------------------------
            bronnen = haal_bronnen_op(
                woning
            )

            bron_namen = []
            knoppen = []

            for bron in bronnen:
                bronnaam = str(
                    bron.get(
                        "bron",
                        "Onbekend",
                    )
                )

                link = str(
                    bron.get(
                        "link",
                        "",
                    )
                )

                veilige_bronnaam = escape(
                    bronnaam
                )

                veilige_link = escape(
                    link,
                    quote=True,
                )

                bron_namen.append(
                    veilige_bronnaam
                )

                if veilige_link:
                    knoppen.append(
                        f"""
                        <a href="{veilige_link}" style="
                            display: inline-block;
                            padding: 10px 16px;
                            margin: 0 8px 8px 0;
                            background-color: #1a73e8;
                            color: #ffffff;
                            text-decoration: none;
                            border-radius: 5px;
                            font-weight: bold;
                        ">
                            Bekijk op {veilige_bronnaam}
                        </a>
                        """
                    )

            bronnen_tekst = ", ".join(
                bron_namen
            )
            
            ai_html = maak_ai_html(
                woning
            )
            # -------------------------------------------------
            # Complete woningkaart
            # -------------------------------------------------
            woningblokken.append(
                f"""
                <div style="
                    border: 1px solid #d8d8d8;
                    border-radius: 8px;
                    padding: 18px;
                    margin: 0 0 16px 0;
                    background-color: #ffffff;
                    overflow: hidden;
                ">

                    {foto_html}

                    <h3 style="
                        margin: 0 0 12px 0;
                    ">
                        {titel}
                    </h3>

                    <p style="
                        margin: 6px 0;
                    ">
                        <strong>Bron:</strong>
                        {bronnen_tekst}
                    </p>

                    <p style="
                        margin: 6px 0;
                    ">
                        <strong>Prijs:</strong>
                        {prijs}
                    </p>

                    <p style="
                        margin: 6px 0;
                    ">
                        <strong>Plaats:</strong>
                        {plaats}
                    </p>

                    <p style="
                        margin: 6px 0;
                    ">
                        <strong>Slaapkamers:</strong>
                        {slaapkamers_tekst}
                    </p>

                    <p style="
                        margin: 6px 0;
                    ">
                        <strong>Oppervlakte:</strong>
                        {oppervlakte_tekst}
                    </p>
                    
                    {perceel_html}

                    {ai_html}

                    <div style="
                        margin: 18px 0 0 0;
                    ">
                        {''.join(knoppen)}
                    </div>
                    
                </div>
                """
            )

        veilige_profielnaam = escape(
            profielnaam
        )

        profielblokken.append(
            f"""
            <div style="
                background-color: #ffffff;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 22px;
            ">
                <h2 style="
                    margin: 0 0 6px 0;
                ">
                    {veilige_profielnaam}
                </h2>

                <p style="
                    margin: 0 0 18px 0;
                    color: #555555;
                ">
                    {len(woningen)} nieuwe
                    woning{'en' if len(woningen) != 1 else ''}
                </p>

                {''.join(woningblokken)}
            </div>
            """
        )

    # ---------------------------------------------------------
    # Complete HTML-mail
    # ---------------------------------------------------------
    html_inhoud = f"""
    <html>
        <body style="
            margin: 0;
            padding: 24px;
            background-color: #f3f5f7;
            font-family: Arial, sans-serif;
            color: #222222;
        ">
            <div style="
                max-width: 720px;
                margin: 0 auto;
            ">
                <div style="
                    background-color: #ffffff;
                    border-radius: 10px;
                    padding: 22px;
                    margin-bottom: 22px;
                ">
                    <h1 style="
                        margin: 0 0 10px 0;
                    ">
                        Huizenzoeker
                    </h1>

                    <p style="
                        margin: 0;
                    ">
                        Er {'is' if totaal_aantal == 1 else 'zijn'}
                        <strong>{totaal_aantal}</strong>
                        nieuwe woning
                        {'gevonden' if totaal_aantal == 1 else 'en gevonden'}
                        in
                        <strong>{aantal_profielen}</strong>
                        zoekprofiel
                        {' ' if aantal_profielen == 1 else 'en'}.
                    </p>
                </div>

                {''.join(profielblokken)}

                <p style="
                    font-size: 12px;
                    color: #666666;
                    text-align: center;
                ">
                    Automatisch verzonden door Huizenzoeker
                    versie {APP_VERSION}.
                </p>
            </div>
        </body>
    </html>
    """

    bericht.add_alternative(
        html_inhoud,
        subtype="html",
    )

    # ---------------------------------------------------------
    # Verzenden
    # ---------------------------------------------------------
    try:
        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
            timeout=30,
        ) as smtp:
            smtp.login(
                EMAIL_ADDRESS,
                EMAIL_PASSWORD,
            )

            smtp.send_message(
                bericht
            )

        print(
            f"Gecombineerde HTML-e-mail verstuurd met "
            f"{totaal_aantal} unieke nieuwe woning(en)."
        )

    except smtplib.SMTPAuthenticationError:
        logger.exception(
            "Gmail heeft de aanmelding geweigerd"
        )

        print(
            "Gmail heeft de aanmelding geweigerd."
        )

    except Exception:
        logger.exception(
            "E-mail kon niet worden verstuurd"
        )

        raise
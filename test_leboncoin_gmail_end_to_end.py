import base64
from pathlib import Path

from bs4 import BeautifulSoup

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from leboncoin import haal_detail_op
from leboncoin_alerts import (
    parse_leboncoin_alert,
    combineer_alert_en_detail,
    dedupliceer_advertenties,
    filter_nieuwe_advertenties,
    markeer_als_verwerkt,
    markeer_als_onbeschikbaar,
    registreer_retry,
    verwijder_retry,
)

# ============================================================
# CONFIGURATIE
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

TOKEN_FILE = Path("token.json")
CREDENTIALS_FILE = Path("credentials.json")

MAX_ALERTMAILS = 50


# ============================================================
# GMAIL
# ============================================================

def gmail_service():
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES,
        )

    if not creds or not creds.valid:

        if (
            creds
            and creds.expired
            and creds.refresh_token
        ):
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES,
            )

            creds = flow.run_local_server(
                port=0
            )

        TOKEN_FILE.write_text(
            creds.to_json(),
            encoding="utf-8",
        )

    return build(
        "gmail",
        "v1",
        credentials=creds,
    )


# ============================================================
# GMAIL BODY DECODEN
# ============================================================

def decode_body(data):
    if not data:
        return ""

    decoded = base64.urlsafe_b64decode(
        data.encode("ASCII")
    )

    return decoded.decode(
        "utf-8",
        errors="replace",
    )


def haal_tekst_uit_payload(payload):
    plain_parts = []
    html_parts = []

    def verwerk_part(part):
        mime_type = part.get(
            "mimeType",
            "",
        )

        body = part.get(
            "body",
            {},
        )

        data = body.get(
            "data"
        )

        if data:
            tekst = decode_body(data)

            if mime_type == "text/plain":
                plain_parts.append(tekst)

            elif mime_type == "text/html":
                html_parts.append(tekst)

        for child in part.get(
            "parts",
            [],
        ):
            verwerk_part(child)

    verwerk_part(payload)

    if plain_parts:
        return "\n".join(plain_parts)

    if html_parts:
        return "\n".join(html_parts)

    return ""


# ============================================================
# HTML → PARSERTEKST
# ============================================================

def html_naar_parser_tekst(html):
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    for link in soup.find_all("a"):
        href = link.get("href")

        if not href:
            continue

        linktekst = link.get_text(
            " ",
            strip=True,
        )

        vervanging = (
            f"[{linktekst}]"
            f"({href})"
        )

        link.replace_with(vervanging)

    return soup.get_text(
        "\n",
        strip=True,
    )


# ============================================================
# LEBONCOIN MAILS OPHALEN
# ============================================================

def haal_leboncoin_mails(service):
    """
    Haalt maximaal MAX_ALERTMAILS recente
    Leboncoin-woningalerts op.
    """

    resultaat = (
        service.users()
        .messages()
        .list(
            userId="me",
            q=(
                "from:no.reply@leboncoin.fr "
                "subject:vendre "
                "-in:spam "
                "-in:trash"
            ),
            maxResults=MAX_ALERTMAILS,
        )
        .execute()
    )

    return resultaat.get(
        "messages",
        [],
    )


def haal_volledige_mail(service, message_id):
    return (
        service.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="full",
        )
        .execute()
    )


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 72)
    print("LEBONCOIN - GMAIL MULTI-ALERT END TO END TEST")
    print("=" * 72)

    if not CREDENTIALS_FILE.exists():
        print("\nFOUT: credentials.json niet gevonden.")
        return

    # --------------------------------------------------------
    # Gmail
    # --------------------------------------------------------

    print("\nGmail verbinden...")

    service = gmail_service()

    print("Gmail verbinding: OK")

    # --------------------------------------------------------
    # Alle recente alertmails zoeken
    # --------------------------------------------------------

    print(
        f"\nMaximaal {MAX_ALERTMAILS} "
        f"Leboncoin-alertmails ophalen..."
    )

    messages = haal_leboncoin_mails(
        service
    )

    print(
        f"Gevonden alertmails: "
        f"{len(messages)}"
    )

    if not messages:
        print("\nGeen Leboncoin-alertmails gevonden.")
        return

    # --------------------------------------------------------
    # Advertenties uit ALLE mails verzamelen
    # --------------------------------------------------------

    alle_advertenties = []

    for nummer, item in enumerate(
        messages,
        start=1,
    ):
        message_id = item["id"]

        bericht = haal_volledige_mail(
            service,
            message_id,
        )

        payload = bericht.get(
            "payload",
            {},
        )

        headers = {
            header["name"]: header["value"]
            for header in payload.get(
                "headers",
                [],
            )
        }

        subject = headers.get(
            "Subject"
        )

        print("\n" + "-" * 72)
        print(
            f"MAIL {nummer} VAN {len(messages)}"
        )
        print("-" * 72)

        print(
            f"Message ID : {message_id}"
        )

        print(
            f"Subject    : {subject}"
        )

        body = haal_tekst_uit_payload(
            payload
        )

        parser_body = body

        if (
            "<html" in body.lower()
            or "<a " in body.lower()
        ):
            parser_body = html_naar_parser_tekst(
                body
            )

        advertenties = parse_leboncoin_alert(
            parser_body
        )

        print(
            f"Advertenties gevonden: "
            f"{len(advertenties)}"
        )

        alle_advertenties.extend(
            advertenties
        )

    # --------------------------------------------------------
    # Over alle mails heen dedupliceren
    # --------------------------------------------------------

    print("\n" + "=" * 72)
    print("ADVERTENTIES VERZAMELD")
    print("=" * 72)

    print(
        f"Totaal vóór deduplicatie : "
        f"{len(alle_advertenties)}"
    )

    unieke_advertenties = (
        dedupliceer_advertenties(
            alle_advertenties
        )
    )

    print(
        f"Uniek na deduplicatie     : "
        f"{len(unieke_advertenties)}"
    )

    # --------------------------------------------------------
    # Historie toepassen
    # --------------------------------------------------------

    nieuwe_advertenties = (
        filter_nieuwe_advertenties(
            unieke_advertenties
        )
    )

    print(
        f"Nog niet verwerkt         : "
        f"{len(nieuwe_advertenties)}"
    )

    if not nieuwe_advertenties:
        print(
            "\nGeen nieuwe Leboncoin-advertenties "
            "om te verwerken."
        )

        print("\n" + "=" * 72)
        print("TEST AFGEROND")
        print("=" * 72)

        return

    # --------------------------------------------------------
    # Nieuwe advertenties verwerken
    # --------------------------------------------------------

    succesvol = []
    mislukt = []
    onbeschikbaar = []

    for nummer, alert in enumerate(
        nieuwe_advertenties,
        start=1,
    ):
        print("\n" + "=" * 72)
        print(
            f"NIEUWE ADVERTENTIE "
            f"{nummer} VAN {len(nieuwe_advertenties)}"
        )
        print("=" * 72)

        advertentie_id = alert.get(
            "advertentie_id"
        )

        print(
            f"Advertentie ID : "
            f"{advertentie_id}"
        )

        print(
            f"Alert URL      : "
            f"{alert.get('url')}"
        )

        try:
            # ------------------------------------------------
            # Detail ophalen
            # ------------------------------------------------

            print(
                "\nDetailpagina ophalen..."
            )

            detail = haal_detail_op(
                alert["url"]
            )

            print(
                "Detailpagina verwerkt: OK"
            )

            # ------------------------------------------------
            # Combineren
            # ------------------------------------------------

            woning = combineer_alert_en_detail(
                alert,
                detail,
            )

            # ------------------------------------------------
            # Resultaat tonen
            # ------------------------------------------------

            print(
                "\nGECOMBINEERD WONINGRECORD"
            )
            print("-" * 72)

            for key, value in woning.items():

                if key == "beschrijving":
                    continue

                print(
                    f"{key:22} : {value}"
                )

            # ------------------------------------------------
            # Alleen na succes historie bijwerken
            # ------------------------------------------------

            markeer_als_verwerkt(
                advertentie_id
            )

            verwijder_retry(
                advertentie_id
            )

            succesvol.append(
                advertentie_id
            )

            print(
                f"\nAdvertentie "
                f"{advertentie_id} "
                f"gemarkeerd als verwerkt."
            )

        except Exception as exc:
            fouttekst = str(exc)

            print(
                "\nFOUT tijdens verwerking:"
            )

            print(
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            # ------------------------------------------------
            # HTTP 410 = definitief verdwenen advertentie
            # ------------------------------------------------

            if (
                isinstance(exc, RuntimeError)
                and "HTTP status 410" in fouttekst
            ):
                markeer_als_onbeschikbaar(
                    advertentie_id
                )

                onbeschikbaar.append(
                    advertentie_id
                )

                print(
                    f"\nAdvertentie {advertentie_id} "
                    f"is definitief niet meer beschikbaar."
                )

                print(
                    "Advertentie gemarkeerd als "
                    "onbeschikbaar."
                )

                continue

            # ------------------------------------------------
            # Andere fouten zijn tijdelijk / onbekend.
            # Later opnieuw proberen.
            # ------------------------------------------------

            registreer_retry(
                advertentie_id,
                f"{type(exc).__name__}: {exc}",
            )

            mislukt.append(
                advertentie_id
            )
            print(
                "\nAdvertentie wordt NIET als verwerkt "
                "of onbeschikbaar gemarkeerd."
            )

            print(
                "Deze advertentie wordt bij een volgende "
                "run opnieuw geprobeerd."
            )

            continue

    # --------------------------------------------------------
    # Eindrapport
    # --------------------------------------------------------

    print("\n" + "=" * 72)
    print("EINDRAPPORT")
    print("=" * 72)

    print(
        f"Gmail-alertmails gelezen   : "
        f"{len(messages)}"
    )

    print(
        f"Advertenties aangetroffen  : "
        f"{len(alle_advertenties)}"
    )

    print(
        f"Unieke advertenties        : "
        f"{len(unieke_advertenties)}"
    )

    print(
        f"Nieuwe advertenties        : "
        f"{len(nieuwe_advertenties)}"
    )

    print(
        f"Succesvol verwerkt         : "
        f"{len(succesvol)}"
    )

    print(
        f"Onbeschikbaar (HTTP 410)   : "
        f"{len(onbeschikbaar)}"
    )

    print(
        f"Mislukt                    : "
        f"{len(mislukt)}"
    )

    if onbeschikbaar:
        print(
            "\nDefinitief onbeschikbare advertentie-ID's:"
        )

        for advertentie_id in onbeschikbaar:
            print(
                f"  - {advertentie_id}"
            )

    if mislukt:
        print(
            "\nMislukte advertentie-ID's:"
        )

        for advertentie_id in mislukt:
            print(
                f"  - {advertentie_id}"
            )

    print("\n" + "=" * 72)
    print("TEST AFGEROND")
    print("=" * 72)


if __name__ == "__main__":
    main()
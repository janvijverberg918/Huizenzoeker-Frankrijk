import base64
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from leboncoin_alerts import parse_leboncoin_alert


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

TOKEN_FILE = Path("token.json")
CREDENTIALS_FILE = Path("credentials.json")


def gmail_service():
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES,
        )

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES,
            )

            creds = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(
            creds.to_json(),
            encoding="utf-8",
        )

    return build(
        "gmail",
        "v1",
        credentials=creds,
    )


def decode_body(data):
    """
    Decodeert Gmail base64url-data naar tekst.
    """

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
    """
    Zoekt recursief naar text/plain.

    Als er geen text/plain beschikbaar is,
    gebruiken we text/html als fallback.
    """

    plain_parts = []
    html_parts = []

    def verwerk_part(part):
        mime_type = part.get("mimeType", "")

        body = part.get("body", {})
        data = body.get("data")

        if data:
            tekst = decode_body(data)

            if mime_type == "text/plain":
                plain_parts.append(tekst)

            elif mime_type == "text/html":
                html_parts.append(tekst)

        for child in part.get("parts", []):
            verwerk_part(child)

    verwerk_part(payload)

    if plain_parts:
        return "\n".join(plain_parts)

    if html_parts:
        return "\n".join(html_parts)

    return ""

from bs4 import BeautifulSoup


def html_naar_parser_tekst(html):
    """
    Zet HTML-mail om naar tekst waarbij links worden bewaard
    in dezelfde [tekst](url)-vorm die parse_leboncoin_alert()
    al begrijpt.
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    # Eerst alle links vervangen door Markdown-achtige links.
    for link in soup.find_all("a"):
        href = link.get("href")

        if not href:
            continue

        linktekst = link.get_text(
            " ",
            strip=True,
        )

        vervanging = f"[{linktekst}]({href})"

        link.replace_with(
            vervanging
        )

    return soup.get_text(
        "\n",
        strip=True,
    )

def main():
    print("=" * 72)
    print("GMAIL → LEBONCOIN ALERT PARSER TEST")
    print("=" * 72)

    service = gmail_service()

    # --------------------------------------------------------
    # Zoek de nieuwste echte Leboncoin-alert
    # --------------------------------------------------------

    resultaat = (
        service.users()
        .messages()
        .list(
            userId="me",
            q=(
                "from:no.reply@leboncoin.fr "
                "-in:spam "
                "-in:trash"
            ),
            maxResults=1,
        )
        .execute()
    )

    messages = resultaat.get(
        "messages",
        [],
    )

    if not messages:
        print("\nGeen Leboncoin-alertmails gevonden.")
        return

    message_id = messages[0]["id"]

    print(f"\nGmail message ID: {message_id}")

    # --------------------------------------------------------
    # Volledige mail ophalen
    # --------------------------------------------------------

    bericht = (
        service.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="full",
        )
        .execute()
    )

    headers = {
        header["name"]: header["value"]
        for header in bericht
        .get("payload", {})
        .get("headers", [])
    }

    print(f"From    : {headers.get('From')}")
    print(f"Subject : {headers.get('Subject')}")

    # --------------------------------------------------------
    # Body uit Gmail halen
    # --------------------------------------------------------

    body = haal_tekst_uit_payload(
        bericht.get("payload", {})
    )

    print(f"\nBody grootte: {len(body):,} tekens")
    print(
        "Bevat Leboncoin /vi/:",
        "/vi/" in body,
    )

    # --------------------------------------------------------
    # Onze bestaande parser gebruiken
    # --------------------------------------------------------
   
    parser_body = body

    if "<html" in body.lower() or "<a " in body.lower():
        parser_body = html_naar_parser_tekst(body)

    print(
        "Parser body bevat /vi/:",
        "/vi/" in parser_body,
    )

    advertenties = parse_leboncoin_alert(
        parser_body
    )

    print(
        f"\nAantal advertenties gevonden: "
        f"{len(advertenties)}"
    )

    for nummer, advertentie in enumerate(
        advertenties,
        start=1,
    ):
        print("\n" + "-" * 72)
        print(f"Advertentie {nummer}")
        print("-" * 72)

        for key, value in advertentie.items():
            print(f"{key:22} : {value}")

    print("\n" + "=" * 72)
    print("TEST AFGEROND")
    print("=" * 72)


if __name__ == "__main__":
    main()
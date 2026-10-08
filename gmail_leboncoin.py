import base64
from pathlib import Path

from bs4 import BeautifulSoup

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# ============================================================
# CONFIGURATIE
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

TOKEN_FILE = Path("token.json")
CREDENTIALS_FILE = Path("credentials.json")


# ============================================================
# GMAIL VERBINDING
# ============================================================

def gmail_service():
    """
    Maakt verbinding met Gmail via OAuth.

    Gebruikt token.json indien aanwezig.
    Indien nodig wordt opnieuw geautoriseerd via
    credentials.json.
    """

    credentials = None

    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES,
        )

    if not credentials or not credentials.valid:

        if (
            credentials
            and credentials.expired
            and credentials.refresh_token
        ):
            try:
                credentials.refresh(
                    Request()
                )

            except Exception:
                credentials = None

        if credentials is None:

            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    "credentials.json niet gevonden."
                )

            flow = (
                InstalledAppFlow
                .from_client_secrets_file(
                    CREDENTIALS_FILE,
                    SCOPES,
                )
            )

            credentials = (
                flow.run_local_server(
                    port=0
                )
            )

        TOKEN_FILE.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )

    return build(
        "gmail",
        "v1",
        credentials=credentials,
    )


# ============================================================
# LEBONCOIN ALERTMAILS ZOEKEN
# ============================================================

def zoek_leboncoin_alerts(
    service,
    max_resultaten=50,
    max_results=None,
):
    """
    Zoekt Leboncoin-alertmails in Gmail.

    Ondersteunt zowel max_resultaten als de oudere
    parameternaam max_results.
    """

    if max_results is not None:
        max_resultaten = max_results

    query = (
        'from:(no.reply@leboncoin.fr) '
        'subject:("bien")'
    )

    resultaat = (
        service.users()
        .messages()
        .list(
            userId="me",
            q=query,
            maxResults=max_resultaten,
        )
        .execute()
    )

    return resultaat.get(
        "messages",
        []
    )
    """
    Zoekt Leboncoin-alertmails in Gmail.

    Retourneert de Gmail message-records.
    """

    query = (
        'from:(no.reply@leboncoin.fr) '
        'subject:("bien")'
    )

    resultaat = (
        service.users()
        .messages()
        .list(
            userId="me",
            q=query,
            maxResults=max_resultaten,
        )
        .execute()
    )

    return resultaat.get(
        "messages",
        []
    )


# ============================================================
# ÉÉN GMAIL-BERICHT OPHALEN
# ============================================================

def haal_email_op(
    service,
    message_id,
):
    """
    Haalt één volledig Gmail-bericht op en voegt enkele
    handige headerwaarden toe aan het resultaat.
    """

    message = (
        service.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="full",
        )
        .execute()
    )

    headers = (
        message
        .get("payload", {})
        .get("headers", [])
    )

    header_dict = {
        header.get("name", "").lower():
            header.get("value", "")
        for header in headers
    }

    message["from"] = header_dict.get(
        "from",
        ""
    )

    message["subject"] = header_dict.get(
        "subject",
        ""
    )

    message["date"] = header_dict.get(
        "date",
        ""
    )

    return message


# ============================================================
# MIME PARTS
# ============================================================

def _decode_body_data(data):
    """
    Decodeert Gmail base64url-data naar UTF-8 tekst.
    """

    if not data:
        return ""

    padding = "=" * (
        -len(data) % 4
    )

    decoded = base64.urlsafe_b64decode(
        data + padding
    )

    return decoded.decode(
        "utf-8",
        errors="replace",
    )


def _verzamel_parts(
    payload,
    mime_type,
):
    """
    Zoekt recursief alle MIME-parts van het opgegeven type.
    """

    resultaten = []

    if not payload:
        return resultaten

    if payload.get("mimeType") == mime_type:

        data = (
            payload
            .get("body", {})
            .get("data")
        )

        if data:
            resultaten.append(
                _decode_body_data(
                    data
                )
            )

    for part in payload.get(
        "parts",
        []
    ):
        resultaten.extend(
            _verzamel_parts(
                part,
                mime_type,
            )
        )

    return resultaten


# ============================================================
# HTML → PARSERTEKST
# ============================================================

def _html_naar_parsertekst(html):
    """
    Zet de HTML van een Leboncoin-mail om naar tekst waarbij
    links behouden blijven in Markdown-vorm:

        [zichtbare tekst](URL)

    Ook afbeeldingen worden als Markdown-afbeelding opgenomen:

        ![alt](image-URL)

    Hierdoor kan leboncoin_alerts.py zowel advertentielinks
    als afbeeldingen uit de Gmail-body halen.
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    # --------------------------------------------------------
    # Afbeeldingen behouden
    # --------------------------------------------------------

    for img in soup.find_all("img"):

        src = img.get("src")

        if not src:
            continue

        alt = img.get(
            "alt",
            ""
        )

        vervanging = (
            f"\n![{alt}]({src})\n"
        )

        img.replace_with(
            vervanging
        )

    # --------------------------------------------------------
    # Links behouden
    # --------------------------------------------------------

    for link in soup.find_all(
        "a",
        href=True,
    ):

        href = link.get("href")

        zichtbare_tekst = (
            link.get_text(
                " ",
                strip=True,
            )
        )

        if zichtbare_tekst:
            vervanging = (
                f"[{zichtbare_tekst}]"
                f"({href})"
            )
        else:
            vervanging = (
                f"[link]({href})"
            )

        link.replace_with(
            vervanging
        )

    return soup.get_text(
        "\n",
        strip=True,
    )


# ============================================================
# BODY OPHALEN
# ============================================================

def haal_email_body_op(email):
    """
    Haalt de bruikbare body uit een Gmail-bericht.

    HTML heeft voorkeur omdat daarin de advertentielinks en
    afbeeldingen beschikbaar zijn.

    Als HTML ontbreekt, wordt text/plain gebruikt.
    """

    payload = email.get(
        "payload",
        {}
    )

    html_parts = _verzamel_parts(
        payload,
        "text/html",
    )

    if html_parts:

        html = "\n".join(
            html_parts
        )

        return _html_naar_parsertekst(
            html
        )

    tekst_parts = _verzamel_parts(
        payload,
        "text/plain",
    )

    if tekst_parts:
        return "\n".join(
            tekst_parts
        )

    # Soms zit de body rechtstreeks in de hoofd-payload.
    data = (
        payload
        .get("body", {})
        .get("data")
    )

    if data:
        return _decode_body_data(
            data
        )

    return ""
# ============================================================
# COMPATIBILITEIT MET BESTAANDE LEBONCOIN RUNNER
# ============================================================

haal_mail_op = haal_email_op
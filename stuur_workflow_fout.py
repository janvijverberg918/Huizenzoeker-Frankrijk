import os
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def main():

    email_provider = os.getenv(
        "EMAIL_PROVIDER",
        "",
    ).lower()

    email_address = os.getenv(
        "EMAIL_ADDRESS"
    )

    email_password = os.getenv(
        "EMAIL_PASSWORD"
    )

    email_to = os.getenv(
        "EMAIL_TO"
    )

    foutmelding = os.getenv(
        "WORKFLOW_ERROR",
        "Onbekende fout.",
    )

    if not all(
        [
            email_address,
            email_password,
            email_to,
        ]
    ):
        raise RuntimeError(
            "E-mailconfiguratie ontbreekt."
        )

    if email_provider == "gmail":
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

    elif email_provider == "outlook":
        smtp_server = "smtp.office365.com"
        smtp_port = 587

    else:
        raise RuntimeError(
            f"Onbekende EMAIL_PROVIDER: "
            f"{email_provider}"
        )

    onderwerp = (
        "[Huizenzoeker Frankrijk - FOUT] "
        "Leboncoin workflow mislukt"
    )

    tekst = f"""
De automatische Leboncoin-run is mislukt.

Onderdeel:
Gmail / Leboncoin workflow

Fout:
{foutmelding}

Er zijn geen nieuwe Leboncoin-advertenties als verwerkt
gemarkeerd als de run vóór verwerking is gestopt.

Controleer de mislukte GitHub Actions-run.

Huizenzoeker Frankrijk
"""

    bericht = MIMEMultipart()

    bericht["From"] = email_address
    bericht["To"] = email_to
    bericht["Subject"] = onderwerp

    bericht.attach(
        MIMEText(
            tekst,
            "plain",
            "utf-8",
        )
    )

    with smtplib.SMTP(
        smtp_server,
        smtp_port,
    ) as server:

        server.starttls()

        server.login(
            email_address,
            email_password,
        )

        server.send_message(
            bericht
        )

    print(
        "Foutmelding per e-mail verstuurd."
    )


if __name__ == "__main__":
    main()
from gmail_leboncoin import (
    gmail_service,
    zoek_leboncoin_alerts,
    haal_email_op,
    haal_email_body_op,
)

from leboncoin_alerts import (
    parse_leboncoin_alert,
)


def main():

    print("=" * 72)
    print("GMAIL → LEBONCOIN FOTO TEST")
    print("=" * 72)

    # --------------------------------------------------------
    # Gmail verbinden
    # --------------------------------------------------------

    print()
    print("Gmail verbinden...")

    service = gmail_service()

    print("Gmail verbinding: OK")

    # --------------------------------------------------------
    # Leboncoin-mails zoeken
    # --------------------------------------------------------

    print()
    print("Leboncoin-alertmails zoeken...")

    mails = zoek_leboncoin_alerts(
        service,
        max_resultaten=10,
    )

    print(
        f"Aantal gevonden mails: {len(mails)}"
    )

    if not mails:
        print(
            "Geen Leboncoin-alertmails gevonden."
        )
        return

    # --------------------------------------------------------
    # Alleen nieuwste mail testen
    # --------------------------------------------------------

    nieuwste = mails[0]

    message_id = nieuwste["id"]

    print()
    print(
        f"Nieuwste Gmail message ID: "
        f"{message_id}"
    )

    email = haal_email_op(
        service,
        message_id,
    )

    subject = email.get(
        "subject",
        ""
    )

    print(
        f"Subject: {subject}"
    )

    # --------------------------------------------------------
    # Body ophalen
    # --------------------------------------------------------

    body = haal_email_body_op(
        email
    )
    with open(
        "leboncoin_email_body_debug.txt",
        "w",
        encoding="utf-8",
    ) as bestand:
        bestand.write(body)

    print()
    print(
        "Debug body opgeslagen als: "
        "leboncoin_email_body_debug.txt"
    )
    print()
    print("=" * 72)
    print("AFBEELDINGSREGELS IN BODY")
    print("=" * 72)

    for regel in body.splitlines():
        regel_lower = regel.lower()

        if (
            "img.leboncoin" in regel_lower
            or "image" in regel_lower
            or "![" in regel
        ):
            print(regel)
    print(
        f"Body grootte: {len(body):,} tekens"
    )

    # --------------------------------------------------------
    # Parser
    # --------------------------------------------------------

    advertenties = parse_leboncoin_alert(
        body
    )

    print()
    print("=" * 72)
    print("GEVONDEN ADVERTENTIES")
    print("=" * 72)

    print(
        f"Aantal advertenties: "
        f"{len(advertenties)}"
    )

    for nummer, advertentie in enumerate(
        advertenties,
        start=1,
    ):

        print()
        print("-" * 72)
        print(
            f"Advertentie {nummer}"
        )
        print("-" * 72)

        print(
            f"advertentie_id         : "
            f"{advertentie.get('advertentie_id')}"
        )

        print(
            f"prijs                  : "
            f"{advertentie.get('prijs')}"
        )

        print(
            f"woonoppervlakte        : "
            f"{advertentie.get('woonoppervlakte')}"
        )

        print(
            f"perceeloppervlakte     : "
            f"{advertentie.get('perceeloppervlakte')}"
        )

        print(
            f"plaats                 : "
            f"{advertentie.get('plaats')}"
        )

        print(
            f"postcode               : "
            f"{advertentie.get('postcode')}"
        )

        print(
            f"foto_url               : "
            f"{advertentie.get('foto_url')}"
        )

        print(
            f"url                    : "
            f"{advertentie.get('url')}"
        )

    print()
    print("=" * 72)
    print("FOTO TEST AFGEROND")
    print("=" * 72)


if __name__ == "__main__":
    main()
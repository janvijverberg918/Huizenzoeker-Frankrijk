from emailer import stuur_nieuwe_woningen


def main():

    test_woning = {
        "titel": "TEST - Huizenzoeker Frankrijk GitHub",
        "prijs": "€ 150.000",
        "plaats": "Givet",
        "postcode": "08600",
        "link": "https://www.bienici.com/",
        "foto": "",
        "bron": "Bien'ici",
        "bron_sleutel": "bienici",

        # Nodig voor groepering in de e-mail.
        "zoekprofiel": "Frankrijk",

        # Testwaarden AI Huizencoach.
        "ai_score": 8,
        "ai_advies": "TEST - e-mailverbinding werkt",
        "ai_betrouwbaarheid": "Hoog",
        "ai_samenvatting": (
            "Dit is geen echte woning. "
            "Dit bericht test uitsluitend de e-mailverbinding "
            "van Huizenzoeker Frankrijk via GitHub Actions."
        ),
        "ai_sterke_punten": [
            "Test van GitHub Actions",
            "Test van Gmail SMTP",
        ],
        "ai_aandachtspunten": [
            "Dit is geen echte woningadvertentie.",
        ],
        "ai_ontbrekende_informatie": [],
    }

    nieuwe_woningen = [
        test_woning
    ]

    print("=" * 60)
    print("GITHUB E-MAILTEST")
    print("=" * 60)

    stuur_nieuwe_woningen(
        nieuwe_woningen
    )

    print()
    print("E-mailtest succesvol afgerond.")


if __name__ == "__main__":
    main()
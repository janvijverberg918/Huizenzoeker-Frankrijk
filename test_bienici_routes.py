from bienici import haal_html_op

TEST_URLS = [
    "https://www.bienici.com/recherche/achat/08320/maisonvilla",
    "https://www.bienici.com/recherche/achat/02830/maisonvilla",
    "https://www.bienici.com/recherche/achat/55700/maisonvilla",
]

for url in TEST_URLS:
    print("=" * 72)
    print(url)

    try:
        html = haal_html_op(
            url,
            wacht_op_resultaten=True,
        )

        print(
            f"HTML ontvangen: {len(html)} tekens"
        )

    except Exception as fout:
        print(
            f"FOUT: {fout}"
        )
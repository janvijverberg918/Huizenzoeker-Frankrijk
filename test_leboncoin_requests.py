import requests


URL = (
    "https://www.leboncoin.fr/cl/"
    "ventes_immobilieres/"
    "cp_givet_08600/"
    "real_estate_type%3A1"
)


def main():

    print("=" * 72)
    print("LEBONCOIN REQUESTS TEST")
    print("=" * 72)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/142.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "fr-FR,fr;q=0.9",
    }

    response = requests.get(
        URL,
        headers=headers,
        timeout=30,
    )

    print()
    print(
        f"HTTP-status : {response.status_code}"
    )

    print(
        f"HTML lengte : {len(response.text):,}"
    )

    print(
        f"Eind-URL    : {response.url}"
    )

    print()
    print(
        response.text[:1000]
    )


if __name__ == "__main__":
    main()
from leboncoin import haal_detail_op


DETAIL_URL = (
    "https://www.leboncoin.fr/vi/3268053815.htm"
    "#at_medium=email"
    "&at_emailtype=retention"
    "&at_campaign=fr_lbc_immo_searchp_emllbc_part_click-ad-saved-search-other__alert"
)


def main():
    print("=" * 72)
    print("LEBONCOIN - MODULE TEST")
    print("=" * 72)

    try:
        woning = haal_detail_op(
            DETAIL_URL
        )

    except Exception as exc:
        print("\nFOUT:")
        print(exc)
        return

    print("\nWONINGRECORD")
    print("-" * 72)

    for key, value in woning.items():

        if key == "beschrijving":
            continue

        print(
            f"{key:22} : {value}"
        )

    print("\n" + "=" * 72)
    print("MODULE TEST AFGEROND")
    print("=" * 72)


if __name__ == "__main__":
    main()
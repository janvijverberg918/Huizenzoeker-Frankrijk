from immovlan import zoek_immovlan


def main():
    print("=" * 60)
    print("TEST IMMOVLAN - SAINTE-ODE 6680")
    print("=" * 60)

    try:
        resultaten = zoek_immovlan(
            postcode="6680",
            woningtype="huis",
            min_prijs=100000,
            max_prijs=250000,
            csv_bestand="woningen_sainte_ode_immovlan.csv",
        )

        print()
        print("=" * 60)
        print("RESULTAAT")
        print("=" * 60)
        print("IMMOVLAN SAINTE-ODE : OK")
        print(
            f"Nieuwe woningen     : {len(resultaten)}"
        )
        print("=" * 60)

    except Exception as fout:
        print()
        print("=" * 60)
        print("RESULTAAT")
        print("=" * 60)
        print("IMMOVLAN SAINTE-ODE : MISLUKT")
        print(f"Fout: {fout}")
        print("=" * 60)


if __name__ == "__main__":
    main()
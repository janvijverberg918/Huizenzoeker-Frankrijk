from immovlan import zoek_immovlan


zoek_immovlan(
    postcode="6980",
    woningtype="huis",
    min_prijs=100000,
    max_prijs=250000,
    csv_bestand="woningen_immovlan_test.csv",
)
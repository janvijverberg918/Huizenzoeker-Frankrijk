from zimmo import zoek_zimmo


zoek_zimmo(
    postcode="6980",
    woningtype="huis",
    min_prijs=100000,
    max_prijs=250000,
    csv_bestand="woningen_zimmo_test.csv",
)
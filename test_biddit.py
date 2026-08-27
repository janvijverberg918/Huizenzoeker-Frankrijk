from biddit import zoek_biddit

zoek_biddit(
    postcode="6987",
    woningtype="huis",
    min_prijs=0,
    max_prijs=1000000,
    csv_bestand="woningen_biddit_test.csv",
)
import glob
import os
import re

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Huizenzoeker Dashboard",
    page_icon="🏠",
    layout="wide",
)


# ---------------------------------------------------------
# Hulpfuncties
# ---------------------------------------------------------

def prijs_naar_getal(waarde):
    """
    Zet een prijs om naar een geheel getal.

    Voorbeelden:
    '€ 225.000' -> 225000
    '225 000 €' -> 225000
    """

    if pd.isna(waarde):
        return None

    tekst = str(waarde).strip()

    # Alleen het eerste prijsachtige bedrag pakken.
    match = re.search(
        r"(\d[\d\.\s]*)",
        tekst,
    )

    if not match:
        return None

    cijfers = re.findall(
        r"\d+",
        match.group(1),
    )

    if not cijfers:
        return None

    try:
        return int(
            "".join(cijfers)
        )
    except ValueError:
        return None


def normaliseer_tekst(waarde):
    """
    Maakt NaN/None netjes leeg.
    """

    if pd.isna(waarde):
        return ""

    return str(waarde).strip()


def maak_weergave_prijs(waarde):
    """
    Maakt van een numerieke prijs een nette euro-weergave.
    """

    if pd.isna(waarde):
        return ""

    try:
        return (
            f"€ {int(waarde):,}"
            .replace(",", ".")
        )
    except Exception:
        return ""


def haal_zoekgebied_uit_bestandsnaam(bestand):
    """
    Haalt globaal het zoekgebied uit een CSV-bestandsnaam.

    Voorbeeld:
    woningen_la_roche_immoweb.csv
    -> la_roche
    """

    naam = os.path.basename(
        bestand
    )

    naam = naam.removeprefix(
        "woningen_"
    )

    naam = naam.removesuffix(
        ".csv"
    )

    bekende_bronnen = [
        "immoweb",
        "immovlan",
        "ardenneimmo",
        "biddit",
    ]

    for bron in bekende_bronnen:
        suffix = f"_{bron}"

        if naam.endswith(suffix):
            return naam[
                :-len(suffix)
            ]

    return naam


@st.cache_data
def laad_woningen():
    """
    Leest alle productie-CSV-bestanden uit de projectmap.
    """

    bestanden = glob.glob(
        "woningen_*.csv"
    )

    alle_woningen = []

    for bestand in bestanden:

        # Testbestanden niet meenemen
        if "_test" in bestand.lower():
            continue

        try:
            df = pd.read_csv(
                bestand,
                encoding="utf-8-sig",
            )

        except Exception:
            continue

        if df.empty:
            continue

        # -------------------------------------------------
        # Ontbrekende kolommen aanvullen
        # -------------------------------------------------
        verwachte_kolommen = [
            "titel",
            "prijs",
            "slaapkamers",
            "oppervlakte",
            "perceeloppervlakte",
            "plaats",
            "link",
            "bron",
        ]

        for kolom in verwachte_kolommen:
            if kolom not in df.columns:
                df[kolom] = ""

        df["csv_bestand"] = os.path.basename(
            bestand
        )

        df["zoekgebied"] = (
            haal_zoekgebied_uit_bestandsnaam(
                bestand
            )
        )

        alle_woningen.append(
            df
        )

    if not alle_woningen:
        return pd.DataFrame()

    df = pd.concat(
        alle_woningen,
        ignore_index=True,
    )

    # -----------------------------------------------------
    # Opschonen
    # -----------------------------------------------------
    tekstkolommen = [
        "titel",
        "prijs",
        "slaapkamers",
        "oppervlakte",
        "perceeloppervlakte",
        "plaats",
        "link",
        "bron",
        "zoekgebied",
    ]

    for kolom in tekstkolommen:
        df[kolom] = df[kolom].apply(
            normaliseer_tekst
        )

    df["prijs_getal"] = df["prijs"].apply(
        prijs_naar_getal
    )

    return df


# ---------------------------------------------------------
# Data laden
# ---------------------------------------------------------

df = laad_woningen()


# ---------------------------------------------------------
# Titel
# ---------------------------------------------------------

st.title(
    "🏠 Huizenzoeker Dashboard"
)

st.caption(
    "Actueel overzicht van woningen en andere objecten "
    "uit Immoweb, Immovlan, Ardenne Immo en Biddit."
)


if df.empty:
    st.warning(
        "Geen woninggegevens gevonden."
    )
    st.stop()


# ---------------------------------------------------------
# Statistieken
# ---------------------------------------------------------

totaal = len(df)

aantal_bronnen = (
    df["bron"]
    .replace("", pd.NA)
    .dropna()
    .nunique()
)

aantal_plaatsen = (
    df["plaats"]
    .replace("", pd.NA)
    .dropna()
    .nunique()
)

geldige_prijzen = (
    df["prijs_getal"]
    .dropna()
)

gemiddelde_prijs = (
    geldige_prijzen.mean()
    if not geldige_prijzen.empty
    else None
)


kolom1, kolom2, kolom3, kolom4 = st.columns(
    4
)

kolom1.metric(
    "Advertenties",
    totaal,
)

kolom2.metric(
    "Websites",
    aantal_bronnen,
)

kolom3.metric(
    "Plaatsen",
    aantal_plaatsen,
)

if gemiddelde_prijs is not None:
    kolom4.metric(
        "Gemiddelde prijs",
        maak_weergave_prijs(
            gemiddelde_prijs
        ),
    )
else:
    kolom4.metric(
        "Gemiddelde prijs",
        "-",
    )


st.divider()


# ---------------------------------------------------------
# Filters
# ---------------------------------------------------------

st.subheader(
    "Filters"
)

filter1, filter2, filter3, filter4 = st.columns(
    4
)


with filter1:
    beschikbare_bronnen = sorted(
        [
            bron
            for bron in df["bron"].unique()
            if bron
        ]
    )

    geselecteerde_bronnen = st.multiselect(
        "Website",
        beschikbare_bronnen,
        default=beschikbare_bronnen,
    )


with filter2:
    beschikbare_gebieden = sorted(
        [
            gebied
            for gebied in df["zoekgebied"].unique()
            if gebied
        ]
    )

    geselecteerde_gebieden = st.multiselect(
        "Zoekgebied",
        beschikbare_gebieden,
        default=beschikbare_gebieden,
    )


with filter3:
    zoektekst = st.text_input(
        "Zoek op plaats of omschrijving",
        placeholder="Bijvoorbeeld Rendeux, chalet, garage...",
    )


with filter4:
    max_prijs_data = (
        int(
            geldige_prijzen.max()
        )
        if not geldige_prijzen.empty
        else 300000
    )

    slider_max = max(
        max_prijs_data,
        300000,
    )

    prijs_range = st.slider(
        "Prijs",
        min_value=0,
        max_value=slider_max,
        value=(
            0,
            min(
                250000,
                slider_max,
            ),
        ),
        step=5000,
    )


# ---------------------------------------------------------
# Filters toepassen
# ---------------------------------------------------------

gefilterd = df.copy()


if geselecteerde_bronnen:
    gefilterd = gefilterd[
        gefilterd["bron"].isin(
            geselecteerde_bronnen
        )
    ]


if geselecteerde_gebieden:
    gefilterd = gefilterd[
        gefilterd["zoekgebied"].isin(
            geselecteerde_gebieden
        )
    ]


gefilterd = gefilterd[
    gefilterd["prijs_getal"].isna()
    |
    (
        (
            gefilterd["prijs_getal"]
            >= prijs_range[0]
        )
        &
        (
            gefilterd["prijs_getal"]
            <= prijs_range[1]
        )
    )
]


if zoektekst:
    zoektekst_lower = (
        zoektekst.lower()
    )

    masker = (
        gefilterd["plaats"]
        .str.lower()
        .str.contains(
            zoektekst_lower,
            regex=False,
        )
        |
        gefilterd["titel"]
        .str.lower()
        .str.contains(
            zoektekst_lower,
            regex=False,
        )
        |
        gefilterd["bron"]
        .str.lower()
        .str.contains(
            zoektekst_lower,
            regex=False,
        )
    )

    gefilterd = gefilterd[
        masker
    ]


# ---------------------------------------------------------
# Sortering
# ---------------------------------------------------------

st.divider()

sort1, sort2 = st.columns(
    2
)

with sort1:
    sorteer_op = st.selectbox(
        "Sorteer op",
        [
            "Prijs laag → hoog",
            "Prijs hoog → laag",
            "Plaats A → Z",
            "Website A → Z",
        ],
    )

with sort2:
    st.metric(
        "Resultaten na filters",
        len(gefilterd),
    )


if sorteer_op == "Prijs laag → hoog":
    gefilterd = gefilterd.sort_values(
        by="prijs_getal",
        ascending=True,
        na_position="last",
    )

elif sorteer_op == "Prijs hoog → laag":
    gefilterd = gefilterd.sort_values(
        by="prijs_getal",
        ascending=False,
        na_position="last",
    )

elif sorteer_op == "Plaats A → Z":
    gefilterd = gefilterd.sort_values(
        by="plaats",
        ascending=True,
    )

elif sorteer_op == "Website A → Z":
    gefilterd = gefilterd.sort_values(
        by="bron",
        ascending=True,
    )


# ---------------------------------------------------------
# Tabel voorbereiden
# ---------------------------------------------------------

tabel = gefilterd.copy()


tabel["Prijs"] = tabel[
    "prijs_getal"
].apply(
    maak_weergave_prijs
)

tabel["Plaats"] = tabel[
    "plaats"
]

tabel["Website"] = tabel[
    "bron"
]

tabel["Slaapkamers"] = tabel[
    "slaapkamers"
]

tabel["Woonopp."] = tabel[
    "oppervlakte"
]

tabel["Perceel"] = tabel[
    "perceeloppervlakte"
]

tabel["Titel"] = tabel[
    "titel"
]

tabel["Advertentie"] = tabel[
    "link"
]

tabel["Zoekgebied"] = tabel[
    "zoekgebied"
]


zichtbare_kolommen = [
    "Prijs",
    "Plaats",
    "Website",
    "Slaapkamers",
    "Woonopp.",
    "Perceel",
    "Titel",
    "Zoekgebied",
    "Advertentie",
]

tabel = tabel[
    zichtbare_kolommen
]


# ---------------------------------------------------------
# Resultaten
# ---------------------------------------------------------

st.subheader(
    "Woningen"
)

st.dataframe(
    tabel,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Prijs": st.column_config.TextColumn(
            "Prijs",
            width="small",
        ),
        "Plaats": st.column_config.TextColumn(
            "Plaats",
            width="medium",
        ),
        "Website": st.column_config.TextColumn(
            "Website",
            width="small",
        ),
        "Slaapkamers": st.column_config.TextColumn(
            "Slaapkamers",
            width="small",
        ),
        "Woonopp.": st.column_config.TextColumn(
            "Woonopp. m²",
            width="small",
        ),
        "Perceel": st.column_config.TextColumn(
            "Perceel m²",
            width="small",
        ),
        "Titel": st.column_config.TextColumn(
            "Omschrijving",
            width="large",
        ),
        "Zoekgebied": st.column_config.TextColumn(
            "Zoekgebied",
            width="medium",
        ),
        "Advertentie": st.column_config.LinkColumn(
            "Advertentie",
            display_text="Open",
            width="small",
        ),
    },
)


# ---------------------------------------------------------
# Aantallen per website
# ---------------------------------------------------------

st.divider()

st.subheader(
    "Aanbod per website"
)

per_bron = (
    gefilterd["bron"]
    .value_counts()
    .rename_axis("Website")
    .reset_index(
        name="Aantal"
    )
)

st.dataframe(
    per_bron,
    use_container_width=False,
    hide_index=True,
)


st.caption(
    "De data wordt rechtstreeks gelezen uit de "
    "CSV-bestanden van Huizenzoeker."
)
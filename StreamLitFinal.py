# Dashboard for visualizing gaming data
import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt

# Page Configuration
st.set_page_config(layout="wide")
st.title("Gaming Dashboard")

# Data Loading Function
@st.cache_data
def load_data(path):
    df=pd.read_csv(path)
    df.columns=df.columns.str.strip().str.lower()
    df["date"]=pd.to_datetime(df["date"], errors="coerce")
    return df

# Loading Data
master_df=load_data("data/largefiles/test_data.csv")
map_df_raw=load_data("data/largefiles/test_data.csv")
#map_df_raw=load_data("data/raw/World_Map_Data.csv")

# Sidebar Filters
st.sidebar.title("Filters")
min_date=master_df["date"].min().to_pydatetime()
max_date=master_df["date"].max().to_pydatetime()

selected_date=st.sidebar.slider(
    "Select Month Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date,max_date),
    format="MMM YYYY",
    key="date_slider",
)

# World Map Filters
st.sidebar.header("World Map Filters")
platforms_map=["All"]+sorted(map_df_raw["platform"].dropna().unique())
selected_platforms_map=st.sidebar.multiselect("Platform", platforms_map, default=["All"], key="map_platforms")
genres_map=["All"]+sorted(map_df_raw["genres"].dropna().unique())
selected_genres_map=st.sidebar.multiselect("Genres", genres_map, default=["All"], key="map_genres")
games_map=["All"]+sorted(map_df_raw["title"].dropna().unique())
selected_games_map=st.sidebar.multiselect("Game", games_map, default=["All"], key="map_games")

# Bar Plot Filters
st.sidebar.header("Bar Plot Filters")
countries_bar=["All"]+sorted(master_df["country"].dropna().unique())
selected_bar_country=st.sidebar.multiselect("Country", countries_bar, key="bar_country")
platforms_bar=["All"]+sorted(master_df["platform"].dropna().unique())
selected_platforms_bar=st.sidebar.multiselect("Platform", platforms_bar, default=["All"], key="bar_platforms")
genres_bar=["All"]+sorted(master_df["genres"].dropna().unique())
selected_genres_bar=st.sidebar.multiselect("Genres", genres_bar, default=["All"], key="bar_genres")

# Data Table Filters
st.sidebar.header("Data Table Filters")
countries_table=["All"]+sorted(master_df["country"].dropna().unique())
selected_table_countries=st.sidebar.multiselect("Country", countries_table, default=["All"], key="table_countries")
games_table=["All"]+sorted(master_df["title"].unique())
selected_table_games=st.sidebar.multiselect("Game", games_table, default=["All"], key="table_games")
platforms_table=["All"]+sorted(master_df["platform"].dropna().unique())
selected_table_platforms=st.sidebar.multiselect("Platform", platforms_table, default=["All"], key="table_platforms")
genres_table=["All"]+sorted(master_df["genres"].dropna().unique())
selected_table_genres=st.sidebar.multiselect("Genres", genres_table, default=["All"], key="table_genres")

# World Map Processing
st.header("World Map")

country_game_counts_filtered = (
    map_df_raw.groupby(["country", "title"])
    .agg(total_players=("playerid", "nunique"))
    .reset_index()
)

top20_filtered = (
    country_game_counts_filtered.sort_values(
        ["country", "total_players"], ascending=[True, False]
    )
    .groupby("country")
    .head(20)[["country", "title"]]
)

filtered_df = map_df_raw.merge(top20_filtered, on=["country", "title"], how="inner")

system_counts = (
    filtered_df.groupby(["country", "platform"])
    .agg(count=("playerid", "nunique"))
    .reset_index()
)

steam_df = system_counts[system_counts["platform"] == "steam"]
ps_df = system_counts[system_counts["platform"] == "ps"]

col1, col2 = st.columns(2)

# Steam Map
with col1:
    st.subheader("Steam Distribution")
    if steam_df.empty:
        st.info("No Steam data for the selected filters.")
    else:
        fig_steam = px.choropleth(
            steam_df,
            locations="country",
            locationmode="country names",
            color="count",
            color_continuous_scale=["#FFE5D9", "#FF8C42"],
        )
        fig_steam.update_geos(projection_type="natural earth")
        fig_steam.update_layout(margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_steam, use_container_width=True)

# Playstation Map
with col2:
    st.subheader("PS Distribution")
    if ps_df.empty:
        st.info("No PS data for the selected filters.")
    else:
        fig_ps = px.choropleth(
            ps_df,
            locations="country",
            locationmode="country names",
            color="count",
            color_continuous_scale=["#B3D9FF", "#0070CC"],
        )
        fig_ps.update_geos(projection_type="natural earth")
        fig_ps.update_layout(margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_ps, use_container_width=True)

# Count Helper
def compute_platform_counts(df):
    grouped=(
        df.groupby(["title","platform"])
        .agg(players=("playerid","nunique"))
        .reset_index()
    )
    pivoted=(
        grouped.pivot(index="title", columns="platform", values="players")
        .fillna(0)
        .reset_index()
    )
    pivoted["steam"]=pivoted.get("steam",0)
    pivoted["ps"]=pivoted.get("ps",0)
    pivoted["total"]=pivoted["steam"]+pivoted["ps"]
    return pivoted

# Top 10 Games Bar Plot
st.header("Top 10 Games - Global")

global_filtered=master_df.copy()
global_filtered=global_filtered[
    (global_filtered["date"]>=pd.Timestamp(selected_date[0]))
    &(global_filtered["date"]<=pd.Timestamp(selected_date[1]))
]
if "All" not in selected_platforms_bar:
    global_filtered=global_filtered[global_filtered["platform"].isin(selected_platforms_bar)]
if "All" not in selected_genres_bar:
    global_filtered=global_filtered[global_filtered["genres"].isin(selected_genres_bar)]

global_counts=compute_platform_counts(global_filtered)
global_top10=global_counts.sort_values("total", ascending=False).head(10)

global_chart=(
    alt.Chart(global_top10)
    .mark_bar()
    .transform_fold(["steam","ps"], as_=["platform","players"])
    .encode(
        x=alt.X("title:N", sort="-y"),
        y=alt.Y("players:Q"),
        color=alt.Color(
            "platform:N",
            scale=alt.Scale(
                domain=["steam","ps"],
                range=["#FF8C42","#0070CC"],
            ),
        ),
        tooltip=["title:N","platform:N","players:Q"],
    )
)
st.altair_chart(global_chart, use_container_width=True)

# Data Tables
st.header("Global Game Totals")
global_table_df=master_df.copy()
global_table_df=global_table_df[
    (global_table_df["date"]>=pd.Timestamp(selected_date[0]))
    &(global_table_df["date"]<=pd.Timestamp(selected_date[1]))
]
global_table_df=(
    global_table_df.groupby("title")
    .agg(total_players=("playerid","nunique"))
    .reset_index()
)
global_table_df=global_table_df.sort_values("total_players", ascending=False)
st.dataframe(global_table_df, hide_index=True)

# Country-Level Breakdown
st.header("Country-Level Player Breakdown")
country_table_df=master_df.copy()

# Date filter
country_table_df=country_table_df[
    (country_table_df["date"]>=pd.Timestamp(selected_date[0]))&
    (country_table_df["date"]<=pd.Timestamp(selected_date[1]))]

# Apply table filters
if "All" not in selected_table_countries:
    country_table_df=country_table_df[country_table_df["country"].isin(selected_table_countries)]

if "All" not in selected_table_games:
    country_table_df=country_table_df[country_table_df["title"].isin(selected_table_games)]

if "All" not in selected_table_platforms:
    country_table_df=country_table_df[country_table_df["platform"].isin(selected_table_platforms)]

if "All" not in selected_table_genres:
    country_table_df=country_table_df[country_table_df["genres"].isin(selected_table_genres)]

# Aggregate
country_table_df=(
    country_table_df.groupby(["country","title","platform"])
    .agg(players=("playerid","nunique"))
    .reset_index()
)

country_pivot=(
    country_table_df.pivot_table(
        index=["country","title"],columns="platform",values="players",fill_value=0).reset_index())

country_pivot["total_players"]=country_pivot.get("ps",0)+country_pivot.get("steam",0)
country_pivot=country_pivot.sort_values("total_players",ascending=False)

st.dataframe(country_pivot,hide_index=True)

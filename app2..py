import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# Page setup
# ---------------------------------------------------------
st.set_page_config(
    page_title="Nigeria Incident Data Analysis",
    page_icon="📊",
    layout="wide"
)

st.title("Nigeria Incident Data Analysis Dashboard")
st.write(
    "Explore incident trends, state-level patterns, incident descriptions "
    "and reported deaths across Nigeria."
)

# ---------------------------------------------------------
# Load and prepare data
# ---------------------------------------------------------
@st.cache_data
def load_data():
    data = pd.read_csv("cleaned_incidents_standardized.csv")

    data["Start date"] = pd.to_datetime(data["Start date"], errors="coerce")
    data["End date"] = pd.to_datetime(data["End date"], errors="coerce")
    data["Year"] = pd.to_numeric(data["Year"], errors="coerce").round().astype("Int64")
    data["Number of deaths"] = pd.to_numeric(
        data["Number of deaths"], errors="coerce"
    ).fillna(0)

    # Standardise text values used by the filters.
    data["State"] = (
        data["State"].fillna("Unclassified")
        .astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    )
    data["Month Name"] = data["Start date"].dt.month_name()
    data["Month Number"] = data["Start date"].dt.month

    return data

try:
    df = load_data()
except FileNotFoundError:
    st.error(
        "The file 'cleaned_incidents_standardized.csv' was not found. "
        "Place it in the same GitHub repository folder as app.py."
    )
    st.stop()

# ---------------------------------------------------------
# Research questions
# ---------------------------------------------------------
with st.expander("Research Questions", expanded=False):
    research_questions = [
        "How has the number of reported incidents changed from year to year?",
        "Which states recorded the highest number of incidents?",
        "Which states recorded the highest number of reported deaths?",
        "Which months recorded the highest number of incidents?",
        "What incident descriptions appeared most frequently in the dataset?",
        "Which recorded incidents had the highest reported death tolls?",
        "How does the average number of deaths per incident vary across states?",
        "How have reported deaths changed over the years?"
    ]
    for number, question in enumerate(research_questions, start=1):
        st.markdown(f"{number}. {question}")

# ---------------------------------------------------------
# Sidebar filters: multiselect dropdowns
# ---------------------------------------------------------
st.sidebar.header("Filter Incidents")
st.sidebar.caption("Select one or more values. Leave all selected to view the full dataset.")

year_options = sorted(
    [int(year) for year in df["Year"].dropna().unique()]
)
state_options = sorted(df["State"].dropna().unique().tolist())
month_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
month_options = [
    month for month in month_order if month in df["Month Name"].dropna().unique()
]

selected_years = st.sidebar.multiselect(
    "Year",
    options=year_options,
    default=year_options,
    format_func=lambda year: str(int(year)),
    help="Choose one or more years."
)

selected_states = st.sidebar.multiselect(
    "State",
    options=state_options,
    default=state_options,
    help="State names are standardised to remove duplicate spellings and formatting."
)

selected_months = st.sidebar.multiselect(
    "Month",
    options=month_options,
    default=month_options,
    help="Choose one or more months."
)

# ---------------------------------------------------------
# Apply filters consistently to every dashboard element
# ---------------------------------------------------------
filtered_df = df[
    df["Year"].isin(selected_years)
    & df["State"].isin(selected_states)
    & df["Month Name"].isin(selected_months)
].copy()

st.caption(
    f"Showing {len(filtered_df):,} of {len(df):,} records "
    f"for the selected filters."
)

if filtered_df.empty:
    st.warning("No records match the selected filters. Adjust your selections.")
    st.stop()

# ---------------------------------------------------------
# KPI cards
# ---------------------------------------------------------
st.subheader("Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Incidents", f"{len(filtered_df):,}")
col2.metric(
    "Total Reported Deaths",
    f"{int(filtered_df['Number of deaths'].sum()):,}"
)
col3.metric("States Covered", f"{filtered_df['State'].nunique():,}")
col4.metric(
    "Average Deaths per Incident",
    f"{filtered_df['Number of deaths'].mean():.2f}"
)

# ---------------------------------------------------------
# Trend charts
# ---------------------------------------------------------
st.subheader("Incident Trends")
left, right = st.columns(2)

with left:
    incidents_by_year = (
        filtered_df.groupby("Year").size()
        .sort_index().rename("Number of Incidents")
    )
    st.markdown("**Incidents by Year**")
    st.bar_chart(incidents_by_year)

with right:
    deaths_by_year = (
        filtered_df.groupby("Year")["Number of deaths"]
        .sum().sort_index().rename("Reported Deaths")
    )
    st.markdown("**Reported Deaths by Year**")
    st.bar_chart(deaths_by_year)

# Month chart in calendar order
st.markdown("**Incidents by Month**")
incidents_by_month = (
    filtered_df["Month Name"].value_counts()
    .reindex(month_order, fill_value=0)
)
st.bar_chart(incidents_by_month)

# Monthly time series
trend_data = filtered_df.dropna(subset=["Start date"]).copy()
trend_data["Month-Year"] = trend_data["Start date"].dt.to_period("M").astype(str)
monthly_trend = (
    trend_data.groupby("Month-Year").size()
    .rename("Number of Incidents").sort_index()
)
st.markdown("**Monthly Incident Trend Over Time**")
if not monthly_trend.empty:
    st.line_chart(monthly_trend)
else:
    st.info("No valid start dates are available for the selected filters.")

# ---------------------------------------------------------
# State-level charts
# ---------------------------------------------------------
st.subheader("State-Level Analysis")
left, right = st.columns(2)

with left:
    incidents_by_state = (
        filtered_df.groupby("State").size()
        .sort_values(ascending=False).head(10)
        .rename("Number of Incidents")
    )
    st.markdown("**Top 10 States by Number of Incidents**")
    st.bar_chart(incidents_by_state)

with right:
    deaths_by_state = (
        filtered_df.groupby("State")["Number of deaths"]
        .sum().sort_values(ascending=False).head(10)
        .rename("Reported Deaths")
    )
    st.markdown("**Top 10 States by Reported Deaths**")
    st.bar_chart(deaths_by_state, color="#FF0000")

avg_deaths_state = (
    filtered_df.groupby("State")["Number of deaths"]
    .mean().sort_values(ascending=False).head(10)
    .rename("Average Deaths per Incident")
)
st.markdown("**Top 10 States by Average Deaths per Incident**")
st.bar_chart(avg_deaths_state)

# State-by-year comparison
state_year = pd.pivot_table(
    filtered_df,
    index="State",
    columns="Year",
    values="Identifier",
    aggfunc="count",
    fill_value=0
)
if not state_year.empty:
    top_states = filtered_df["State"].value_counts().head(10).index
    st.markdown("**Incidents by State and Year (Top 10 States)**")
    st.bar_chart(state_year.loc[state_year.index.intersection(top_states)])

# ---------------------------------------------------------
# Incident description analysis
# ---------------------------------------------------------
st.subheader("Incident Description Analysis")
top_titles = (
    filtered_df["Title"].dropna().astype(str).str.strip()
    .value_counts().head(10).sort_values()
)
st.markdown("**10 Most Frequently Recorded Incident Descriptions**")
st.bar_chart(top_titles.rename("Number of Records"))

top_death_incidents = (
    filtered_df.sort_values("Number of deaths", ascending=False)
    [["Title", "State", "Start date", "Number of deaths"]]
    .head(10)
)
st.markdown("**10 Incidents with the Highest Reported Deaths**")
st.dataframe(top_death_incidents, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# Filtered records and download
# ---------------------------------------------------------
st.subheader("Filtered Incident Records")
st.dataframe(filtered_df, use_container_width=True, hide_index=True)

csv_data = filtered_df.drop(
    columns=["Month Number"], errors="ignore"
).to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Data as CSV",
    data=csv_data,
    file_name="filtered_incidents.csv",
    mime="text/csv"
)

# ---------------------------------------------------------
# Key findings for the current filter selection
# ---------------------------------------------------------
st.subheader("Key Findings")
total_deaths = filtered_df["Number of deaths"].sum()
state_counts = filtered_df["State"].value_counts()
top_state = state_counts.index[0] if not state_counts.empty else "N/A"
top_state_count = int(state_counts.iloc[0]) if not state_counts.empty else 0

highest_incident = filtered_df.loc[
    filtered_df["Number of deaths"].idxmax()
]

st.markdown(f"- **Incidents analysed:** {len(filtered_df):,}")
st.markdown(f"- **Total reported deaths:** {total_deaths:,.0f}")
st.markdown(
    f"- **State with the most incidents:** {top_state} "
    f"({top_state_count:,} incidents)"
)
st.markdown(
    f"- **Highest-death incident in the current selection:** "
    f"{highest_incident['Title']} "
    f"({highest_incident['Number of deaths']:,.0f} reported deaths)"
)

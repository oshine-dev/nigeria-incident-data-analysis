
import streamlit as st
import pandas as pd

# Page setup
st.set_page_config(
    page_title="Nigeria Incident Data Analysis",
    page_icon="📊",
    layout="wide"
)

# Load data
df = pd.read_csv("cleaned incidents.csv")


# Convert Month column to month names
df["Month"] = pd.to_numeric(df["Month"], errors="coerce")

df["Month Name"] = df["Month"].map({
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December"
})

df["Start date"] = pd.to_datetime(
    df["Start date"], errors="coerce"
)
df["End date"] = pd.to_datetime(
    df["End date"], errors="coerce"
)

# Convert Start date to datetime
df["Start date"] = pd.to_datetime(
    df["Start date"], errors="coerce"
)

# Recreate Month from Start date
df["Month"] = df["Start date"].dt.month

# Create month names
df["Month Name"] = df["Start date"].dt.month_name()

df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
df["Month"] = pd.to_numeric(df["Month"], errors="coerce")
df["Number of deaths"] = pd.to_numeric(
    df["Number of deaths"], errors="coerce"
).fillna(0)

# Dashboard title
st.title("Nigeria Incident Data Analysis Dashboard")
st.write(
    "Explore incident trends, state-level patterns, "
    "and reported deaths in Nigeria."
)

# Sidebar filters
st.sidebar.header("Filter Incidents")

years = sorted(df["Year"].dropna().unique().tolist())
states = sorted(df["State"].dropna().unique().tolist())

selected_years = st.sidebar.multiselect(
    "Select Year",
    options=years,
    default=years
)

month_options = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December"
]

selected_months = st.sidebar.multiselect(
    "Filter by Month",
    options=month_options,
    default=month_options
)

selected_states = st.sidebar.multiselect(
    "Select State",
    options=states,
    default=states
)

# Apply filters

filtered_df = df[
    (df["Year"].isin(selected_years)) &
    (df["State"].isin(selected_states)) &
    (df["Month Name"].isin(selected_months))
]


# KPI cards
st.subheader("Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Incidents",
    f"{len(filtered_df):,}"
)

col2.metric(
    "Total Deaths",
    f"{int(filtered_df['Number of deaths'].sum()):,}"
)

col3.metric(
    "States Covered",
    f"{filtered_df['State'].nunique():,}"
)

col4.metric(
    "Average Deaths per Incident",
    f"{filtered_df['Number of deaths'].mean():.2f}"
    if not filtered_df.empty else "0.00"
)

# Display filtered data
st.subheader("Filtered Incident Records")
st.dataframe(filtered_df, use_container_width=True)


# Monthly incident trend
st.subheader("Monthly Incident Trend")

trend_data = filtered_df.dropna(subset=["Start date"]).copy()

trend_data["Month-Year"] = (
    trend_data["Start date"].dt.to_period("M").astype(str)
)

monthly_trend = (
    trend_data.groupby("Month-Year")
    .size()
    .reset_index(name="Number of Incidents")
    .sort_values("Month-Year")
)

if not monthly_trend.empty:
    st.line_chart(
        monthly_trend.set_index("Month-Year"),
        y="Number of Incidents"
    )
else:
    st.info("No incident data available for the selected filters.")

# Ensure deaths are numeric
filtered_df["Number of deaths"] = pd.to_numeric(
    filtered_df["Number of deaths"], errors="coerce"
).fillna(0)

# Top 10 states by number of incidents
st.subheader("Top 10 States by Number of Incidents")

incidents_by_state = filtered_df["State"].value_counts().head(10)

st.bar_chart(incidents_by_state)

# Top 10 states by total deaths
st.subheader("Top 10 States by Total Deaths")

deaths_by_state = (
    filtered_df.groupby("State")["Number of deaths"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

st.bar_chart(deaths_by_state, color="#FF0000")

# Download filtered incident data
st.subheader("Download Incident Data")

csv_data = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Data as CSV",
    data=csv_data,
    file_name="filtered_incidents.csv",
    mime="text/csv"
)

# Key Findings
st.subheader("Key Findings")

if not filtered_df.empty:
    total_incidents = len(filtered_df)
    total_deaths = filtered_df["Number of deaths"].sum()

    st.write(
        f"- **Total incidents analysed:** {total_incidents:,}"
    )
    st.write(
        f"- **Total reported deaths:** {total_deaths:,.0f}"
    )

    # State with the most incidents
    state_incidents = filtered_df["State"].dropna().value_counts()

    if not state_incidents.empty:
        top_state = state_incidents.idxmax()
        top_state_count = state_incidents.max()

        st.write(
            f"- **State with the most incidents:** "
            f"{top_state} ({top_state_count:,} incidents)"
        )

    # Incident with the highest reported deaths
    if not filtered_df.empty:
        highest_incident = filtered_df.loc[
            filtered_df["Number of deaths"].idxmax()
        ]

        st.write(
            f"- **Highest-death incident:** "
            f"{highest_incident['Title']} "
            f"({highest_incident['Number of deaths']:,.0f} deaths)"
        )
else:
    st.info("No incidents match the selected filters.")

st.subheader("Number of Incidents by Month")

month_order = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December"
]

monthly_incidents = (
    filtered_df["Month Name"]
    .value_counts()
    .reindex(month_order, fill_value=0)
)

st.bar_chart(monthly_incidents)



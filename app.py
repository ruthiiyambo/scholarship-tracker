"""
Scholarship Tracker

Run locally:
    streamlit run app.py
"""

import datetime as dt
import pandas as pd
import streamlit as st

# Basic page setup
st.set_page_config(page_title="Scholarship Tracker", page_icon="🎓", layout="wide")

# Simple styling for cards and badges
st.markdown(
    """
    <style>
    .card {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        background: #ffffff;
        box-shadow: 0 1px 2px rgba(0,0,0,0.06);
        color: #111827;
    }
    .card h3 {
        margin: 0 0 8px 0;
        font-size: 1.2rem;
        color: #111827;
    }
    .meta {
        color: #6b7280;
        font-size: 0.9rem;
    }
    .card p {
        color: #111827;
    }
    .card strong {
        color: #111827;
    }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-left: 8px;
    }
    .badge-open { background: #e7f9ef; color: #0f5132; }
    .badge-soon { background: #fff4d6; color: #7a5b00; }
    .badge-closed { background: #fde2e2; color: #842029; }
    .link a {
        text-decoration: none;
        color: #1d4ed8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Title and intro
st.title("Scholarship Tracker")
st.write("Find scholarships, check eligibility, and track deadlines.")

# Load data from CSV
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    data = pd.read_csv(path)
    data["Deadline"] = pd.to_datetime(data["Deadline"], errors="coerce")
    return data

try:
    df = load_data("scholarships.csv")
except FileNotFoundError:
    st.error("Could not find scholarships.csv in the project folder.")
    st.stop()

# Add helper columns for status and days left
# Days left: positive means deadline in the future
# Status:
# - Closed: deadline passed
# - Closing Soon: deadline within 14 days
# - Open: deadline beyond 14 days

TODAY = dt.date.today()

def compute_days_left(deadline: pd.Timestamp) -> int | None:
    if pd.isna(deadline):
        return None
    return (deadline.date() - TODAY).days


def compute_status(days_left: int | None) -> str:
    if days_left is None:
        return "Open"
    if days_left < 0:
        return "Closed"
    if days_left <= 14:
        return "Closing Soon"
    return "Open"


df["Days Left"] = df["Deadline"].apply(compute_days_left)
df["Deadline Status"] = df["Days Left"].apply(compute_status)

# Sidebar filters
st.sidebar.header("Filters")

country_options = ["All"] + sorted(df["Country/Region"].dropna().unique().tolist())
degree_options = ["All"] + sorted(df["Degree Level"].dropna().unique().tolist())
field_options = ["All"] + sorted(df["Field of Study"].dropna().unique().tolist())
status_options = ["All", "Open", "Closing Soon", "Closed"]

country_filter = st.sidebar.selectbox("Country/Region", country_options)
degree_filter = st.sidebar.selectbox("Degree Level", degree_options)
field_filter = st.sidebar.selectbox("Field of Study", field_options)
status_filter = st.sidebar.selectbox("Deadline Status", status_options)

# Search bar
search_query = st.text_input("Search by name or keyword", value="")

# Apply filters
filtered = df.copy()

if country_filter != "All":
    filtered = filtered[filtered["Country/Region"] == country_filter]
if degree_filter != "All":
    filtered = filtered[filtered["Degree Level"] == degree_filter]
if field_filter != "All":
    filtered = filtered[filtered["Field of Study"] == field_filter]
if status_filter != "All":
    filtered = filtered[filtered["Deadline Status"] == status_filter]

if search_query.strip():
    query = search_query.lower()
    filtered = filtered[
        filtered.apply(
            lambda row: query in " ".join(row.astype(str)).lower(),
            axis=1,
        )
    ]

# Results
st.subheader(f"Scholarships ({len(filtered)})")

if filtered.empty:
    st.info("No scholarships match your filters. Try removing a filter or search term.")
else:
    for _, row in filtered.iterrows():
        deadline = row["Deadline"]
        days_left = row["Days Left"]
        status = row["Deadline Status"]

        if status == "Closed":
            badge_class = "badge-closed"
        elif status == "Closing Soon":
            badge_class = "badge-soon"
        else:
            badge_class = "badge-open"

        deadline_display = "TBD" if pd.isna(deadline) else deadline.strftime("%Y-%m-%d")

        if status == "Closed":
            days_left_text = "Closed"
        else:
            days_left_text = "TBD" if days_left is None else f"{days_left} days left"

        st.markdown(
            f"""
            <div class="card">
                <h3>{row['Scholarship Name']}
                    <span class="badge {badge_class}">{status}</span>
                </h3>
                <div class="meta">Deadline: {deadline_display} | {days_left_text}</div>
                <p><strong>Eligibility:</strong> {row['Eligibility']}</p>
                <p><strong>Award Amount:</strong> {row['Award Amount']}</p>
                <p><strong>Country/Region:</strong> {row['Country/Region']}</p>
                <p><strong>Degree Level:</strong> {row['Degree Level']}</p>
                <p><strong>Field of Study:</strong> {row['Field of Study']}</p>
                <p class="link"><strong>Application Link:</strong> <a href="{row['Application Link']}" target="_blank">{row['Application Link']}</a></p>
                <p><strong>Notes:</strong> {row['Notes']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

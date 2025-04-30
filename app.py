import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Streamlit page configuration
st.set_page_config(
    page_title="HIT 3: Movie Analytics Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS (unchanged)
st.markdown("""
    <style>
    .main, .stApp {
        background-color: #111111 !important;
        color: #f5f5f5 !important;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #ff4d4d !important;
        font-family: 'Arial Black', Arial, sans-serif;
        letter-spacing: 1px;
    }
    .stMarkdown, .stDataFrame, .stText, .stTable, .stDownloadButton, .stButton>button {
        color: #f5f5f5 !important;
    }
    .stButton>button {
        background-color: #ff4d4d;
        color: white;
        border-radius: 5px;
        font-weight: bold;
    }
    .stDownloadButton>button {
        background-color: #4d94ff !important;
        color: #fff !important;
        border-radius: 5px !important;
        font-weight: bold !important;
        border: none !important;
        box-shadow: 0 2px 8px #00000055 !important;
    }
    .stDataFrame {
        background-color: #222222;
        color: #f5f5f5;
    }
    .metric-card {
        background: linear-gradient(135deg, #222 60%, #2a2a2a 100%);
        padding: 18px 10px 10px 10px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 8px #00000055;
        margin-bottom: 10px;
    }
    .movie-info-card {
        background: linear-gradient(120deg, #191919 80%, #222 100%);
        border-radius: 16px;
        box-shadow: 0 4px 24px #00000099;
        padding: 32px 24px 24px 24px;
        margin-bottom: 32px;
        display: flex;
        align-items: flex-start;
        gap: 32px;
    }
    .movie-poster {
        border-radius: 12px;
        box-shadow: 0 2px 16px #00000088;
        width: 220px;
        height: auto;
        object-fit: cover;
    }
    .movie-details {
        flex: 1;
    }
    .movie-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #ff4d4d;
        margin-bottom: 0.5rem;
    }
    .movie-desc {
        font-size: 1.15rem;
        color: #f5f5f5;
        margin-bottom: 1.2rem;
    }
    .movie-castcrew {
        font-size: 1.05rem;
        color: #ffd700;
        margin-bottom: 0.5rem;
    }
    .movie-section-title {
        color: #4d94ff;
        font-size: 1.2rem;
        font-weight: bold;
        margin-top: 1.2rem;
        margin-bottom: 0.3rem;
    }
    </style>
""", unsafe_allow_html=True)

# Function to load and process CSV data
def load_csv_data(csv_path):
    try:
        # Check if file exists
        if not os.path.exists(csv_path):
            st.error(f"CSV file not found at {csv_path}")
            logger.error(f"CSV file not found at {csv_path}")
            return None
        
        # Read CSV
        df = pd.read_csv(csv_path)
        
        # Validate required columns
        required_columns = [
            "AreaName", "ShowCount", "FastFillingShows", "SoldOutShows",
            "Occupancy", "BookedGross", "MaxCapacityGross",
            "BookedTicketsCount", "TotalTicketsCount"
        ]
        if not all(col in df.columns for col in required_columns):
            st.error("CSV file is missing required columns")
            logger.error("CSV file is missing required columns")
            return None
        
        # Ensure Occupancy is formatted as string with % symbol
        df["Occupancy"] = df["Occupancy"].apply(lambda x: f"{float(x):.2f}%" if isinstance(x, (int, float)) else x)
        
        # Sort by occupancy (excluding OVERALL_TOTAL)
        city_df = df[df["AreaName"] != "OVERALL_TOTAL"]
        city_df = city_df.sort_values(
            by="Occupancy",
            key=lambda x: x.apply(lambda y: float(y.strip("%"))),
            ascending=False
        )
        
        # Append OVERALL_TOTAL if it exists
        total_df = df[df["AreaName"] == "OVERALL_TOTAL"]
        results = pd.concat([city_df, total_df]).reset_index(drop=True)
        
        return results
    
    except Exception as e:
        st.error(f"Error loading CSV file: {str(e)}")
        logger.error(f"Error loading CSV file: {e}")
        return None

# Function to get last modified time of CSV file
def get_file_last_modified(csv_path):
    try:
        if os.path.exists(csv_path):
            mtime = os.path.getmtime(csv_path)
            return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        return "Unknown"
    except Exception as e:
        logger.error(f"Error getting file modification time: {e}")
        return "Unknown"

# Main dashboard
def main():
    # Path to the CSV file (adjust as needed)
    CSV_PATH = "./movie_analytics_ET00410905.csv"
    
    st.title(":red[Movie Analytics Dashboard]")
    last_modified = get_file_last_modified(CSV_PATH)
    st.markdown(f"**Last Updated:** {last_modified} (Updates every hour)")

    # --- Key Metrics Section ---
    st.header(":orange[Key Metrics]")
    
    # Load data
    with st.spinner("Loading analytics data..."):
        df = load_csv_data(CSV_PATH)
    
    if df is None:
        st.error("Failed to load data. Please ensure the CSV file is available and correctly formatted.")
        return

    cols = st.columns(4)
    with cols[0]:
        st.markdown(f"<div class='metric-card'><h3>Total Shows</h3><p>{df.iloc[-1]['ShowCount']}</p></div>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"<div class='metric-card'><h3>Fast-Filling Shows</h3><p>{df.iloc[-1]['FastFillingShows']}</p></div>", unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f"<div class='metric-card'><h3>Sold-Out Shows</h3><p>{df.iloc[-1]['SoldOutShows']}</p></div>", unsafe_allow_html=True)
    with cols[3]:
        st.markdown(f"<div class='metric-card'><h3>Overall Occupancy</h3><p>{df.iloc[-1]['Occupancy']}</p></div>", unsafe_allow_html=True)

    # --- Detailed Analytics Section ---
    st.header(":blue[Detailed Analytics]")
    st.dataframe(df.style.format({
        "BookedGross": "₹{:.2f}",
        "MaxCapacityGross": "₹{:.2f}",
        "Occupancy": "{}"
    }), use_container_width=True)

    # --- Visual Insights Section ---
    st.header(":violet[Visual Insights]")
    
    # Occupancy by City
    city_df = df[df["AreaName"] != "OVERALL_TOTAL"]
    fig_occupancy = px.bar(
        city_df,
        x="AreaName",
        y=city_df["Occupancy"].apply(lambda x: float(x.strip("%"))),
        title="Occupancy by City",
        labels={"y": "Occupancy (%)"},
        color="AreaName",
        color_discrete_sequence=px.colors.qualitative.Set1
    )
    st.plotly_chart(fig_occupancy, use_container_width=True)

    # Revenue Comparison
    fig_revenue = go.Figure(data=[
        go.Bar(name="Booked Gross", x=city_df["AreaName"], y=city_df["BookedGross"].astype(float), marker_color="#ff4d4d"),
        go.Bar(name="Max Capacity Gross", x=city_df["AreaName"], y=city_df["MaxCapacityGross"].astype(float), marker_color="#4d94ff")
    ])
    fig_revenue.update_layout(
        title="Revenue Comparison by City",
        barmode="group",
        yaxis_title="Amount (₹)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_revenue, use_container_width=True)

    # --- Export Data Section ---
    st.header(":green[Export Data]")
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Analytics as CSV",
        data=csv,
        file_name="movie_analytics_ET00410905.csv",
        mime="text/csv"
    )

    # --- Movie Info Section (unchanged) ---
    with st.container():
        cols = st.columns([1, 3])
        with cols[0]:
            st.image("Hit3.jpg", caption="HIT 3 Poster", use_column_width=True)
        with cols[1]:
            st.markdown(
                f"""
                <div class='movie-details'>
                    <div class='movie-title'>HIT: The Third Case (HIT 3)</div>
                    <div class='movie-desc'>
                        <b>Genre:</b> Action, Thriller<br>
                        <b>Description:</b> \"HIT: The Third Case\" (also known as \"HIT 3\") is a Telugu action thriller film starring Nani as cop Arjun Sarkaar, who is assigned a high-priority case in Jammu and Kashmir to catch a group of serial killers. The film, directed by Sailesh Kolanu, explores the dark side of the criminal world and Arjun's bloody quest for justice.
                    </div>
                    <div class='movie-section-title'>Main Cast</div>
                    <div class='movie-castcrew'>
                        <b>Nani</b> as Arjun Sarkaar<br>
                        <b>Srinidhi Shetty</b>
                    </div>
                    <div class='movie-section-title'>Crew</div>
                    <div class='movie-castcrew'>
                        <b>Director:</b> Sailesh Kolanu<br>
                        <b>Producer:</b> Prashanti Tipirneni<br>
                        <b>Music:</b> Mickey J Meyar<br>
                        <b>Cinematography:</b> Sanu John Varghese<br>
                        <b>Editor:</b> Karthik Srinivas
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

if __name__ == "__main__":
    main()

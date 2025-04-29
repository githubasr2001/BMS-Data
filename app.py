import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import uuid
import time
import logging
import random

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

# Enhanced Custom CSS for a deeper dark theme and brighter text
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

# City configurations
CITIES = {
    "Hyderabad": {
        "regionCode": "HYD",
        "subRegionCode": "HYD",
        "regionSlug": "hyderabad",
        "latitude": "17.385044",
        "longitude": "78.486671"
    },
    "Bangalore": {
        "regionCode": "BANG",
        "subRegionCode": "BANG",
        "regionSlug": "bangalore",
        "latitude": "12.9716",
        "longitude": "77.5946"
    },
    "Chennai": {
        "regionCode": "CHEN",
        "subRegionCode": "CHEN",
        "regionSlug": "chennai",
        "latitude": "13.0827",
        "longitude": "80.2707"
    }
}

# Function to implement exponential backoff
def retry_with_backoff(retries=3, backoff_in_seconds=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    if x == retries:
                        raise e
                    sleep = (backoff_in_seconds * 2 ** x + 
                            random.uniform(0, 1))
                    time.sleep(sleep)
                    x += 1
        return wrapper
    return decorator

# Function to fetch showtimes with new caching and retry logic
@st.cache_data(ttl=1800)
@retry_with_backoff(retries=3)
def fetch_showtimes(city):
    url = f"https://in.bookmyshow.com/api/movies-data/showtimes-by-event?appCode=MOBAND2&appVersion=14304&language=en&eventCode=ET00410905&regionCode={city['regionCode']}&subRegion={city['subRegionCode']}&bmsId=1.21345445.1703250084656&token=67x1xa33b4x422b361ba&lat={city['latitude']}&lon={city['longitude']}&query="
    
    headers = {
        "Host": "in.bookmyshow.com",
        "x-bms-id": "1.21345445.1703250084656",
        "x-region-code": city["regionCode"],
        "x-subregion-code": city["subRegionCode"],
        "x-region-slug": city["regionSlug"],
        "x-platform": "AND",
        "x-platform-code": "ANDROID",
        "x-app-code": "MOBAND2",
        "x-device-make": "Google-Pixel XL",
        "x-screen-height": "2392",
        "x-screen-width": "1440",
        "x-screen-density": "3.5",
        "x-app-version": "14.3.4",
        "x-app-version-code": "14304",
        "x-network": "Android | WIFI",
        "x-latitude": city["latitude"],
        "x-longitude": city["longitude"],
        "x-ab-testing": "adtechHPSlug=default",
        "x-location-selection": "manual",
        "x-location-shared": "false",
        "lang": "en",
        "user-agent": "Dalvik/2.1.0 (Linux; U; Android 12; Pixel XL Build/SP2A.220505.008)"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            st.error("⚠️ BookMyShow API rate limit reached. Please try again in a few minutes.")
            logger.error(f"Rate limit exceeded for {city['regionSlug']}")
        else:
            st.error(f"⚠️ Failed to fetch data from BookMyShow API: {str(e)}")
            logger.error(f"Error fetching showtimes for {city['regionSlug']}: {e}")
        return None
    except Exception as e:
        st.error(f"⚠️ An unexpected error occurred: {str(e)}")
        logger.error(f"Unexpected error for {city['regionSlug']}: {e}")
        return None

# Function to process showtime data
def process_showtime_data(area_name, data):
    grand_total_max_seats = 0
    grand_total_seats_available = 0
    grand_total_booked_tickets = 0
    grand_total_gross = 0
    grand_booked_gross = 0
    total_show_count = 0
    fast_filling_show_count = 0
    sold_out_show_count = 0
    fast_filling_threshold = 70

    if data and data.get("ShowDetails"):
        for show_detail in data["ShowDetails"]:
            if show_detail.get("Venues"):
                for venue in show_detail["Venues"]:
                    if venue.get("ShowTimes"):
                        for show_time in venue["ShowTimes"]:
                            total_show_count += 1
                            total_max_seats = 0
                            total_seats_available = 0
                            total_booked_tickets = 0
                            total_gross = 0
                            booked_gross = 0

                            if show_time.get("Categories"):
                                for category in show_time["Categories"]:
                                    max_seats = int(category.get("MaxSeats", 0)) or 0
                                    seats_avail = int(category.get("SeatsAvail", 0)) or 0
                                    booked_tickets = max_seats - seats_avail
                                    current_price = float(category.get("CurPrice", 0)) or 0

                                    total_max_seats += max_seats
                                    total_seats_available += seats_avail
                                    total_booked_tickets += booked_tickets
                                    total_gross += max_seats * current_price
                                    booked_gross += booked_tickets * current_price

                            show_occupancy = (total_booked_tickets / total_max_seats * 100) if total_max_seats > 0 else 0
                            if fast_filling_threshold <= show_occupancy < 100:
                                fast_filling_show_count += 1
                            if show_occupancy >= 99.5:
                                sold_out_show_count += 1

                            grand_total_max_seats += total_max_seats
                            grand_total_seats_available += total_seats_available
                            grand_total_booked_tickets += total_booked_tickets
                            grand_total_gross += total_gross
                            grand_booked_gross += booked_gross

    grand_occupancy = (grand_total_booked_tickets / grand_total_max_seats * 100) if grand_total_max_seats > 0 else 0
    
    return {
        "AreaName": area_name,
        "ShowCount": total_show_count,
        "FastFillingShows": fast_filling_show_count,
        "SoldOutShows": sold_out_show_count,
        "Occupancy": f"{grand_occupancy:.2f}%",
        "BookedGross": grand_booked_gross,
        "MaxCapacityGross": grand_total_gross,
        "BookedTicketsCount": grand_total_booked_tickets,
        "TotalTicketsCount": grand_total_max_seats
    }

# Function to fetch and process all showtimes
def fetch_all_showtimes():
    results = []
    for city_name, city_config in CITIES.items():
        logger.info(f"Fetching data for {city_name}")
        data = fetch_showtimes(city_config)
        if data:
            result = process_showtime_data(city_name, data)
            results.append(result)
    
    # Sort by occupancy
    results.sort(key=lambda x: float(x["Occupancy"].strip("%")), reverse=True)
    
    # Calculate totals
    totals = {
        "AreaName": "OVERALL_TOTAL",
        "ShowCount": sum(r["ShowCount"] for r in results),
        "FastFillingShows": sum(r["FastFillingShows"] for r in results),
        "SoldOutShows": sum(r["SoldOutShows"] for r in results),
        "BookedGross": sum(r["BookedGross"] for r in results),
        "MaxCapacityGross": sum(r["MaxCapacityGross"] for r in results),
        "BookedTicketsCount": sum(r["BookedTicketsCount"] for r in results),
        "TotalTicketsCount": sum(r["TotalTicketsCount"] for r in results),
        "Occupancy": f"{(sum(r['BookedTicketsCount'] for r in results) / sum(r['TotalTicketsCount'] for r in results) * 100):.2f}%" if sum(r["TotalTicketsCount"] for r in results) > 0 else "0.00%"
    }
    
    results.append(totals)
    return results

# Main dashboard
def main():
    st.title(":red[Movie Analytics Dashboard]")
    st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Updates every 30 minutes)")

    # --- Key Metrics Section ---
    st.header(":orange[Key Metrics]")
    # Fetch data
    with st.spinner("Fetching latest showtime data..."):
        results = fetch_all_showtimes()
    
    if not results:
        st.error("Failed to fetch data. Please try again later.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(results)
    
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

    # --- Movie Info Section ---
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
import streamlit as st
import pandas as pd
import geopandas as gpd
from geopy.geocoders import GoogleV3
from shapely.geometry import Point
from io import BytesIO
import re

def geocoding_page():
    st.title("Geocoding & Reverse Geocoding")

    geocoding_mode = st.radio("Select Geocoding Mode:", ["Geocoding", "Reverse Geocoding"])
    coordinate_format = st.radio("Select Coordinate Format:", ["W, N", "Lat, Lng"])

    if geocoding_mode == "Geocoding":
        address = st.text_input("Enter an address to geocode:")
    else:
        if coordinate_format == "W, N":
            w_coord = st.text_input("Enter W Coordinate:")
            n_coord = st.text_input("Enter N Coordinate:")
        else:
            lat = st.text_input("Enter Latitude:")
            lng = st.text_input("Enter Longitude:")

    file_upload = st.file_uploader("Upload a CSV file for batch processing (Optional)", type=["csv"])

    if st.button("Process"):
        # geolocator = GoogleV3(api_key=st.secrets["wander_key"])
        geolocator = GoogleV3(api_key='AIzaSyD6XxLeRgR8ZiGdKSwayaPEDn2GGkiHOyc')

        if file_upload:
            df = pd.read_csv(file_upload)

            if geocoding_mode == "Geocoding":
                df['location'] = df['address'].apply(geolocator.geocode)
                df['lat'] = df['location'].apply(lambda loc: loc.latitude if loc else None)
                df['lng'] = df['location'].apply(lambda loc: loc.longitude if loc else None)
            else:
                if coordinate_format == "W, N":
                    df['lat'], df['lng'] = df['n_coord'].apply(convert_w_n_to_lat_lng)
                df['address'] = df.apply(lambda row: geolocator.reverse(f"{row['lat']}, {row['lng']}").address if row['lat'] and row['lng'] else None, axis=1)

            df.drop(columns=['location'], inplace=True)

            st.write(df.head())

            buffer = BytesIO()
            df.to_csv(buffer, index=False)
            buffer.seek(0)

            st.download_button(
                label="Download Processed File",
                data=buffer,
                file_name="processed_geocoding.csv",
                mime="text/csv"
            )

        else:
            if geocoding_mode == "Geocoding":
                location = geolocator.geocode(address)
                if location:
                    st.write(f"Address: {address}")
                    st.write(f"Latitude: {location.latitude}, Longitude: {location.longitude}")
            else:
                if coordinate_format == "W, N":
                    lat, lng = convert_w_n_to_lat_lng(w_coord, n_coord)
                location = geolocator.reverse(f"{lat}, {lng}")
                if location:
                    st.write(f"Coordinates: {lat}, {lng}")
                    st.write(f"Address: {location.address}")

    if st.button("Back to Home"):
        st.session_state.operation = None
        st.experimental_rerun()

def convert_w_n_to_lat_lng(w_coord, n_coord):
    def dms_to_decimal(dms_str):
        parts = re.split('[°\'"]+', dms_str)
        degrees = float(parts[0])
        minutes = float(parts[1]) / 60
        seconds = float(parts[2]) / 3600
        return degrees + minutes + seconds
    
    lat = dms_to_decimal(n_coord)
    lng = -dms_to_decimal(w_coord)  # Assuming W is negative longitude
    return lat, lng

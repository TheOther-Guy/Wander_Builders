import streamlit as st
import osmnx as ox
import pandas as pd
import geopandas as gpd
import base64
import json
from io import BytesIO
import requests
import time

def search_pois():
    st.title("Search for Points of Interest")

    place_name = st.text_input("Enter a place name or address:")
    search_type = st.radio("Select Search Type", ["OSM", "Google POIs"])

    google_types = [
        "accounting", "airport", "amusement_park", "aquarium", "art_gallery", "atm",
        "bakery", "bank", "bar", "beauty_salon", "bicycle_store", "book_store",
        "bowling_alley", "bus_station", "cafe", "campground", "car_dealer", "car_rental",
        "car_repair", "car_wash", "casino", "cemetery", "church", "city_hall",
        "clothing_store", "convenience_store", "courthouse", "dentist", "department_store",
        "doctor", "drugstore", "electrician", "electronics_store", "embassy",
        "fire_station", "florist", "funeral_home", "furniture_store", "gas_station", "gym",
        "hair_care", "hardware_store", "hindu_temple", "home_goods_store", "hospital",
        "insurance_agency", "jewelry_store", "laundry", "lawyer", "library",
        "light_rail_station", "liquor_store", "local_government_office", "locksmith",
        "lodging", "meal_delivery", "meal_takeaway", "mosque", "movie_rental",
        "movie_theater", "moving_company", "museum", "night_club", "painter", "park",
        "parking", "pet_store", "pharmacy", "physiotherapist", "plumber", "police",
        "post_office", "primary_school", "real_estate_agency", "restaurant",
        "roofing_contractor", "rv_park", "school", "secondary_school", "shoe_store",
        "shopping_mall", "spa", "stadium", "storage", "store", "subway_station",
        "supermarket", "synagogue", "taxi_stand", "tourist_attraction", "train_station",
        "transit_station", "travel_agency", "university", "veterinary_care", "zoo"
    ]

    if search_type == "OSM":
        category_tags = {
            "Lodging": [{"tourism": ["hotel", "motel", "guest_house", "hostel"]}],
            "Food & Drink": [{"amenity": ["restaurant", "cafe", "pub", "bar"]}],
            "Shopping": [{"shop": True}],
            "Things To Do": [{"tourism": "attraction"}, {"leisure": ["park", "sports_centre"]}],
            "Museums": [{"tourism": "museum"}]
        }

        selected_categories = st.multiselect(
            'Select Categories to Search For:',
            options=list(category_tags.keys()), 
            default=['Food & Drink']
        )

        tags = {}
        for category in selected_categories:
            for tag in category_tags[category]:
                tags.update(tag)

    elif search_type == "Google POIs":
        selected_types = st.multiselect('Select Types to Search For:', google_types, ['restaurant'])

    if st.button("Search"):
        if search_type == "OSM" and place_name:
            gdf = ox.geometries_from_place(place_name, tags=tags)
            gdf_dissolve = gdf.dissolve(by='name')[['geometry']].reset_index()
            gdf_dissolve = gdf_dissolve[gdf_dissolve['geometry'].geom_type == 'Point']

            geojson_str = gdf_dissolve.to_json()
            csv_text = gdf_dissolve.to_csv(index=False)

            b64 = base64.b64encode(geojson_str.encode()).decode()
            st.markdown(f'<a href="data:file/json;base64,{b64}" download="{place_name}_{selected_categories}_OSM_POIs.geojson">Download GeoJSON file</a>', unsafe_allow_html=True)

            b64 = base64.b64encode(csv_text.encode()).decode()
            st.markdown(f'<a href="data:file/json;base64,{b64}" download="{place_name}_{selected_categories}_OSM_POIs.csv">Download CSV file</a>', unsafe_allow_html=True)

        elif search_type == "Google POIs" and place_name:
            places = search_google_pois(place_name, selected_types)
            if places:
                features = [{
                    "type": "Feature",
                    "properties": {"name": place.get("name")},
                    "geometry": {
                        "type": "Point",
                        "coordinates": [place.get("geometry", {}).get("location", {}).get("lng"),
                                        place.get("geometry", {}).get("location", {}).get("lat")]
                    }
                } for place in places]

                geojson = {
                    "type": "FeatureCollection",
                    "features": features
                }

                geojson_str = json.dumps(geojson)
                b64 = base64.b64encode(geojson_str.encode()).decode()
                st.markdown(f'<a href="data:file/json;base64,{b64}" download="{place_name}_{selected_types}_Google_POIs.geojson">Download GeoJSON file</a>', unsafe_allow_html=True)

                places_dicts = [{
                    "Name": place.get("name"),
                    "Latitude": place.get("geometry", {}).get("location", {}).get("lat"),
                    "Longitude": place.get("geometry", {}).get("location", {}).get("lng")
                } for place in places]

                df = pd.DataFrame(places_dicts)
                csv = df.to_csv(index=False)
                st.download_button("Download CSV", csv, file_name=f"{place_name.replace(' ', '_')}_{selected_types}_Google_POIs.csv")

    if st.button('Back to Home'):
        st.session_state.operation = None
        st.experimental_rerun()

def search_google_pois(place_name, selected_types):
    # api_key = st.secrets["wander_key"]
    api_key = 'AIzaSyD6XxLeRgR8ZiGdKSwayaPEDn2GGkiHOyc'
    API_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    NEARBY_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    params = {
        'input': place_name,
        'inputtype': 'textquery',
        'fields': 'photos,formatted_address,name,geometry',
        'key': api_key
    }

    place_response = requests.get(API_URL, params=params).json()
    if place_response.get("candidates"):
        location = place_response['candidates'][0]['geometry']['location']
        
        nearby_params = {
            'location': f"{location['lat']},{location['lng']}",
            'radius': '30000',
            'type': '|'.join(selected_types),
            'key': api_key
        }

        all_places = []
        next_page_token = None

        while True:
            if next_page_token:
                nearby_params['pagetoken'] = next_page_token
            else:
                nearby_params.pop('pagetoken', None)

            response = requests.get(NEARBY_SEARCH_URL, params=nearby_params)
            results = response.json()

            all_places.extend(results.get('results', []))

            next_page_token = results.get('next_page_token')
            if not next_page_token:
                break
            else:
                time.sleep(2)

        return all_places
    else:
        return []

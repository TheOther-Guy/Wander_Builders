import streamlit as st
import geopandas as gpd
import xml.etree.ElementTree as ET
import os
from shapely.geometry import Polygon, Point, LineString, MultiLineString
import json
from io import BytesIO
import random

# Function to extract coordinates from KML
def extract_coordinates(coordinates):
    coords = coordinates.text.split()
    coord_list = []
    for coord in coords:
        lon, lat, _ = coord.split(",")
        coord_list.append([float(lon), float(lat)])
    return coord_list

def kml_to_geojson(kml_path):
    # Parse the KML file
    tree = ET.parse(kml_path)
    root = tree.getroot()

    # Define the KML namespace
    kml_ns = "{http://www.opengis.net/kml/2.2}"

    # Define the base structure for the GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    # Function to extract coordinates from KML
    def extract_coordinates(coordinates):
        coords = coordinates.text.split()
        coord_list = []
        for coord in coords:
            lon, lat, _ = coord.split(",")
            coord_list.append([float(lon), float(lat)])
        return coord_list

    # Iterate over Placemark elements in the KML
    for placemark in root.findall(".//{}Placemark".format(kml_ns)):
        # Create a base feature structure
        feature = {
            "type": "Feature",
            "properties": {},
            "geometry": {}
        }
        
        # Extract Polygon geometries
        polygon = placemark.find(".//{}Polygon".format(kml_ns))
        if polygon is not None:
            feature["geometry"]["type"] = "Polygon"
            outer_boundary = polygon.find("{}outerBoundaryIs/{}LinearRing/{}coordinates".format(kml_ns, kml_ns, kml_ns))
            feature["geometry"]["coordinates"] = [extract_coordinates(outer_boundary)]
            
        # Extract LineString geometries
        linestring = placemark.find(".//{}LineString".format(kml_ns))
        if linestring is not None:
            feature["geometry"]["type"] = "LineString"
            coordinates = linestring.find("{}coordinates".format(kml_ns))
            feature["geometry"]["coordinates"] = extract_coordinates(coordinates)

        # If we've defined a geometry, add the feature to the list
        if "type" in feature["geometry"]:
            geojson["features"].append(feature)

    return geojson

###################
def make_random_changes_from_file(gdf, tolerance=0.000007):
    """
    Modify the LineString or MultiLineString geometry in the given GeoDataFrame.
    
    Parameters:
        gdf (GeoDataFrame): Input GeoDataFrame.
        tolerance (float): Amount by which to randomly alter each coordinate.
        
    Returns:
        GeoDataFrame: Modified GeoDataFrame.
    """

    def is_linestring_or_multilinestring(geom):
        return isinstance(geom, (LineString, MultiLineString))

    # Filter rows where the geometry is LineString or MultiLineString
    lines = gdf[gdf.geometry.apply(is_linestring_or_multilinestring)]

    # If there are no LineString or MultiLineString geometries, return the original GeoDataFrame
    if lines.shape[0] == 0:
        return gdf

    modified_geoms = []
    for geometry in lines.geometry:
        if isinstance(geometry, LineString):
            coords = list(geometry.coords)
            modified_coords = [(x + random.uniform(-tolerance, tolerance), y + random.uniform(-tolerance, tolerance)) for x, y in coords]
            modified_geoms.append(LineString(modified_coords))
        elif isinstance(geometry, MultiLineString):
            modified_multiline_coords = []
            for linestring in geometry:
                coords = list(linestring.coords)
                modified_coords = [(x + random.uniform(-tolerance, tolerance), y + random.uniform(-tolerance, tolerance)) for x, y in coords]
                modified_multiline_coords.append(modified_coords)
            modified_geoms.append(MultiLineString(modified_multiline_coords))

    # Update the geometry column in the filtered rows
    gdf.loc[lines.index, 'geometry'] = modified_geoms

    return gdf
################

def convert_kml_to_geojson():
    st.header("Convert KML to GeoJSON")

    uploaded_file = st.file_uploader("Choose a KML file", type="kml")
    if uploaded_file:
        geojson_data = kml_to_geojson(uploaded_file)

        # Convert the GeoJSON data to a GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geojson_data["features"])
        
        # Check if the geometry type is LineString or MultiLineString
        if any(gdf["geometry"].geom_type.isin(["LineString", "MultiLineString"])):
            # Alter the geometry with the provided function
            gdf = make_random_changes_from_file(gdf)

        # Extract the file name without the extension and keep the spaces
        file_name_without_extension = os.path.splitext(uploaded_file.name)[0]

        # Add the 'Name' column to the GeoDataFrame
        gdf['Name'] = file_name_without_extension
        
        # Convert the modified GeoDataFrame back to GeoJSON
        geojson_data = json.loads(gdf.to_json())

        # Convert GeoJSON data to a string and then encode it
        geojson_str = json.dumps(geojson_data)
        geojson_bytes = geojson_str.encode('utf-8')
        
        # Use BytesIO to hold the byte data
        buffer = BytesIO()
        buffer.write(geojson_bytes)
        buffer.seek(0)
        
        # Create a download link for the GeoJSON data
        fname = file_name_without_extension + ".geojson"
        st.markdown(
            f"<a href='data:application/json;charset=utf-8;,{geojson_str}' download='{fname}'>Click here to download the modified GeoJSON file</a>",
            unsafe_allow_html=True
        )

    if st.button('Back to Home'):
        st.session_state.operation = None
        st.experimental_rerun()


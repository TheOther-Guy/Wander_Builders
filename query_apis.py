import streamlit as st
import requests
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, MultiLineString, Point, shape
import json
from datetime import datetime
from io import BytesIO

def query_apis_page():
    st.title("Query APIs")

    api_choice = st.selectbox(
        "Select API to Query:",
        ("Greenways API", "Multi Use Paths API", "Parks and Facilities API")
    )

    layer_id = st.text_input("Enter Layer ID:", value="0")

    if api_choice == "Greenways API":
        endpoint = f"https://twfgis.wakeforestnc.gov/server/rest/services/Greenways_Wake_Forest/MapServer/{layer_id}/query"
        dissolve_column = "Name"
    elif api_choice == "Multi Use Paths API":
        endpoint = f"https://twfgis.wakeforestnc.gov/server/rest/services/MultiUsePath/MapServer/{layer_id}/query"
        dissolve_column = "Street"
    elif api_choice == "Parks and Facilities API":
        endpoint = f"https://twfgis.wakeforestnc.gov/server/rest/services/ParksAndFacilities/MapServer/{layer_id}/query"
        dissolve_column = None  # No dissolve for point data

    params = {
        "where": "1=1",
        "outFields": "*",
        "f": "json"
    }

    if st.button("Query API"):
        data = query_api(endpoint, params)
        if data:
            st.success("API queried successfully!")

            features = data['features']
            geometries = []
            attributes = []
            spatial_ref = None

            if 'spatialReference' in data:
                spatial_ref = data['spatialReference']['latestWkid']
            else:
                if 'features' in data and data['features']:
                    spatial_ref = data['features'][0]['geometry'].get('spatialReference', {}).get('latestWkid', None)
            
            for feature in features:
                geom = feature['geometry']
                
                if geom is None:
                    continue
                
                try:
                    if 'paths' in geom:
                        geom_geojson = convert_arcgis_paths_to_geojson(geom)
                    elif 'x' in geom and 'y' in geom:  # Point data for Parks and Facilities API
                        geom_geojson = Point(geom['x'], geom['y'])
                    else:
                        geom_geojson = shape(geom)
                    
                    shapely_geom = shape(geom_geojson)
                    geometries.append(shapely_geom)
                    attributes.append(feature['attributes'])
                except Exception as e:
                    st.warning(f"Skipping a feature due to geometry processing error: {e}")
                    continue

            st.write(f"Number of geometries: {len(geometries)}")
            st.write(f"Number of attributes: {len(attributes)}")

            df = pd.DataFrame(attributes)

            if dissolve_column:
                mask = df[dissolve_column].notna()
                df = df[mask]
                geometries = [geometry for i, geometry in enumerate(geometries) if mask.iloc[i]]

            if len(df) != len(geometries):
                st.error("Mismatch between number of geometries and attributes after processing. Please check the data.")
                return

            gdf = gpd.GeoDataFrame(df, geometry=geometries)

            if spatial_ref:
                gdf.set_crs(epsg=spatial_ref, inplace=True)

            if dissolve_column and dissolve_column in df.columns:
                dissolved_gdf = gdf.dissolve(by=dissolve_column, aggfunc='first')
                dissolved_gdf.reset_index(inplace=True)
            else:
                dissolved_gdf = gdf

            if dissolve_column:
                dissolved_gdf.rename(columns={dissolve_column: 'name'}, inplace=True)
                dissolved_gdf['name'] = dissolved_gdf['name'].str.lower()
                non_logical_names = [
                    "no name trail", "unknown", "no name", "null", "undefined", 
                    "trail", "n/a", "na", "-", "", None
                ]
                dissolved_gdf = dissolved_gdf[~dissolved_gdf['name'].isin(non_logical_names)]
                dissolved_gdf['far_splitted'] = dissolved_gdf['geometry'].apply(check_far_splitted)

            dissolved_gdf = dissolved_gdf.to_crs(epsg=4326)

            # making name titles --> capitalizing each word
            dissolved_gdf['name'] = dissolved_gdf['name'].str.title()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = f"{api_choice.replace(' ', '_').lower()}_{timestamp}.xlsx"
            geojson_filename = f"{api_choice.replace(' ', '_').lower()}_{timestamp}.geojson"

            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                dissolved_gdf.to_excel(writer, index=False, sheet_name='Sheet1')

            output.seek(0)

            st.download_button(
                label="Download as Excel",
                data=output,
                file_name=excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            geojson = dissolved_gdf.to_json()
            st.download_button(
                label="Download as GeoJSON",
                data=geojson,
                file_name=geojson_filename,
                mime="application/json"
            )

    if st.button("Back to Home"):
        st.session_state.operation = None
        st.experimental_rerun()

def query_api(url, params):
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error querying API: {response.status_code}")
        return None

def convert_arcgis_paths_to_geojson(arcgis_geom):
    paths = arcgis_geom.get('paths', [])
    if len(paths) == 1:
        geojson_geom = LineString(paths[0])
    else:
        geojson_geom = MultiLineString(paths)
    return geojson_geom

def check_far_splitted(geometry):
    if isinstance(geometry, MultiLineString):
        segments = list(geometry.geoms)  # Correctly retrieve the individual LineStrings
        for i in range(len(segments) - 1):
            # Calculate the distance between the end of the current segment and the start of the next
            distance = Point(segments[i].coords[-1]).distance(Point(segments[i+1].coords[0]))
            if distance > 50:  # Check if the distance is greater than 50 meters
                return 'yes'
    return 'no'

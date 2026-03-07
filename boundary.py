import streamlit as st
import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt

def display_boundary_page():
    st.title('Get Boundary')

    def get_geometry(address):
        city = ox.geocode_to_gdf(address)
        multipolygon = city.geometry.iloc[0]
        coordinates = []

        if multipolygon.geom_type == 'Polygon':
            coordinates = [list(coord) for coord in multipolygon.exterior.coords]
        elif multipolygon.geom_type == 'MultiPolygon':
            for polygon in multipolygon:
                coordinates.extend([list(coord) for coord in polygon.exterior.coords])
        else:
            raise ValueError("Unsupported geometry type: {}".format(multipolygon.geom_type))
        
        return coordinates, multipolygon

    def plot_polygon(coordinates, multipolygon):
        fig, ax = plt.subplots()

        # Plot polygon
        polygon_gdf = gpd.GeoDataFrame(index=[0], geometry=[multipolygon])
        polygon_gdf.plot(ax=ax, color='blue')

        # Plot centroid
        centroid = multipolygon.centroid
        ax.plot(centroid.x, centroid.y, 'ro')

        plt.title('Polygon')
        st.pyplot(fig)

    st.header("Enter an address to get its boundary")

    address = st.text_input("Enter an address:")

    coordinates = None
    multipolygon = None

    if st.button('Plot'):
        try:
            coordinates, multipolygon = get_geometry(address)
            plot_polygon(coordinates, multipolygon)
            st.text("Geometry:")
            st.text_area("", value=str(coordinates), height=150)
            st.session_state['multipolygon'] = multipolygon
        except Exception as e:
            st.error("An error occurred while retrieving the boundary:")
            st.error(e)

    if st.button("Back to Home"):
        st.session_state.operation = None
        st.experimental_rerun()

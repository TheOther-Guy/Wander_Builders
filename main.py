import streamlit as st
from boundary import display_boundary_page
from convert_kml import convert_kml_to_geojson
from search_pois import search_pois
from geocoding import geocoding_page
from query_apis import query_apis_page
from crm_query_interface import crm_query_interface

def main():
    st.title("Wander Builders")

    def choose_operation():
        st.write("Choose Operation from the Sidebar")
        with st.sidebar:
            if st.button("Get Boundary", key='get_boundary'):
                st.session_state.operation = "boundary"
                st.experimental_rerun()
            elif st.button("Convert KML to GeoJSON", key='convert_kml'):
                st.session_state.operation = "convert_kml"
                st.experimental_rerun()
            elif st.button("Search POIs", key='search_pois'):
                st.session_state.operation = "search_pois"
                st.experimental_rerun()
            elif st.button("Geocoding & Reverse Geocoding", key='geocoding'):
                st.session_state.operation = "geocoding"
                st.experimental_rerun()
            elif st.button("Query APIs", key='query_apis'):
                st.session_state.operation = "query_apis"
                st.experimental_rerun()
            elif st.button("CRM API Query Interface", key='crm_query'):
                st.session_state.operation = "crm_query"
                st.experimental_rerun()

    if "operation" not in st.session_state:
        st.session_state.operation = None

    if st.session_state.operation == "boundary":
        display_boundary_page()
    elif st.session_state.operation == "convert_kml":
        convert_kml_to_geojson()
    elif st.session_state.operation == "search_pois":
        search_pois()
    elif st.session_state.operation == "geocoding":
        geocoding_page()
    elif st.session_state.operation == "query_apis":
        query_apis_page()
    elif st.session_state.operation == "crm_query":
        crm_query_interface()
    else:
        choose_operation()

if __name__ == "__main__":
    main()

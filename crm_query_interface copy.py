import streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO

def crm_query_interface():
    st.title("CRM API Query Interface")

    # Display radio buttons for available methods (single selection)
    query_type = st.radio(
        "Select the type of query you want to perform:",
        (
            "Get All Listings (getListings)",
            "Filter by Listing ID (getListing)"
            # "Get Listing Types",
            # "Get Listing Regions",
            # "Get Listing Amenities",
            # "Get Listing Categories"
        )
    )

    # Depending on the selected method, show relevant filters
    listing_id = None
    if query_type == "Filter by Listing ID (getListing)":
        st.subheader("Filter by Listing ID (getListing)")
        listing_id = st.text_input("Enter Listing ID")

    # Button to execute the selected query
    if st.button("Query CRM API"):
        if query_type == "Get All Listings (getListings)":
            query_get_listings()
        elif query_type == "Filter by Listing ID (getListing)":
            if listing_id:
                query_get_listing(listing_id)
            else:
                st.warning("Please enter a Listing ID.")
        # elif query_type == "Get Listing Types":
        #     query_get_listing_types()
        # elif query_type == "Get Listing Regions":
        #     query_get_listing_regions()
        # elif query_type == "Get Listing Amenities":
        #     query_get_listing_amenities()
        # elif query_type == "Get Listing Categories":
        #     query_get_listing_cats()

    if st.button("Back to Home"):
        st.session_state.operation = None
        st.experimental_rerun()

def query_get_listings():
    url = "https://raleigh.simpleviewcrm.com/webapi/listings/xml/listings.cfm"
    params = {
        'USERNAME': "WonderMaps_CRMapi",
        'PASSWORD': "api^m@ps1",
        'ACTION': "getListings",
        'PAGENUM': 1,
        'PAGESIZE': 50
    }

    all_listings = []
    total_pages = None

    # Initialize a placeholder for dynamically updating the page number
    progress_text = st.empty()

    while True:
        response = requests.post(url, data=params)
        if response.status_code == 200:
            root = ET.fromstring(response.text)

            # Retrieve total results count and calculate total pages (if not done already)
            if total_pages is None:
                total_results = int(root.find(".//RESULTS").text)
                total_pages = (total_results // params['PAGESIZE']) + 1
                st.write(f"Total Results: {total_results}, Total Pages: {total_pages}")

            # Iterate over each LISTING element
            for listing in root.findall(".//LISTING"):
                listing_data = {}

                # Iterate through each field in the listing and store it in a dictionary
                for child in listing:
                    listing_data[child.tag] = child.text  # Use the tag as the column name

                # Append the complete listing data to the list
                all_listings.append(listing_data)

            # Update the dynamic statement to track page number
            progress_text.text(f"Retrieving page {params['PAGENUM']} of {total_pages}...")

            # Break the loop if we've retrieved all pages
            if params['PAGENUM'] >= total_pages:
                break

            # Move to the next page
            params['PAGENUM'] += 1

        else:
            st.error(f"Error querying API: {response.status_code}")
            return

    # Clear the progress text when done
    progress_text.text("All pages retrieved.")

    # Convert the list of dictionaries (all_listings) into a DataFrame
    df = pd.DataFrame(all_listings)
    st.write(df)

    csv = df.to_csv(index=False)
    st.download_button("Download CSV", csv, file_name="all_listings.csv")

def query_get_listing(listing_id):
    url = "https://raleigh.simpleviewcrm.com/webapi/listings/xml/listings.cfm"
    params = {
        'USERNAME': "WonderMaps_CRMapi",
        'PASSWORD': "api^m@ps1",
        'ACTION': "getListing",
        'LISTINGID': listing_id
    }

    response = requests.post(url, data=params)

    if response.status_code == 200:
        root = ET.fromstring(response.text)
        listing = root.find(".//LISTING")

        if listing is not None:
            listing_data = {}

            # Iterate through each field in the listing and store it in a dictionary
            for child in listing:
                listing_data[child.tag] = child.text  # Use the tag as the column name

            df = pd.DataFrame([listing_data])
            st.write(df)

            csv = df.to_csv(index=False)
            st.download_button("Download CSV", csv, file_name=f"listing_{listing_id}.csv")
        else:
            st.warning(f"No listing found for Listing ID: {listing_id}")
    else:
        st.error(f"Error querying API: {response.status_code}")

# The following functions are commented out as the endpoints are currently unavailable
# def query_get_listing_types():
#     # Implementation for querying listing types

# def query_get_listing_regions():
#     # Implementation for querying listing regions

# def query_get_listing_amenities():
#     # Implementation for querying listing amenities

# def query_get_listing_cats():
#     # Implementation for querying listing categories

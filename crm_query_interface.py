import streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from google.cloud import storage
import os
from datetime import datetime
from tzlocal import get_localzone

def upload_to_gcs(file_data, api_name, bucket_name, folder_name):
    try:
        # Initialize Google Cloud Storage client
        client = storage.Client.from_service_account_json("wander-production-308019-9da7883cc4cc.json")

        # Get the bucket
        st.write(f"Connecting to Google Cloud bucket: {bucket_name}")
        bucket = client.bucket(bucket_name)

        if not bucket.exists():
            st.error(f"Bucket {bucket_name} does not exist!")
            return

        st.write(f"Connected to bucket {bucket_name}.")

        # Check if the folder exists by listing blobs
        blobs = bucket.list_blobs(prefix=folder_name + '/')
        if not any(blobs):
            st.write(f"Folder '{folder_name}' does not exist, creating it.")
            blob = bucket.blob(folder_name + '/')
            blob.upload_from_string('')
            st.write(f"Folder '{folder_name}' created.")
        else:
            st.write(f"Folder '{folder_name}' already exists.")

        # Get the local time zone
        local_tz = get_localzone()

        # Get current time with the local time zone
        now_with_timezone = datetime.now(local_tz)

        # Format the timestamp as: yyyymmdd_hhmm_tz
        formatted_timestamp = now_with_timezone.strftime('%Y%m%d_%H%M_%Z').lower()

        # Create the file name
        file_name = f"{api_name}_cleaned_{formatted_timestamp}.csv"

        # Define the destination path (folder + file name)
        destination_blob_name = f"{folder_name}/{file_name}"

        # Create a new blob and upload the file
        st.write(f"Uploading file '{file_name}' to Google Cloud Storage...")
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(file_data)

        st.success(f"File '{file_name}' uploaded successfully to Google Cloud Storage!")
    except Exception as e:
        st.error(f"Failed to upload '{file_name}' to Google Cloud Storage: {str(e)}")




def crm_query_interface():
    st.title("CRM API Query Interface")

    # Display radio buttons for available methods (single selection)
    query_type = st.radio(
        "Select the type of query you want to perform:",
        (
            "Get All Listings (getListings)",
            "Filter by Listing ID (getListing)"
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

    # Placeholder to update page number dynamically
    progress_text = st.empty()

    while True:
        response = requests.post(url, data=params)
        if response.status_code == 200:
            root = ET.fromstring(response.text)

            # Retrieve total results count and calculate total pages
            if total_pages is None:
                total_results = int(root.find(".//RESULTS").text)
                total_pages = (total_results // params['PAGESIZE']) + 1
                st.write(f"Total Results: {total_results}, Total Pages: {total_pages}")

            # Iterate over each LISTING element
            for listing in root.findall(".//LISTING"):
                listing_data = {}
                for child in listing:
                    listing_data[child.tag] = child.text
                all_listings.append(listing_data)

            # Update the progress text
            progress_text.text(f"Retrieving page {params['PAGENUM']} of {total_pages}...")

            if params['PAGENUM'] >= total_pages:
                break
            params['PAGENUM'] += 1
        else:
            st.error(f"Error querying API: {response.status_code}")
            return

    # Convert listings to DataFrame
    df = pd.DataFrame(all_listings)
    st.write(df)

    # Save the DataFrame as CSV string
    csv_data = df.to_csv(index=False)

    # Create a timestamp for the file name
    local_tz = get_localzone()
    now_with_timezone = datetime.now(local_tz)
    formatted_timestamp = now_with_timezone.strftime('%A_%y-%b-%d_%H-%M_%Z').lower()

    # Create the file name starting with "getlistings"
    file_name = f"getlistings_{formatted_timestamp}.csv"

    # Upload to Google Cloud Storage
    upload_to_gcs(csv_data, file_name, bucket_name="raleigh-wander", folder_name="cleaned")

    # Provide download button for CSV
    st.download_button("Download CSV", csv_data, file_name=file_name)



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
            for child in listing:
                listing_data[child.tag] = child.text

            df = pd.DataFrame([listing_data])
            st.write(df)

            csv_data = df.to_csv(index=False)

            # Create a timestamp for the file name
            local_tz = get_localzone()
            now_with_timezone = datetime.now(local_tz)
            formatted_timestamp = now_with_timezone.strftime('%A_%y-%b-%d_%H-%M_%Z').lower()

            # Create the file name starting with "getlisting"
            file_name = f"getlisting_{listing_id}_{formatted_timestamp}.csv"

            # Upload to Google Cloud Storage
            upload_to_gcs(csv_data, file_name, bucket_name="raleigh-wander", folder_name="cleaned")

            st.download_button("Download CSV", csv_data, file_name=file_name)
        else:
            st.warning(f"No listing found for Listing ID: {listing_id}")
    else:
        st.error(f"Error querying API: {response.status_code}")



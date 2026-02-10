import requests
import json
import os

def fetch_roam_file(local_api_port, graph_name, file_url, output_path):
    """
    Fetches a file from Roam Research via the Local API (handles decryption).
    
    Args:
        local_api_port (int): The port shown in Roam Desktop > Settings > Local API.
        graph_name (str): The name of your Roam graph.
        file_url (str): The Firebase storage URL (e.g., https://firebasestorage...).
        output_path (str): Where to save the decrypted file.
    """
    
    # The Local API endpoint for file fetching
    # Note: The exact path may vary slightly based on version, but typically follows this structure
    api_endpoint = f"http://127.0.0.1:{local_api_port}/api/{graph_name}"

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "action": "file.get",
        "args": [
            {
                "url" : file_url
            }
        ]
    }

    print(f"Requesting file from: {api_endpoint}")
    
    try:
        # The Local API expects a POST request with the file URL
        response = requests.post(api_endpoint, json=payload, headers=headers, stream=True)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Success! File saved to: {output_path}")
        else:
            print(f"Error: Failed to fetch file. Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Roam Local API. Is the Roam Desktop App running and Local API enabled?")

# --- Configuration ---
# 1. Open Roam Desktop -> Settings -> Graph -> Local API to find your PORT.
PORT = 3333 # Replace with your actual port
GRAPH = "SCFH" 
# 2. The URL usually found in a block like ![](https://firebasestorage...)
FILE_URL = "https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2FSCFH%2F-9owRBegJ8.jpeg.enc?alt=media&token=9b673aae-8089-4a91-84df-9dac152a7f94"
OUTPUT_FILE = "downloaded_image.png"

# --- Execute ---
if __name__ == "__main__":
    fetch_roam_file(PORT, GRAPH, FILE_URL, OUTPUT_FILE)
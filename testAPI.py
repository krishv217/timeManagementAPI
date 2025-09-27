import requests
import json

url = "https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app/schedule"
payload = {"text": "I have a meeting at 2pm and need to go to the gym"}

try:
    response = requests.post(url, json=payload)
    response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

    # Assuming the API returns JSON
    print("Success! Response from /schedule:")
    print(json.dumps(response.json(), indent=4))

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

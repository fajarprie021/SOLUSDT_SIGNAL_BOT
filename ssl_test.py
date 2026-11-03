import requests
import certifi
import socket
import ssl

url = "https://fapi.binance.com/fapi/v1/ping"

print("Testing Binance SSL Connection...")
print("Certifi:", certifi.where())

try:
    response = requests.get(
        url,
        timeout=15,
        verify=certifi.where()
    )

    print("HTTP Status:", response.status_code)
    print("Response:", response.text)
    print("SSL CONNECTION SUCCESS")

except requests.exceptions.SSLError as e:
    print("SSL ERROR:", e)

except requests.exceptions.RequestException as e:
    print("CONNECTION ERROR:", e)
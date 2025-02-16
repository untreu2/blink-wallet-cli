import os
import requests
from dotenv import load_dotenv

load_dotenv()
auth_token = os.getenv("API_KEY")

minor_unit_mapping = {
    "USD": 100,
    "EUR": 100,
    "GBP": 100,
    "TRY": 100,
}

def convert_satoshi(satoshi_amount, currency):
    currency = currency.upper()
    if currency == "BTC":
        btc_amount = satoshi_amount / 1e8
        print(f"{satoshi_amount:.0f} satoshi is equal to {btc_amount:.8f} BTC.")
        return

    url = "https://api.staging.blink.sv/graphql"
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": auth_token,
    }
    query = """
    query realtimePrice($currency: DisplayCurrency) {
      realtimePrice(currency: $currency) {
        btcSatPrice {
          base
          offset
        }
        denominatorCurrencyDetails {
          symbol
        }
      }
    }
    """
    variables = {"currency": currency}

    try:
        response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    except requests.RequestException as e:
        print("Error during API request:", e)
        return

    if response.status_code != 200:
        print("Request failed with status code:", response.status_code)
        print("Response:", response.text)
        return

    try:
        data = response.json()
    except ValueError:
        print("Failed to parse JSON response.")
        return

    realtime_price = data.get("data", {}).get("realtimePrice")
    if realtime_price is None:
        print("Unexpected response format:", data)
        return

    btc_sat_price = realtime_price.get("btcSatPrice")
    if btc_sat_price is None or btc_sat_price.get("base") is None or btc_sat_price.get("offset") is None:
        print("Failed to retrieve satoshi price information.")
        return

    try:
        base = float(btc_sat_price["base"])
        offset = int(btc_sat_price["offset"])
    except (ValueError, TypeError):
        print("Price information is not in the expected format.")
        return

    price_per_sat_minor = base / (10 ** offset)
    divisor = minor_unit_mapping.get(currency, 100)
    price_per_sat = price_per_sat_minor / divisor

    converted_value = satoshi_amount * price_per_sat
    symbol = realtime_price.get("denominatorCurrencyDetails", {}).get("symbol", currency)
    print(f"{satoshi_amount:.0f} satoshi is approximately {symbol}{converted_value:.2f} {currency}.")

if __name__ == "__main__":
    try:
        satoshi_input = float(input("Enter satoshi amount: "))
    except ValueError:
        print("Invalid number.")
        exit(1)

    currency_input = input("Enter target currency (e.g. BTC, USD, GBP, EUR, TRY): ").strip().upper()
    if not currency_input:
        print("No valid currency code provided.")
        exit(1)

    convert_satoshi(satoshi_input, currency_input)

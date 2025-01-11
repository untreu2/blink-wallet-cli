import os
from dotenv import load_dotenv
import requests

load_dotenv()
auth_token = os.getenv("API_KEY")

def get_btc_balance(auth_token):
    url = "https://api.blink.sv/graphql"
    headers = {
        "content-type": "application/json",
        "X-API-KEY": auth_token,
    }

    query = """
    query Me {
      me {
        defaultAccount {
          wallets {
            walletCurrency
            balance
          }
        }
      }
    }
    """

    response = requests.post(url, json={"query": query}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        wallets = data["data"]["me"]["defaultAccount"]["wallets"]
        for wallet in wallets:
            if wallet["walletCurrency"] == "BTC":
                return wallet["balance"]
        print("BTC wallet not found.")
        return None
    else:
        print("Failed to fetch balances. Status code:", response.status_code)
        print("Response:", response.text)
        return None

btc_balance = get_btc_balance(auth_token)
if btc_balance is not None:
    print(f"Your BTC balance: {btc_balance} satoshis")

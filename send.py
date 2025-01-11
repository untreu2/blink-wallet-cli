import os
from dotenv import load_dotenv
import requests

load_dotenv()
auth_token = os.getenv("API_KEY")

def get_wallet_id(auth_token):
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
            id
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
                return wallet["id"]
        print("BTC wallet not found.")
        return None
    else:
        print("Failed to fetch wallet ID. Status code:", response.status_code)
        print("Response:", response.text)
        return None

def pay_invoice(auth_token, wallet_id, payment_request):
    url = "https://api.blink.sv/graphql"
    headers = {
        "content-type": "application/json",
        "X-API-KEY": auth_token,
    }

    query = """
    mutation LnInvoicePaymentSend($input: LnInvoicePaymentInput!) {
      lnInvoicePaymentSend(input: $input) {
        status
        errors {
          message
          path
          code
        }
      }
    }
    """

    variables = {
        "input": {
            "paymentRequest": payment_request,
            "walletId": wallet_id
        }
    }

    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data["data"]["lnInvoicePaymentSend"]["errors"]:
            print("Errors:", data["data"]["lnInvoicePaymentSend"]["errors"])
        else:
            print("Payment Status:", data["data"]["lnInvoicePaymentSend"]["status"])
    else:
        print("Failed to send payment. Status code:", response.status_code)
        print("Response:", response.text)

def pay_lnurl(auth_token, wallet_id, lnurl, amount_satoshis):
    url = "https://api.blink.sv/graphql"
    headers = {
        "content-type": "application/json",
        "X-API-KEY": auth_token,
    }

    query = """
    mutation LnurlPaymentSend($input: LnurlPaymentSendInput!) {
      lnurlPaymentSend(input: $input) {
        status
        errors {
          code
          message
          path
        }
      }
    }
    """

    variables = {
        "input": {
            "walletId": wallet_id,
            "amount": amount_satoshis,
            "lnurl": lnurl
        }
    }

    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data["data"]["lnurlPaymentSend"]["errors"]:
            print("Errors:", data["data"]["lnurlPaymentSend"]["errors"])
        else:
            print("Payment Status:", data["data"]["lnurlPaymentSend"]["status"])
    else:
        print("Failed to send payment. Status code:", response.status_code)
        print("Response:", response.text)

wallet_id = get_wallet_id(auth_token)
if wallet_id:
    print("Choose payment method:")
    print("1. Pay Lightning Invoice")
    print("2. Pay LNURL")
    choice = input("Enter your choice (1 or 2): ")

    if choice == "1":
        payment_request = input("Enter the Lightning Invoice: ")
        pay_invoice(auth_token, wallet_id, payment_request)
    elif choice == "2":
        lnurl = input("Enter the LNURL: ")
        amount_satoshis = int(input("Enter the amount in satoshis: "))
        pay_lnurl(auth_token, wallet_id, lnurl, amount_satoshis)
    else:
        print("Invalid choice. Please enter 1 or 2.")

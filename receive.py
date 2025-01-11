import os
from dotenv import load_dotenv
import requests
import qrcode

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

def create_lightning_invoice(auth_token, wallet_id, amount_satoshis):
    url = "https://api.blink.sv/graphql"
    
    headers = {
        "content-type": "application/json",
        "X-API-KEY": auth_token,
    }

    query = """
    mutation LnInvoiceCreate($input: LnInvoiceCreateInput!) {
        lnInvoiceCreate(input: $input) {
            invoice {
                paymentRequest
                paymentHash
                paymentSecret
                satoshis
            }
            errors {
                message
            }
        }
    }
    """

    variables = {
        "input": {
            "amount": amount_satoshis,
            "walletId": wallet_id
        }
    }

    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if "errors" in data["data"]["lnInvoiceCreate"] and data["data"]["lnInvoiceCreate"]["errors"]:
            print("Error:", data["data"]["lnInvoiceCreate"]["errors"])
        else:
            return data["data"]["lnInvoiceCreate"]["invoice"]
    else:
        print("Failed to connect to API. Status code:", response.status_code)
        print("Response:", response.text)
        return None

def display_qr_code(payment_request):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(payment_request)
    qr.make(fit=True)

    img = qr.make_image(fill="black", back_color="white")
    img.show()

wallet_id = get_wallet_id(auth_token)
if wallet_id:
    amount_satoshis = int(input("Enter the amount in satoshis: "))
    invoice = create_lightning_invoice(auth_token, wallet_id, amount_satoshis)

    if invoice:
        print("Invoice created successfully:")
        print("Payment Request:", invoice["paymentRequest"])
        print("Payment Hash:", invoice["paymentHash"])
        print("Payment Secret:", invoice["paymentSecret"])
        print("Satoshis:", invoice["satoshis"])

        display_qr_code(invoice["paymentRequest"])

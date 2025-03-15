import os
from dotenv import load_dotenv
import requests
from urllib.parse import urlparse, urlunparse, urlencode, parse_qsl

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

def probe_invoice_fee(auth_token, wallet_id, payment_request):
    url = "https://api.blink.sv/graphql"
    headers = {
        "content-type": "application/json",
        "X-API-KEY": auth_token,
    }
    query = """
    mutation lnInvoiceFeeProbe($input: LnInvoiceFeeProbeInput!) {
      lnInvoiceFeeProbe(input: $input) {
        errors {
          message
        }
        amount
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
        result = data["data"]["lnInvoiceFeeProbe"]
        if result["errors"]:
            print("Fee probe errors:", result["errors"])
            return None
        else:
            fee_amount = result["amount"]
            return fee_amount
    else:
        print("Failed to probe invoice fee. Status code:", response.status_code)
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
        result = data["data"]["lnInvoicePaymentSend"]
        if result["errors"]:
            print("Payment errors:", result["errors"])
        else:
            print("Payment status:", result["status"])
    else:
        print("Failed to send payment. Status code:", response.status_code)
        print("Response:", response.text)

def create_ln_invoice(amount_satoshis, lnurl, memo):
    msat = amount_satoshis * 1000
    if "@" in lnurl:
        user, domain = lnurl.split("@", 1)
        lnurlp = f"https://{domain}/.well-known/lnurlp/{user}"
    else:
        lnurlp = lnurl
    response = requests.get(lnurlp)
    if response.status_code != 200:
        raise Exception(f"Could not fetch LNURL-pay info: {response.status_code}")
    lnurl_data = response.json()
    min_sendable = lnurl_data.get("minSendable", 0)
    max_sendable = lnurl_data.get("maxSendable", 0)
    if msat < min_sendable or msat > max_sendable:
        raise Exception(f"Amount out of range. Minimum {min_sendable // 1000} and maximum {max_sendable // 1000} satoshis allowed.")
    callback_url = lnurl_data.get("callback")
    if not callback_url:
        raise Exception("LNURL-pay info does not contain a callback URL")
    parsed_url = urlparse(callback_url)
    query_params = dict(parse_qsl(parsed_url.query))
    query_params["amount"] = str(msat)
    comment_allowed = lnurl_data.get("commentAllowed", 0)
    if comment_allowed > 0:
        if len(memo) > comment_allowed:
            memo = memo[:comment_allowed]
        query_params["comment"] = memo
    new_query = urlencode(query_params)
    new_callback_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        parsed_url.params,
        new_query,
        parsed_url.fragment
    ))
    invoice_response = requests.get(new_callback_url)
    if invoice_response.status_code != 200:
        raise Exception(f"Failed to fetch invoice: {invoice_response.status_code}")
    invoice_data = invoice_response.json()
    if invoice_data.get("status", "").lower() == "error":
        raise Exception(f"Invoice error: {invoice_data.get('reason', 'Unknown error')}")
    invoice = invoice_data.get("pr")
    if not invoice:
        raise Exception("No invoice found in response")
    return invoice

if __name__ == "__main__":
    wallet_id = get_wallet_id(auth_token)
    if wallet_id:
        print("Choose payment method:")
        print("1. Lightning Invoice Payment")
        print("2. LNURL Payment")
        choice = input("Enter your choice (1 or 2): ")
        if choice == "1":
            payment_request = input("Enter the Lightning Invoice: ")
            fee = probe_invoice_fee(auth_token, wallet_id, payment_request)
            if fee is not None:
                print(f"Invoice fee: {fee} satoshi")
                confirm = input("Do you want to proceed with the payment? (y/n): ")
                if confirm.lower() == "y":
                    pay_invoice(auth_token, wallet_id, payment_request)
                else:
                    print("Payment canceled.")
            else:
                print("Invoice fee could not be retrieved. Payment aborted.")
        elif choice == "2":
            lnurl = input("Enter the LNURL: ")
            try:
                amount_satoshis = int(input("Enter the amount in SATS: "))
            except ValueError:
                print("Invalid amount. Please enter an integer.")
            else:
                memo = input("Enter memo for LN invoice: ")
                try:
                    ln_invoice = create_ln_invoice(amount_satoshis, lnurl, memo)
                    print("Created LN invoice:", ln_invoice)
                    fee = probe_invoice_fee(auth_token, wallet_id, ln_invoice)
                    if fee is not None:
                        print(f"Invoice fee: {fee} satoshi")
                        confirm = input("Do you want to proceed with the payment? (y/n): ")
                        if confirm.lower() == "y":
                            pay_invoice(auth_token, wallet_id, ln_invoice)
                        else:
                            print("Payment canceled.")
                    else:
                        print("Invoice fee could not be retrieved. Payment aborted.")
                except Exception as e:
                    print("Error creating LN invoice:", str(e))
        else:
            print("Invalid choice. Please enter 1 or 2.")

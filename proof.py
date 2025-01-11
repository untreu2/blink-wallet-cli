import os
from dotenv import load_dotenv
import requests

load_dotenv()
auth_token = os.getenv("API_KEY")

def check_payment_status(auth_token, payment_request):
    url = "https://api.blink.sv/graphql"
    headers = {
        "content-type": "application/json",
        "X-API-KEY": auth_token,
    }

    query = """
    query PaymentsWithProof($first: Int) {
      me {
        defaultAccount {
          transactions(first: $first) {
            edges {
              node {
                initiationVia {
                  ... on InitiationViaLn {
                    paymentRequest
                    paymentHash
                  }
                }
                settlementVia {
                  ... on SettlementViaIntraLedger {
                    preImage
                  }
                  ... on SettlementViaLn {
                    preImage
                  }
                }
                settlementAmount
                status
              }
            }
          }
        }
      }
    }
    """

    variables = {"first": 10}

    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        transactions = data["data"]["me"]["defaultAccount"]["transactions"]["edges"]
        for transaction in transactions:
            txn_payment_request = transaction["node"]["initiationVia"].get("paymentRequest", "N/A")
            if txn_payment_request == payment_request:
                settlement_amount = transaction["node"].get("settlementAmount", "N/A")
                status = transaction["node"].get("status", "N/A")
                print(f"Amount (satoshis): {settlement_amount}")
                print(f"Status: {status}")
                return
        print("No matching transaction found for the provided payment request.")
    else:
        print("Failed to fetch transactions. Status code:", response.status_code)
        print("Response:", response.text)

payment_request = input("Enter the Lightning Invoice: ")
check_payment_status(auth_token, payment_request)

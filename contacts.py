import os
from dotenv import load_dotenv
import requests

load_dotenv()
API_KEY = os.getenv("API_KEY")
GRAPHQL_URL = "https://api.blink.sv/graphql"

def get_contact_list(api_key):
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": api_key
    }
    query = """
    query {
      me {
        contacts {
          username
          alias
          transactionsCount
        }
      }
    }
    """
    response = requests.post(GRAPHQL_URL, json={"query": query}, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("data", {}).get("me", {}).get("contacts", [])
    else:
        print("Error fetching contact list. Status code:", response.status_code)
        print("Response:", response.text)
        return []

def get_contact_details(api_key, username):
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": api_key
    }
    query = """
    query GetContactDetails($username: Username!) {
      me {
        contactByUsername(username: $username) {
          username
          alias
        }
      }
    }
    """
    variables = {"username": username}
    response = requests.post(GRAPHQL_URL, json={"query": query, "variables": variables}, headers=headers)
    if response.status_code == 200:
        data = response.json()
        contact = data.get("data", {}).get("me", {}).get("contactByUsername", {})
        if contact:
            contact["lightningAddress"] = f"{contact.get('username')}@blink.sv"
        return contact
    else:
        print("Error fetching contact details. Status code:", response.status_code)
        print("Response:", response.text)
        return {}

def add_contact(api_key, username, alias):
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": api_key
    }
    mutation = """
    mutation AddContact($input: UserContactUpdateAliasInput!) {
      userContactUpdateAlias(input: $input) {
        contact {
          username
          alias
        }
        errors {
          message
        }
      }
    }
    """
    variables = {
        "input": {
            "username": username,
            "alias": alias
        }
    }
    response = requests.post(GRAPHQL_URL, json={"query": mutation, "variables": variables}, headers=headers)
    if response.status_code == 200:
        data = response.json()
        payload = data.get("data", {}).get("userContactUpdateAlias", {})
        errors = payload.get("errors")
        if errors:
            print("Error adding contact:", errors)
        else:
            contact = payload.get("contact")
            print("Contact added/updated successfully:")
            print(f"Username: {contact.get('username')}, Alias: {contact.get('alias')}")
    else:
        print("Error adding contact. Status code:", response.status_code)
        print("Response:", response.text)

def print_contact_list(contacts):
    if not contacts:
        print("No contacts found.")
        return
    print("Contact List:")
    for idx, contact in enumerate(contacts, start=1):
        username = contact.get("username")
        alias = contact.get("alias") or "None"
        print(f"{idx}. Username: {username} - Alias: {alias}")

def main():
    while True:
        print("\nMenu:")
        print("1. List Contacts")
        print("2. View Contact Details")
        print("3. Add Contact")
        print("4. Exit")
        choice = input("Enter your choice: ")
        if choice == "1":
            contacts = get_contact_list(API_KEY)
            print_contact_list(contacts)
        elif choice == "2":
            contacts = get_contact_list(API_KEY)
            if contacts:
                print_contact_list(contacts)
                try:
                    selection = int(input("Enter the number of the contact to view details: "))
                    if 1 <= selection <= len(contacts):
                        selected_username = contacts[selection - 1]["username"]
                        details = get_contact_details(API_KEY, selected_username)
                        if details:
                            print("\nContact Details:")
                            print("Username:", details.get("username"))
                            print("Alias:", details.get("alias") or "None")
                            print("Lightning Address:", details.get("lightningAddress"))
                        else:
                            print("No details found for the selected contact.")
                    else:
                        print("Invalid selection.")
                except ValueError:
                    print("Please enter a valid number.")
        elif choice == "3":
            username = input("Enter the username of the contact to add: ")
            alias = input("Enter alias for the contact: ")
            add_contact(API_KEY, username, alias)
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 4.")

if __name__ == "__main__":
    main()

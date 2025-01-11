import os
import sys
import subprocess
import importlib

def check_and_install_packages():
    """
    Checks if the required packages are installed.
    If any are missing, prompts the user to install them and restarts the script.
    """
    required_packages = {
        "dotenv": "python-dotenv",
        "requests": "requests",
        "qrcode": "qrcode",
    }

    missing_packages = []

    for module_name, package_name in required_packages.items():
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing_packages.append(package_name)

    if missing_packages:
        print("The following packages are missing:")
        for pkg in missing_packages:
            print(f"- {pkg}")
        choice = input("Would you like to install them now? (y/n): ").strip().lower()
        if choice == 'y':
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
                print("All missing packages have been installed successfully.")
                print("Restarting the script to apply changes...")
                os.execv(sys.executable, [sys.executable] + sys.argv)
            except subprocess.CalledProcessError:
                print("An error occurred while installing packages. Please install them manually.")
                sys.exit(1)
        else:
            print("Cannot proceed without installing the required packages.")
            sys.exit(1)
    else:
        print("All required packages are already installed.")

def initialize_environment():
    from dotenv import load_dotenv
    load_dotenv()
    return os.getenv("API_KEY")

def check_and_set_api_key():
    api_key = os.getenv("API_KEY")
    if not api_key or api_key.strip() == "":
        new_api_key = input("API Key missing. Please enter an API Key: ")
        update_env_file("API_KEY", new_api_key)
        print("API Key successfully updated.")
    else:
        print("API Key exists.")

def update_env_file(key, value):
    if not os.path.exists(".env"):
        with open(".env", "w") as file:
            file.write(f"{key}={value}\n")
        return

    with open(".env", "r") as file:
        lines = file.readlines()
    updated = False
    with open(".env", "w") as file:
        for line in lines:
            if line.startswith(f"{key}="):
                file.write(f"{key}={value}\n")
                updated = True
            else:
                file.write(line)
        if not updated:
            file.write(f"{key}={value}\n")

def select_operation():
    print("\nOperation options:")
    print("1. Check balance")
    print("2. Proof of Payment")
    print("3. Receive")
    print("4. Send")
    print("5. Change API Key")
    choice = input("Enter an option (1-5): ").strip()

    python_command = "python3" if sys.platform != "win32" else "python"

    if choice == "1":
        os.system(f"{python_command} balance.py")
    elif choice == "2":
        os.system(f"{python_command} proof.py")
    elif choice == "3":
        os.system(f"{python_command} receive.py")
    elif choice == "4":
        os.system(f"{python_command} send.py")
    elif choice == "5":
        new_api_key = input("Enter new API Key: ")
        update_env_file("API_KEY", new_api_key)
        print("API Key successfully updated.")
    else:
        print("Invalid selection. Please try again.")

def main():
    check_and_install_packages()

    from dotenv import load_dotenv
    import requests
    import qrcode

    auth_token = initialize_environment()

    check_and_set_api_key()

    while True:
        select_operation()
        cont = input("Would you like to perform another operation? (y/n): ").strip().lower()
        if cont != "y":
            print("Exiting...")
            break

if __name__ == "__main__":
    main()

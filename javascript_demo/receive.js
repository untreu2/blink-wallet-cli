require('dotenv').config();
const axios = require('axios');
const QRCode = require('qrcode');
const readline = require('readline');
const { exec } = require('child_process');

const authToken = process.env.API_KEY;

async function getWalletId(authToken) {
    const url = "https://api.blink.sv/graphql";

    const headers = {
        "Content-Type": "application/json",
        "X-API-KEY": authToken,
    };

    const query = `
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
    }`;

    try {
        const response = await axios.post(url, { query }, { headers });

        if (response.status === 200) {
            const wallets = response.data.data.me.defaultAccount.wallets;
            for (const wallet of wallets) {
                if (wallet.walletCurrency === "BTC") {
                    return wallet.id;
                }
            }
            console.log("BTC wallet not found.");
            return null;
        } else {
            console.error("Failed to fetch wallet ID. Status code:", response.status);
            return null;
        }
    } catch (error) {
        console.error("Error fetching wallet ID:", error.message);
        return null;
    }
}

async function createLightningInvoice(authToken, walletId, amountSatoshis, memo) {
    const url = "https://api.blink.sv/graphql";

    const headers = {
        "Content-Type": "application/json",
        "X-API-KEY": authToken,
    };

    const query = `
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
    }`;

    const variables = {
        input: {
            amount: amountSatoshis,
            walletId: walletId,
            memo: memo || "",
        }
    };

    try {
        const response = await axios.post(url, { query, variables }, { headers });

        if (response.status === 200) {
            const result = response.data.data.lnInvoiceCreate;
            if (result.errors && result.errors.length > 0) {
                console.error("Error:", result.errors);
                return null;
            } else {
                return result.invoice;
            }
        } else {
            console.error("Failed to connect to API. Status code:", response.status);
            return null;
        }
    } catch (error) {
        console.error("Error creating lightning invoice:", error.message);
        return null;
    }
}

async function displayQrCode(paymentRequest) {
    try {
        const qrDataUrl = await QRCode.toDataURL(paymentRequest);

        const base64Data = qrDataUrl.replace(/^data:image\/png;base64,/, "");
        const tempFilePath = "./temp-qr-code.png";

        require("fs").writeFileSync(tempFilePath, base64Data, "base64");

        exec(`open ${tempFilePath}`, (error) => {
            if (error) {
                console.error("Error opening the QR code:", error);
            } else {
                console.log("QR code opened successfully.");
            }
        });
    } catch (error) {
        console.error("Error generating QR code:", error);
    }
}

function askQuestion(query) {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
    });

    return new Promise((resolve) => rl.question(query, (answer) => {
        rl.close();
        resolve(answer);
    }));
}

(async function main() {
    const walletId = await getWalletId(authToken);
    if (walletId) {
        const amountInput = await askQuestion("Enter the amount in satoshis: ");
        const amountSatoshis = parseInt(amountInput, 10);

        if (isNaN(amountSatoshis)) {
            console.error("Invalid input. Please enter a numeric value.");
            return;
        }

        const memo = await askQuestion("Enter a memo for the transaction (optional): ");

        const invoice = await createLightningInvoice(authToken, walletId, amountSatoshis, memo);

        if (invoice) {
            console.log("Invoice created successfully:");
            console.log("Payment Request:", invoice.paymentRequest);
            console.log("Payment Hash:", invoice.paymentHash);
            console.log("Payment Secret:", invoice.paymentSecret);
            console.log("Satoshis:", invoice.satoshis);
            console.log("Memo:", memo);

            await displayQrCode(invoice.paymentRequest);
        }
    }
})();

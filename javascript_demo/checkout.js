require('dotenv').config();
const axios = require('axios');
const QRCode = require('qrcode');
const readline = require('readline');
const { exec } = require('child_process');
const fs = require('fs');

async function getExchangeRate(currency) {
  try {
    const response = await axios.get(`https://api.coingecko.com/api/v3/simple/price`, {
      params: {
        ids: 'bitcoin',
        vs_currencies: currency.toLowerCase(),
      },
    });
    const data = response.data;
    if (data.bitcoin && data.bitcoin[currency.toLowerCase()]) {
      return data.bitcoin[currency.toLowerCase()];
    } else {
      throw new Error(`Currency ${currency} not found.`);
    }
  } catch (error) {
    console.error("Error fetching exchange rate:", error.message);
    process.exit(1);
  }
}

async function convertToSatoshis(currency, amount) {
  const btcRate = await getExchangeRate(currency);
  const btcAmount = amount / btcRate;
  const satoshis = Math.floor(btcAmount * 1e8);
  return satoshis;
}

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

async function createLightningInvoice(authToken, walletId, amountSatoshis) {
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
    }
  `;
  const variables = {
    input: {
      amount: amountSatoshis,
      walletId: walletId
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
    fs.writeFileSync(tempFilePath, base64Data, "base64");
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

async function isInvoicePaid(authToken, paymentRequest) {
  const url = "https://api.blink.sv/graphql";
  const headers = {
    "Content-Type": "application/json",
    "X-API-KEY": authToken,
  };
  const query = `
    query PaymentsWithProof($first: Int) {
      me {
        defaultAccount {
          transactions(first: $first) {
            edges {
              node {
                initiationVia {
                  ... on InitiationViaLn {
                    paymentRequest
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
  `;
  const variables = { first: 10 };
  try {
    const response = await axios.post(url, { query, variables }, { headers });
    if (response.status === 200) {
      const transactions = response.data.data.me.defaultAccount.transactions.edges;
      for (const transaction of transactions) {
        const txnPaymentRequest = transaction.node.initiationVia?.paymentRequest || "N/A";
        if (txnPaymentRequest === paymentRequest) {
          const settlementAmount = transaction.node.settlementAmount || "N/A";
          const status = transaction.node.status || "N/A";
          if (status.toUpperCase() === "SUCCESS" || status.toUpperCase() === "COMPLETED") {
            console.log(`Amount (satoshis): ${settlementAmount}`);
            console.log(`Status: ${status}`);
            return true;
          }
        }
      }
    } else {
      console.error("Failed to fetch transactions. Status code:", response.status);
      console.error("Response:", response.data);
    }
  } catch (error) {
    console.error("Error fetching transactions:", error.message);
  }
  return false;
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
  try {
    const currency = await askQuestion('Enter the currency (e.g., USD, EUR): ');
    const amountStr = await askQuestion('Enter the amount: ');
    const numericAmount = parseFloat(amountStr);
    if (isNaN(numericAmount)) {
      console.error("Invalid amount. Please enter a numeric value.");
      process.exit(1);
    }
    const satoshis = await convertToSatoshis(currency.toUpperCase(), numericAmount);
    console.log(`${numericAmount} ${currency.toUpperCase()} is approximately ${satoshis} satoshis.`);
    const walletId = await getWalletId(authToken);
    if (!walletId) {
      console.error("BTC wallet not found. Exiting...");
      process.exit(1);
    }
    const invoice = await createLightningInvoice(authToken, walletId, satoshis);
    if (!invoice) {
      console.error("Failed to create Lightning invoice. Exiting...");
      process.exit(1);
    }
    console.log("\nInvoice created successfully:");
    console.log("Payment Request:", invoice.paymentRequest);
    console.log("Payment Hash:", invoice.paymentHash);
    console.log("Payment Secret:", invoice.paymentSecret);
    console.log("Satoshis:", invoice.satoshis);
    await displayQrCode(invoice.paymentRequest);
    console.log("\nWaiting for payment...");
    const intervalId = setInterval(async () => {
      const paid = await isInvoicePaid(authToken, invoice.paymentRequest);
      if (paid) {
        console.log("SUCCESS - Payment received!");
        clearInterval(intervalId);
        process.exit(0);
      }
    }, 1000);
  } catch (error) {
    console.error("Unexpected error:", error);
    process.exit(1);
  }
})();

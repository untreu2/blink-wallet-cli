require('dotenv').config();
const axios = require('axios');
const readline = require('readline');

const authToken = process.env.API_KEY;

async function checkPaymentStatus(authToken, paymentRequest) {
    const url = "https://api.blink.sv/graphql";
    const headers = {
        "content-type": "application/json",
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
                    console.log(`Amount (satoshis): ${settlementAmount}`);
                    console.log(`Status: ${status}`);
                    return;
                }
            }
            console.log("No matching transaction found for the provided payment request.");
        } else {
            console.error("Failed to fetch transactions. Status code:", response.status);
            console.error("Response:", response.data);
        }
    } catch (error) {
        console.error("Error fetching transactions:", error.message);
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
    const paymentRequest = await askQuestion("Enter the Lightning Invoice: ");
    await checkPaymentStatus(authToken, paymentRequest);
})();
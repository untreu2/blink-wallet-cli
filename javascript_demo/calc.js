const axios = require('axios');

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

    console.log(`${amount} ${currency} is approximately ${satoshis} satoshis.`);
}

const readline = require('readline');
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

rl.question('Enter the currency (e.g., USD, EUR): ', (currency) => {
    rl.question('Enter the amount: ', (amount) => {
        const numericAmount = parseFloat(amount);
        if (isNaN(numericAmount)) {
            console.error("Invalid amount. Please enter a numeric value.");
            rl.close();
            process.exit(1);
        }

        convertToSatoshis(currency.toUpperCase(), numericAmount).finally(() => rl.close());
    });
});

require('dotenv').config();
const smsService = require('./services/sms');

console.log("Testing SMS Service...");
console.log("API Key present:", !!process.env.AAKASH_SMS_API_KEY);

async function test() {
    console.log("Checking Balance...");
    const balance = await smsService.getSMSBalance();
    console.log("Balance Response:", balance);

    // Only send test SMS if configured
    // console.log("Sending Test SMS...");
    // const result = await smsService.sendSMS("9855062769", "Test from Debug Script"); 
    // console.log("Send Result:", result);
}

test();

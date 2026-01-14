// Load environment variables
require('dotenv').config();

// Test Aakash SMS API Connection
const { getSMSBalance, sendSMS } = require('./services/sms');

async function testAakashSMS() {
    console.log('\n========== Testing Aakash SMS API ==========\n');

    // Test 1: Check Balance
    console.log('Test 1: Checking SMS Balance...');
    const balanceResult = await getSMSBalance();
    console.log('Balance Result:', JSON.stringify(balanceResult, null, 2));

    // Test 2: Send Test SMS (commented out to avoid charges)
    // console.log('\nTest 2: Sending Test SMS...');
    // const smsResult = await sendSMS('9855062769', 'Test message from Aarambha PMS');
    // console.log('SMS Result:', JSON.stringify(smsResult, null, 2));

    console.log('\n========== Test Complete ==========\n');
    process.exit(0);
}

testAakashSMS();

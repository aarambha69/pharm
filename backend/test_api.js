const axios = require('axios');

async function testAddClient() {
    try {
        // 1. Login to get token
        const loginRes = await axios.post('http://localhost:5000/api/login', {
            phone: '9855062769',
            password: '987654321'
        });
        const token = loginRes.data.token;
        console.log('Logged in, token received');

        // 2. Add client
        const clientRes = await axios.post('http://localhost:5000/api/super/clients', {
            pharmacy_name: 'Test Pharmacy',
            address: 'Kathmandu',
            pan_number: '123456789',
            contact_number: '9800000000',
            package_id: '2',
            duration_days: '365',
            admin_name: 'Test Admin',
            admin_phone: '9811223344',
            admin_password: 'password123'
        }, {
            headers: { Authorization: `Bearer ${token}` }
        });
        console.log('Client add response:', clientRes.data);

        // 3. Verify client list
        const listRes = await axios.get('http://localhost:5000/api/super/clients', {
            headers: { Authorization: `Bearer ${token}` }
        });
        console.log('Clients count:', listRes.data.length);
        console.log('Clients:', listRes.data);

    } catch (err) {
        console.error('Error:', err.response ? err.response.data : err.message);
    }
}

testAddClient();

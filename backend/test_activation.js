const axios = require('axios');

async function test() {
    try {
        const res = await axios.post('http://localhost:5000/api/activate-super-admin', {
            machine_id: 'test_machine',
            phone: '9855062769',
            password: '987654321'
        });
        console.log('SUCCESS:', res.data);
    } catch (err) {
        console.error('ERROR:', err.response ? err.response.data : err.message);
    }
}

test();

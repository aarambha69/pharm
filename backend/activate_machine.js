const mysql = require('mysql2');
require('dotenv').config();

const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME
});

const machineId = "ff26a44b-a8b6-5024-8cf7-b7217184f070";

db.query('INSERT INTO device_activations (machine_id, user_role, activated_at, status) VALUES (?, "SUPER_ADMIN", NOW(), "active") ON DUPLICATE KEY UPDATE status="active", user_role="SUPER_ADMIN"', [machineId], (err) => {
    if (err) {
        console.error(err);
    } else {
        console.log(`Machine ${machineId} activated successfully!`);
    }
    db.end();
});

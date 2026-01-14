const mysql = require('mysql2');
require('dotenv').config();

const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME
});

db.connect((err) => {
    if (err) {
        console.error('Error connecting:', err);
        process.exit(1);
    }

    const queries = [
        "INSERT INTO users (phone, password, email, name, role) VALUES ('9855062769', '987654321', 'aarambhaaryal.dev@gmail.com', 'Aarambha Aryal', 'SUPER_ADMIN') ON DUPLICATE KEY UPDATE phone=phone",
        "INSERT INTO packages (id, name, features, price, duration_days, max_users) VALUES (1, 'Basic Package', 'Basic billing, 1 user, 100 medicines', 5000, 365, '1') ON DUPLICATE KEY UPDATE name=name",
        "INSERT INTO packages (id, name, features, price, duration_days, max_users) VALUES (2, 'Standard Package', 'Advanced billing, 5 users, 500 medicines, Reports', 15000, 365, '5') ON DUPLICATE KEY UPDATE name=name",
        "INSERT INTO packages (id, name, features, price, duration_days, max_users) VALUES (3, 'Premium Package', 'Full features, Unlimited users, Unlimited medicines, SMS alerts', 35000, 365, 'Unlimited') ON DUPLICATE KEY UPDATE name=name"
    ];

    let count = 0;
    queries.forEach(q => {
        db.query(q, (err) => {
            if (err) console.error('Error executing query:', q, err);
            else console.log('Query successful:', q.substring(0, 30) + '...');
            count++;
            if (count === queries.length) db.end();
        });
    });
});

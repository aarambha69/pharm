const mysql = require('mysql2');
require('dotenv').config();

const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME
});

db.connect(err => {
    if (err) throw err;
    console.log('Connected to MySQL');

    // Force update password for super admin
    const query = "UPDATE users SET password = '123456' WHERE phone = '9855062769'";

    db.query(query, (err, result) => {
        if (err) {
            console.error(err);
        } else {
            console.log('Password reset result:', result);
            if (result.affectedRows === 0) {
                // Insert if not exists (recover deleted user)
                const insert = "INSERT INTO users (name, phone, password, role) VALUES ('Aarambha Aryal', '9855062769', '123456', 'SUPER_ADMIN')";
                db.query(insert, (err, res) => {
                    if (err) console.error(err);
                    else console.log('User recreated:', res);
                    process.exit();
                });
            } else {
                process.exit();
            }
        }
    });
});

const mysql = require('mysql2');
require('dotenv').config();

const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME
});

db.connect();

// Update any vendors/customers/medicines with no client_id (likely created by super admin before)
const tables = ['vendors', 'customers', 'medicines', 'purchases', 'sales', 'stocks', 'supplier_ledger'];

tables.forEach(table => {
    db.query(`UPDATE ${table} SET client_id = 1 WHERE client_id IS NULL OR client_id = 0`, (err, res) => {
        if (err) console.error(`Error updating ${table}:`, err.message);
        else console.log(`Updated ${table}: ${res.affectedRows} rows`);
    });
});

setTimeout(() => db.end(), 5000);

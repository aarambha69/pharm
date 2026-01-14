const mysql = require('mysql2');
require('dotenv').config();

console.log("==========================================");
console.log("   DIAGNOSTIC TOOL - DATABASE CHECK       ");
console.log("==========================================");
console.log("Checking Environment Variables...");
console.log("DB_HOST:", process.env.DB_HOST || '127.0.0.1 (Default)');
console.log("DB_USER:", process.env.DB_USER || 'root (Default)');
console.log("DB_PASS:", process.env.DB_PASS ? '******' : '(Empty)');
console.log("DB_NAME:", process.env.DB_NAME || 'PharmacyDB (Default)');

const connection = mysql.createConnection({
    host: process.env.DB_HOST || '127.0.0.1',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASS || '',
    database: process.env.DB_NAME || 'PharmacyDB',
    connectTimeout: 5000
});

console.log("\nAttempting to connect to MySQL...");

connection.connect((err) => {
    if (err) {
        console.error("\n[X] CONNECTION FAILED!");
        console.error("Error Code:", err.code);
        console.error("Message:", err.message);

        if (err.code === 'ECONNREFUSED') {
            console.log("\nPOSSIBLE CAUSES:");
            console.log("1. MySQL Server is NOT RUNNING (Check Services).");
            console.log("2. MySQL is running on a different port (not 3306).");
        } else if (err.code === 'ER_ACCESS_DENIED_ERROR') {
            console.log("\nPOSSIBLE CAUSES:");
            console.log("1. Wrong Password in .env file.");
            console.log("2. Wrong Username.");
        } else if (err.code === 'ER_BAD_DB_ERROR') {
            console.log("\nPOSSIBLE CAUSES:");
            console.log("1. Database 'PharmacyDB' does not exist.");
        }
    } else {
        console.log("\n[V] SUCCESS! Database is Connected and Ready.");
    }
    console.log("\nPress any key to exit...");
    process.stdin.setRawMode(true);
    process.stdin.resume();
    process.stdin.on('data', process.exit.bind(process, 0));
});

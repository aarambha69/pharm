const mysql = require('mysql2/promise');
require('dotenv').config();

async function setup() {
    const connection = await mysql.createConnection({
        host: process.env.DB_HOST || 'localhost',
        user: process.env.DB_USER || 'root',
        password: process.env.DB_PASS || '',
        database: process.env.DB_NAME || 'PharmacyDB'
    });

    try {
        console.log('Creating sahakari_accounts table...');
        await connection.query(`
            CREATE TABLE IF NOT EXISTS sahakari_accounts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                client_id INT NOT NULL,
                bank_name VARCHAR(255) NOT NULL,
                address VARCHAR(255) NOT NULL,
                account_name VARCHAR(255) NOT NULL,
                account_number VARCHAR(100) NOT NULL,
                holder_name VARCHAR(255) NOT NULL,
                contact VARCHAR(50),
                notes TEXT,
                opening_balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
                opening_balance_date DATE NOT NULL,
                current_balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
                status ENUM('ACTIVE', 'INACTIVE') DEFAULT 'ACTIVE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (account_number, client_id)
            )
        `);

        console.log('Creating karobar_categories table...');
        await connection.query(`
            CREATE TABLE IF NOT EXISTS karobar_categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                client_id INT NOT NULL,
                name VARCHAR(100) NOT NULL,
                type ENUM('IN', 'OUT', 'BOTH') DEFAULT 'BOTH',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (name, client_id)
            )
        `);

        console.log('Creating karobar_statements table...');
        await connection.query(`
            CREATE TABLE IF NOT EXISTS karobar_statements (
                id INT AUTO_INCREMENT PRIMARY KEY,
                client_id INT NOT NULL,
                account_id INT NOT NULL,
                category_id INT NOT NULL,
                type ENUM('IN', 'OUT') NOT NULL,
                amount DECIMAL(15, 2) NOT NULL,
                balance_after DECIMAL(15, 2) NOT NULL,
                reason TEXT,
                notes TEXT,
                reference_no VARCHAR(100),
                performed_by INT NOT NULL,
                status ENUM('ACTIVE', 'DELETED') DEFAULT 'ACTIVE',
                deleted_by INT,
                deleted_at TIMESTAMP NULL,
                delete_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES sahakari_accounts(id),
                FOREIGN KEY (category_id) REFERENCES karobar_categories(id),
                FOREIGN KEY (performed_by) REFERENCES users(id)
            )
        `);

        // Insert default categories
        console.log('Inserting default categories...');
        const defaultCategories = [
            ['Daily Saving', 'IN'],
            ['Monthly Deposit', 'IN'],
            ['Emergency Fund', 'IN'],
            ['Bank Transfer', 'BOTH'],
            ['Expense Withdrawal', 'OUT'],
            ['Misc', 'BOTH']
        ];

        // We'll handle client_id 1 as default for now, but usually it should be dynamic
        // Since I don't know the exact client_id in context, I'll insert for client_id 1
        for (const [name, type] of defaultCategories) {
            await connection.query('INSERT IGNORE INTO karobar_categories (client_id, name, type) VALUES (1, ?, ?)', [name, type]);
        }

        console.log('Karobar tables created successfully!');
    } catch (error) {
        console.error('Error creating tables:', error);
    } finally {
        await connection.end();
    }
}

setup();

const express = require('express');
const router = express.Router();
const mysql = require('mysql2');
const bcrypt = require('bcrypt');
const { sendSMS, logSMS } = require('./services/sms');

// Configure DB connection (using same env vars)
const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME
});

// Helper to check duplicates
const checkDuplicate = (username, mobile) => {
    return new Promise((resolve, reject) => {
        db.query('SELECT * FROM users WHERE username = ? OR phone = ?', [username, mobile], (err, results) => {
            if (err) return reject(err);
            if (results.length > 0) return resolve(true);
            resolve(false);
        });
    });
};

// Create Cashier User
router.post('/cashier', async (req, res) => {
    const { full_name, mobile, username, password, permissions, client_id } = req.body;

    // Strict Input Validation
    if (!full_name || !mobile || !username || !password || !client_id) {
        return res.status(400).json({ error: 'All fields (Name, Mobile, Username, Password) are mandatory.' });
    }

    try {
        // 1. Check Duplicates
        const isDuplicate = await checkDuplicate(username, mobile);
        if (isDuplicate) {
            return res.status(409).json({ error: 'Username or Mobile number already exists.' });
        }

        // 2. Hash Password (Strict: ONE WAY HASH)
        const hashedPassword = await bcrypt.hash(password, 10);

        // 3. Format Permissions (Array to CSV)
        const permsString = Array.isArray(permissions) ? permissions.join(',') : (permissions || '');

        // 4. Insert User
        const query = `
            INSERT INTO users (name, phone, username, password, role, permissions, client_id, status, created_at)
            VALUES (?, ?, ?, ?, 'CASHIER', ?, ?, 'ACTIVE', NOW())
        `;

        db.query(query, [full_name, mobile, username, hashedPassword, permsString, client_id], async (err, result) => {
            if (err) return res.status(500).json({ error: err.message });

            // 5. Send Credential SMS (Strict: Using exact admin-provided details)
            // Generate Access Summary
            const accessList = permsString.split(',').filter(p => p).map(p => `- ${formatPermissionName(p)}`).join('\n') || '- None';

            const smsMessage = `Your cashier account is created.\nLogin ID: ${username}\nPassword: ${password}\nAccess Level:\n${accessList}\n- Aarambha Softwares`;

            const smsResult = await sendSMS(mobile, smsMessage);

            // 6. Log SMS
            logSMS(db, {
                client_id,
                type: 'CASHIER_CREDENTIALS',
                to_number: mobile,
                message_text: smsMessage,
                status: smsResult.success ? 'SENT' : 'FAILED',
                provider_response: smsResult.error || smsResult.messageId
            });

            // 7. Response
            res.status(201).json({
                message: 'Cashier created successfully',
                sms_status: smsResult.success ? 'Sent' : 'Failed',
                sms_error: smsResult.error
            });
        });

    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// Update Cashier Permissions / Details
router.put('/:id', async (req, res) => {
    const { id } = req.params;
    const { full_name, mobile, permissions, status } = req.body;

    // Note: Password update is separate to ensure strict control

    const permsString = Array.isArray(permissions) ? permissions.join(',') : (permissions || '');

    const query = 'UPDATE users SET name = ?, phone = ?, permissions = ?, status = ? WHERE id = ? AND role = "CASHIER"';
    db.query(query, [full_name, mobile, permsString, status, id], (err) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ message: 'Cashier updated successfully' });
    });
});

// Resend Credentials (Strict: Requires Admin to re-enter password for security)
router.post('/resend-creds', async (req, res) => {
    const { mobile, username, password, client_id } = req.body;

    if (!password) return res.status(400).json({ error: 'Password confirmation required for security.' });

    // Verify user exists
    db.query('SELECT * FROM users WHERE username = ? AND phone = ?', [username, mobile], async (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        if (results.length === 0) return res.status(404).json({ error: 'User not found' });

        const user = results[0];

        // Verify password matches (Admin re-entered correct one)
        const match = await bcrypt.compare(password, user.password);
        if (!match) {
            return res.status(401).json({ error: 'Incorrect password entered. Cannot resend.' });
        }

        // Send SMS
        const permsString = user.permissions || '';
        const accessList = permsString.split(',').filter(p => p).map(p => `- ${formatPermissionName(p)}`).join('\n') || '- None';
        const smsMessage = `[Resent] Your cashier account details.\nLogin ID: ${username}\nPassword: ${password}\nAccess Level:\n${accessList}\n- Aarambha Softwares`;

        const smsResult = await sendSMS(mobile, smsMessage);

        logSMS(db, {
            client_id,
            type: 'CASHIER_CREDENTIALS_RESEND',
            to_number: mobile,
            message_text: smsMessage,
            status: smsResult.success ? 'SENT' : 'FAILED',
            provider_response: smsResult.error || smsResult.messageId
        });

        res.json({
            message: 'Credentials resent successfully',
            sms_status: smsResult.success ? 'Sent' : 'Failed'
        });
    });
});

// Helper to list users
router.get('/', (req, res) => {
    const { client_id } = req.query;
    db.query('SELECT id, name, username, phone, role, status, permissions, created_at FROM users WHERE client_id = ? AND role != "SUPER_ADMIN" ORDER BY created_at DESC', [client_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

function formatPermissionName(p) {
    const map = {
        'billing': 'Billing',
        'inventory': 'Inventory',
        'refund': 'Refunds',
        'reports': 'Reports',
        'karobar': 'Karobar',
        'crm': 'CRM',
        'vendor': 'Vendor Mgmt'
    };
    return map[p] || p;
}

module.exports = router;

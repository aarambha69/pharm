const express = require('express');
const router = express.Router();

// Helper to get DB connection
const getDb = (req) => req.app.get('db');

// --- ACCOUNTS MANAGEMENT ---

// List all accounts
router.get('/accounts', async (req, res) => {
    const db = getDb(req);
    const client_id = req.user.client_id;
    try {
        const [rows] = await db.promise().query(
            'SELECT * FROM sahakari_accounts WHERE client_id = ? ORDER BY bank_name ASC',
            [client_id]
        );
        res.json(rows);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Create account
router.post('/accounts', async (req, res) => {
    const db = getDb(req);
    const client_id = req.user.client_id;
    const {
        bank_name, address, account_name, account_number,
        holder_name, contact, notes, opening_balance, opening_balance_date
    } = req.body;

    try {
        const [result] = await db.promise().query(
            `INSERT INTO sahakari_accounts 
            (client_id, bank_name, address, account_name, account_number, holder_name, contact, notes, opening_balance, opening_balance_date, current_balance) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
            [client_id, bank_name, address, account_name, account_number, holder_name, contact, notes, opening_balance, opening_balance_date, opening_balance]
        );
        res.json({ message: 'Account created successfully', id: result.insertId });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Update account
router.put('/accounts/:id', async (req, res) => {
    const db = getDb(req);
    const client_id = req.user.client_id;
    const { id } = req.params;
    const {
        bank_name, address, account_name, account_number,
        holder_name, contact, notes, status
    } = req.body;

    try {
        await db.promise().query(
            `UPDATE sahakari_accounts SET 
            bank_name=?, address=?, account_name=?, account_number=?, holder_name=?, contact=?, notes=?, status=?
            WHERE id=? AND client_id=?`,
            [bank_name, address, account_name, account_number, holder_name, contact, notes, status, id, client_id]
        );
        res.json({ message: 'Account updated successfully' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// --- CATEGORIES MANAGEMENT ---

router.get('/categories', async (req, res) => {
    const db = getDb(req);
    const client_id = req.user.client_id;
    try {
        const [rows] = await db.promise().query(
            'SELECT * FROM karobar_categories WHERE client_id = ? ORDER BY name ASC',
            [client_id]
        );
        res.json(rows);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

router.post('/categories', async (req, res) => {
    const db = getDb(req);
    const client_id = req.user.client_id;
    const { name, type } = req.body;
    try {
        const [result] = await db.promise().query(
            'INSERT INTO karobar_categories (client_id, name, type) VALUES (?, ?, ?)',
            [client_id, name, type]
        );
        res.json({ message: 'Category added', id: result.insertId });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// --- TRANSACTIONS (CASH IN / CASH OUT) ---

router.post('/transaction', async (req, res) => {
    const db = getDb(req);
    const client_id = req.user.client_id;
    const user_id = req.user.id;
    const {
        account_id, category_id, type, amount,
        reason, notes, reference_no, transaction_date
    } = req.body;

    db.beginTransaction(async (err) => {
        if (err) return res.status(500).json({ error: err.message });

        try {
            // 1. Get current balance
            const [accounts] = await db.promise().query(
                'SELECT current_balance FROM sahakari_accounts WHERE id = ? AND client_id = ? FOR UPDATE',
                [account_id, client_id]
            );
            if (accounts.length === 0) throw new Error('Account not found');

            let current_balance = parseFloat(accounts[0].current_balance);
            let new_balance = current_balance;

            if (type === 'IN') {
                new_balance += parseFloat(amount);
            } else {
                if (current_balance < parseFloat(amount)) {
                    // Allowed if user is admin, but blocked by default as per requirement
                    if (req.user.role !== 'ADMIN' && req.user.role !== 'SUPER_ADMIN') {
                        throw new Error('Insufficient funds in account');
                    }
                }
                new_balance -= parseFloat(amount);
            }

            // 2. Update account balance
            await db.promise().query(
                'UPDATE sahakari_accounts SET current_balance = ? WHERE id = ?',
                [new_balance, account_id]
            );

            // 3. Create statement entry
            await db.promise().query(
                `INSERT INTO karobar_statements 
                (client_id, account_id, category_id, type, amount, balance_after, reason, notes, reference_no, performed_by, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
                [client_id, account_id, category_id, type, amount, new_balance, reason, notes, reference_no, user_id, transaction_date || new Date()]
            );

            db.commit((err) => {
                if (err) throw err;
                res.json({ message: 'Transaction successful', balance: new_balance });
            });
        } catch (error) {
            db.rollback(() => {
                res.status(500).json({ error: error.message });
            });
        }
    });
});

// --- STATEMENTS / LEDGER ---

router.get('/statements', async (req, res) => {
    const db = getDb(req);
    const client_id = req.user.client_id;
    const {
        start_date, end_date, account_id, category_id,
        type, performed_by, status, search
    } = req.query;

    let sql = `
        SELECT s.*, a.bank_name, a.account_number, c.name as category_name, u.name as performed_by_name
        FROM karobar_statements s
        JOIN sahakari_accounts a ON s.account_id = a.id
        JOIN karobar_categories c ON s.category_id = c.id
        JOIN users u ON s.performed_by = u.id
        WHERE s.client_id = ?
    `;
    const params = [client_id];

    if (start_date) {
        sql += ' AND DATE(s.created_at) >= ?';
        params.push(start_date);
    }
    if (end_date) {
        sql += ' AND DATE(s.created_at) <= ?';
        params.push(end_date);
    }
    if (account_id) {
        sql += ' AND s.account_id = ?';
        params.push(account_id);
    }
    if (category_id) {
        sql += ' AND s.category_id = ?';
        params.push(category_id);
    }
    if (type) {
        sql += ' AND s.type = ?';
        params.push(type);
    }
    if (performed_by) {
        sql += ' AND s.performed_by = ?';
        params.push(performed_by);
    }
    if (status) {
        sql += ' AND s.status = ?';
        params.push(status);
    } else {
        sql += " AND s.status = 'ACTIVE'";
    }
    if (search) {
        sql += ' AND (s.notes LIKE ? OR s.reference_no LIKE ? OR s.reason LIKE ?)';
        const val = `%${search}%`;
        params.push(val, val, val);
    }

    sql += ' ORDER BY s.created_at DESC, s.id DESC';

    try {
        const [rows] = await db.promise().query(sql, params);
        res.json(rows);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Admin Delete (Soft Delete)
router.patch('/statements/:id/delete', async (req, res) => {
    const db = getDb(req);
    const client_id = req.user.client_id;
    const user_id = req.user.id;
    const { id } = req.params;
    const { reason } = req.body;

    if (req.user.role !== 'ADMIN' && req.user.role !== 'SUPER_ADMIN') {
        return res.status(403).json({ error: 'Permission denied' });
    }

    db.beginTransaction(async (err) => {
        if (err) return res.status(500).json({ error: err.message });

        try {
            // 1. Get target statement
            const [statements] = await db.promise().query(
                'SELECT * FROM karobar_statements WHERE id = ? AND client_id = ?',
                [id, client_id]
            );
            if (statements.length === 0) throw new Error('Statement not found');
            const target = statements[0];

            if (target.status === 'DELETED') throw new Error('Already deleted');

            // 2. Soft delete
            await db.promise().query(
                "UPDATE karobar_statements SET status = 'DELETED', deleted_by = ?, deleted_at = NOW(), delete_reason = ? WHERE id = ?",
                [user_id, reason, id]
            );

            // 3. Recalculate account balance
            // balance = opening_balance + sum(active_in) - sum(active_out)
            const [balances] = await db.promise().query(
                `SELECT
        a.opening_balance +
            COALESCE(SUM(CASE WHEN s.type = 'IN' THEN s.amount ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN s.type = 'OUT' THEN s.amount ELSE 0 END), 0) as new_balance
                FROM sahakari_accounts a
                LEFT JOIN karobar_statements s ON a.id = s.account_id AND s.status = 'ACTIVE'
                WHERE a.id = ?
            GROUP BY a.id`,
                [target.account_id]
            );

            const new_balance = balances[0].new_balance;

            // 4. Update sahakari_accounts table
            await db.promise().query(
                'UPDATE sahakari_accounts SET current_balance = ? WHERE id = ?',
                [new_balance, target.account_id]
            );

            // 5. Update running balances for subsequent statements (to maintain visual ledger integrity)
            // This is complex for a simple soft delete, requirement says recalculate OR immutable.
            // Recalculating the specific account's latest balance is the priority.
            // Visual balance_after for other records stays fixed to point-in-time unless we re-run the whole ledger.
            // For now, we update the account master balance.

            db.commit((err) => {
                if (err) throw err;
                res.json({ message: 'Statement deleted and balance recalculated', new_balance });
            });
        } catch (error) {
            db.rollback(() => {
                res.status(500).json({ error: error.message });
            });
        }
    });
});

module.exports = router;

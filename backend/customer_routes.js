const express = require('express');
const router = express.Router();

// Middleware to ensure user is authenticated
const requireAuth = (req, res, next) => {
    if (req.user) {
        next();
    } else {
        res.status(401).json({ message: 'Unauthorized' });
    }
};

// GET /api/customers - List all customers
router.get('/customers', requireAuth, (req, res) => {
    const client_id = req.user.client_id;
    const { status, search } = req.query;

    let query = 'SELECT * FROM customers WHERE client_id = ?';
    const params = [client_id];

    if (status) {
        query += ' AND status = ?';
        params.push(status);
    }

    if (search) {
        query += ' AND (full_name LIKE ? OR mobile_number LIKE ? OR customer_id LIKE ?)';
        params.push(`%${search}%`, `%${search}%`, `%${search}%`);
    }

    query += ' ORDER BY created_at DESC';

    req.app.get('db').query(query, params, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// GET /api/customers/search - Search customers for autocomplete
router.get('/customers/search', requireAuth, (req, res) => {
    const client_id = req.user.client_id;
    const { q } = req.query;

    if (!q || q.length < 2) {
        return res.json([]);
    }

    const query = `
        SELECT id, customer_id, full_name, mobile_number 
        FROM customers 
        WHERE client_id = ? AND status = 'active'
        AND (full_name LIKE ? OR full_name LIKE ? OR mobile_number LIKE ?)
        ORDER BY full_name ASC
        LIMIT 10
    `;

    const params = [client_id, `${q}%`, `%${q}%`, `%${q}%`];

    req.app.get('db').query(query, params, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// GET /api/customers/:id - Get single customer
router.get('/customers/:id', requireAuth, (req, res) => {
    const client_id = req.user.client_id;
    const { id } = req.params;

    const query = 'SELECT * FROM customers WHERE id = ? AND client_id = ?';
    req.app.get('db').query(query, [id, client_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        if (results.length === 0) return res.status(404).json({ message: 'Customer not found' });
        res.json(results[0]);
    });
});

// POST /api/customers - Add new customer
router.post('/customers', requireAuth, (req, res) => {
    const client_id = req.user.client_id;
    const { full_name, mobile_number, address, notes } = req.body;

    if (!full_name) {
        return res.status(400).json({ message: 'Full name is required' });
    }

    if (!mobile_number) {
        return res.status(400).json({ message: 'Mobile number is required' });
    }

    // Check for duplicate mobile number
    const checkQuery = 'SELECT id FROM customers WHERE client_id = ? AND mobile_number = ?';
    req.app.get('db').query(checkQuery, [client_id, mobile_number], (err, existing) => {
        if (err) return res.status(500).json({ error: err.message });
        if (existing.length > 0) {
            return res.status(409).json({ message: 'Customer with this mobile number already exists' });
        }

        insertCustomer();
    });

    function insertCustomer() {
        // Generate customer ID
        const customerIdQuery = 'SELECT COUNT(*) as count FROM customers WHERE client_id = ?';
        req.app.get('db').query(customerIdQuery, [client_id], (err, countResult) => {
            if (err) return res.status(500).json({ error: err.message });

            const count = countResult[0].count + 1;
            const customer_id = `CUST-${String(count).padStart(6, '0')}`;

            const insertQuery = `
                INSERT INTO customers (client_id, customer_id, full_name, mobile_number, address, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            `;

            req.app.get('db').query(insertQuery, [
                client_id, customer_id, full_name, mobile_number, address || null, notes || null
            ], (err, result) => {
                if (err) return res.status(500).json({ error: err.message });
                res.json({
                    message: 'Customer added successfully',
                    id: result.insertId,
                    customer_id
                });
            });
        });
    }
});

// PUT /api/customers/:id - Update customer
router.put('/customers/:id', requireAuth, (req, res) => {
    const client_id = req.user.client_id;
    const { id } = req.params;
    const { full_name, mobile_number, address, notes, status } = req.body;

    const query = `
        UPDATE customers 
        SET full_name = ?, mobile_number = ?, address = ?, notes = ?, status = ?
        WHERE id = ? AND client_id = ?
    `;

    req.app.get('db').query(query, [
        full_name, mobile_number || null, address || null, notes || null, status || 'active', id, client_id
    ], (err, result) => {
        if (err) return res.status(500).json({ error: err.message });
        if (result.affectedRows === 0) {
            return res.status(404).json({ message: 'Customer not found' });
        }
        res.json({ message: 'Customer updated successfully' });
    });
});

// DELETE /api/customers/:id - Delete/block customer
router.delete('/customers/:id', requireAuth, (req, res) => {
    const client_id = req.user.client_id;
    const { id } = req.params;

    // Soft delete - set status to blocked
    const query = 'UPDATE customers SET status = ? WHERE id = ? AND client_id = ?';
    req.app.get('db').query(query, ['blocked', id, client_id], (err, result) => {
        if (err) return res.status(500).json({ error: err.message });
        if (result.affectedRows === 0) {
            return res.status(404).json({ message: 'Customer not found' });
        }
        res.json({ message: 'Customer blocked successfully' });
    });
});

module.exports = router;

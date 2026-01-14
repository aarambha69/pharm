const express = require('express');
const router = express.Router();

// Middleware
const requireAuth = (req, res, next) => {
    if (req.user) next();
    else res.status(401).json({ message: 'Unauthorized' });
};

const requireAdmin = (req, res, next) => {
    if (req.user && (req.user.role === 'ADMIN' || req.user.role === 'SUPER_ADMIN')) next();
    else res.status(403).json({ message: 'Admin access required' });
};

// POST /api/refunds - Create refund request (Cashier)
router.post('/refunds', requireAuth, (req, res) => {
    const { bill_id, refund_type, items, reason, reason_notes } = req.body;
    const requested_by = req.user.id;
    const client_id = req.user.client_id;

    // Validation
    if (!bill_id || !refund_type || !reason) {
        return res.status(400).json({ message: 'Bill ID, refund type, and reason are required' });
    }

    if (refund_type === 'PARTIAL' && (!items || items.length === 0)) {
        return res.status(400).json({ message: 'Items are required for partial refund' });
    }

    // Get original bill
    const billQuery = `SELECT * FROM sales WHERE id = ? AND client_id = ?`;
    req.app.get('db').query(billQuery, [bill_id, client_id], (err, bills) => {
        if (err) return res.status(500).json({ error: err.message });
        if (bills.length === 0) return res.status(404).json({ message: 'Bill not found' });

        const bill = bills[0];

        // Generate refund ID
        const refundIdQuery = 'SELECT COUNT(*) as count FROM refunds';
        req.app.get('db').query(refundIdQuery, (err, countResult) => {
            if (err) return res.status(500).json({ error: err.message });

            const count = countResult[0].count + 1;
            const refund_id = `REF-${String(count).padStart(6, '0')}`;

            if (refund_type === 'FULL') {
                // Full refund
                const refundAmount = bill.final_amount;

                const insertQuery = `
                    INSERT INTO refunds (refund_id, bill_id, customer_id, refund_type, refund_amount, payment_mode, reason, reason_notes, requested_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                `;

                req.app.get('db').query(insertQuery, [
                    refund_id, bill_id, bill.customer_id, refund_type, refundAmount, bill.payment_category, reason, reason_notes, requested_by
                ], (err, result) => {
                    if (err) return res.status(500).json({ error: err.message });
                    res.json({ message: 'Refund request created', refund_id, id: result.insertId });
                });
            } else {
                // Partial refund
                let refundAmount = 0;
                const itemInserts = [];

                // Get sale items
                const saleItemsQuery = `SELECT * FROM sale_items WHERE sale_id = ?`;
                req.app.get('db').query(saleItemsQuery, [bill_id], (err, saleItems) => {
                    if (err) return res.status(500).json({ error: err.message });

                    // Validate and calculate
                    for (const item of items) {
                        const saleItem = saleItems.find(si => si.id === item.sale_item_id);
                        if (!saleItem) {
                            return res.status(400).json({ message: `Sale item ${item.sale_item_id} not found` });
                        }
                        if (item.quantity > saleItem.quantity) {
                            return res.status(400).json({ message: `Refund quantity exceeds sold quantity for item ${saleItem.medicine_id}` });
                        }

                        const itemTotal = item.quantity * saleItem.unit_price;
                        refundAmount += itemTotal;
                        itemInserts.push([null, saleItem.medicine_id, saleItem.batch_no, item.quantity, saleItem.unit_price, itemTotal, item.sale_item_id]);
                    }

                    // Insert refund
                    const insertQuery = `
                        INSERT INTO refunds (refund_id, bill_id, customer_id, refund_type, refund_amount, payment_mode, reason, reason_notes, requested_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    `;

                    req.app.get('db').query(insertQuery, [
                        refund_id, bill_id, bill.customer_id, refund_type, refundAmount, bill.payment_category, reason, reason_notes, requested_by
                    ], (err, result) => {
                        if (err) return res.status(500).json({ error: err.message });

                        const refund_pk_id = result.insertId;

                        // Insert refund items
                        itemInserts.forEach(item => item[0] = refund_pk_id);
                        const itemsQuery = `INSERT INTO refund_items (refund_id, medicine_id, batch_no, quantity, unit_price, total_amount, sale_item_id) VALUES ?`;

                        req.app.get('db').query(itemsQuery, [itemInserts], (err) => {
                            if (err) return res.status(500).json({ error: err.message });
                            res.json({ message: 'Refund request created', refund_id, id: refund_pk_id });
                        });
                    });
                });
            }
        });
    });
});

// GET /api/refunds - List refunds
router.get('/refunds', requireAuth, (req, res) => {
    const client_id = req.user.client_id;
    const { status } = req.query;
    const isAdmin = req.user.role === 'ADMIN' || req.user.role === 'SUPER_ADMIN';

    let query = `
        SELECT r.*, 
               s.bill_number,
               u1.name as requested_by_name,
               u2.name as approved_by_name
        FROM refunds r
        JOIN sales s ON r.bill_id = s.id
        LEFT JOIN users u1 ON r.requested_by = u1.id
        LEFT JOIN users u2 ON r.approved_by = u2.id
        WHERE s.client_id = ?
    `;

    const params = [client_id];

    if (!isAdmin) {
        query += ` AND r.requested_by = ?`;
        params.push(req.user.id);
    }

    if (status) {
        query += ` AND r.status = ?`;
        params.push(status);
    }

    query += ` ORDER BY r.created_at DESC`;

    req.app.get('db').query(query, params, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// GET /api/refunds/:id - Get refund details
router.get('/refunds/:id', requireAuth, (req, res) => {
    const refund_id = req.params.id;
    const client_id = req.user.client_id;

    const query = `
        SELECT r.*, 
               s.bill_number, s.final_amount as bill_amount,
               u1.name as requested_by_name,
               u2.name as approved_by_name
        FROM refunds r
        JOIN sales s ON r.bill_id = s.id
        LEFT JOIN users u1 ON r.requested_by = u1.id
        LEFT JOIN users u2 ON r.approved_by = u2.id
        WHERE r.id = ? AND s.client_id = ?
    `;

    req.app.get('db').query(query, [refund_id, client_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        if (results.length === 0) return res.status(404).json({ message: 'Refund not found' });

        const refund = results[0];

        // Get refund items if partial
        if (refund.refund_type === 'PARTIAL') {
            const itemsQuery = `
                SELECT ri.*, m.name as medicine_name
                FROM refund_items ri
                JOIN medicines m ON ri.medicine_id = m.id
                WHERE ri.refund_id = ?
            `;

            req.app.get('db').query(itemsQuery, [refund_id], (err, items) => {
                if (err) return res.status(500).json({ error: err.message });
                refund.items = items;
                res.json(refund);
            });
        } else {
            res.json(refund);
        }
    });
});

// PUT /api/refunds/:id/approve - Approve refund (Admin)
router.put('/refunds/:id/approve', requireAdmin, (req, res) => {
    const refund_id = req.params.id;
    const approved_by = req.user.id;
    const client_id = req.user.client_id;

    // Get refund details
    const refundQuery = `
        SELECT r.*, s.client_id
        FROM refunds r
        JOIN sales s ON r.bill_id = s.id
        WHERE r.id = ? AND s.client_id = ?
    `;

    req.app.get('db').query(refundQuery, [refund_id, client_id], (err, refunds) => {
        if (err) return res.status(500).json({ error: err.message });
        if (refunds.length === 0) return res.status(404).json({ message: 'Refund not found' });

        const refund = refunds[0];

        if (refund.status !== 'PENDING') {
            return res.status(400).json({ message: 'Refund already processed' });
        }

        // Update refund status
        const updateQuery = `UPDATE refunds SET status = 'APPROVED', approved_by = ?, approved_at = NOW() WHERE id = ?`;
        req.app.get('db').query(updateQuery, [approved_by, refund_id], (err) => {
            if (err) return res.status(500).json({ error: err.message });

            // Adjust stock
            if (refund.refund_type === 'FULL') {
                // Get all sale items
                const saleItemsQuery = `SELECT * FROM sale_items WHERE sale_id = ?`;
                req.app.get('db').query(saleItemsQuery, [refund.bill_id], (err, items) => {
                    if (err) return res.status(500).json({ error: err.message });

                    items.forEach(item => {
                        const stockUpdate = `UPDATE stocks SET quantity = quantity + ? WHERE medicine_id = ? AND batch_number = ?`;
                        req.app.get('db').query(stockUpdate, [item.quantity, item.medicine_id, item.batch_no]);
                    });

                    res.json({ message: 'Refund approved and stock adjusted' });
                });
            } else {
                // Partial refund - adjust specific items
                const refundItemsQuery = `SELECT * FROM refund_items WHERE refund_id = ?`;
                req.app.get('db').query(refundItemsQuery, [refund_id], (err, items) => {
                    if (err) return res.status(500).json({ error: err.message });

                    items.forEach(item => {
                        const stockUpdate = `UPDATE stocks SET quantity = quantity + ? WHERE medicine_id = ? AND batch_number = ?`;
                        req.app.get('db').query(stockUpdate, [item.quantity, item.medicine_id, item.batch_no]);
                    });

                    res.json({ message: 'Refund approved and stock adjusted' });
                });
            }
        });
    });
});

// PUT /api/refunds/:id/reject - Reject refund (Admin)
router.put('/refunds/:id/reject', requireAdmin, (req, res) => {
    const refund_id = req.params.id;
    const approved_by = req.user.id;
    const client_id = req.user.client_id;
    const { admin_remarks } = req.body;

    if (!admin_remarks) {
        return res.status(400).json({ message: 'Admin remarks required for rejection' });
    }

    const query = `
        UPDATE refunds r
        JOIN sales s ON r.bill_id = s.id
        SET r.status = 'REJECTED', r.approved_by = ?, r.approved_at = NOW(), r.admin_remarks = ?
        WHERE r.id = ? AND s.client_id = ?
    `;

    req.app.get('db').query(query, [approved_by, admin_remarks, refund_id, client_id], (err, result) => {
        if (err) return res.status(500).json({ error: err.message });
        if (result.affectedRows === 0) return res.status(404).json({ message: 'Refund not found' });

        res.json({ message: 'Refund rejected' });
    });
});

module.exports = router;

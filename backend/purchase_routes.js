const express = require('express');
const router = express.Router();
const mysql = require('mysql2');

// Helper to get DB connection from app
const getDb = (req) => req.app.get('db');

// --- PRODUCT SEARCH (TYPEAHEAD) ---
router.get('/search-medicines', (req, res) => {
    const db = getDb(req);
    const query = req.query.q || '';
    const sql = `
        SELECT id, name, strength, manufacturer, dosage_form, unit,
               avg_cost, last_purchase_rate, item_code, barcode
        FROM medicines 
        WHERE (name LIKE ? OR generic_name LIKE ? OR barcode = ? OR item_code = ?)
        LIMIT 20
    `;
    const val = `%${query}%`;
    db.query(sql, [val, val, query, query], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// --- SAVE GRN (DRAFT OR CONFIRMED) ---
router.post('/purchases', async (req, res) => {
    const db = getDb(req);
    const {
        grn_no, supplier_id, invoice_no, purchase_date,
        payment_type, due_date, subtotal, discount_total,
        tax_total, grand_total, paid_amount, status, notes, items
    } = req.body;

    const client_id = req.user.client_id;
    const user_id = req.user.id;

    db.beginTransaction(async (err) => {
        if (err) return res.status(500).json({ error: err.message });

        try {
            // 1. Insert/Update Purchase Header
            const actual_grn = grn_no || `GRN-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
            const purchaseSql = `
                INSERT INTO purchases (
                    grn_no, client_id, supplier_id, invoice_no, purchase_date, 
                    payment_type, due_date, subtotal, discount_total, tax_total, 
                    grand_total, paid_amount, status, notes, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON DUPLICATE KEY UPDATE 
                    supplier_id=VALUES(supplier_id), invoice_no=VALUES(invoice_no),
                    purchase_date=VALUES(purchase_date), payment_type=VALUES(payment_type),
                    due_date=VALUES(due_date), subtotal=VALUES(subtotal),
                    discount_total=VALUES(discount_total), tax_total=VALUES(tax_total),
                    grand_total=VALUES(grand_total), paid_amount=VALUES(paid_amount),
                    status=VALUES(status), notes=VALUES(notes)
            `;

            const [pResult] = await db.promise().query(purchaseSql, [
                actual_grn, client_id, supplier_id, invoice_no, purchase_date,
                payment_type, due_date || null, subtotal, discount_total, tax_total,
                grand_total, paid_amount, status, notes, user_id
            ]);

            const purchase_id = pResult.insertId || (await db.promise().query('SELECT id FROM purchases WHERE grn_no = ?', [actual_grn]))[0][0].id;

            // 2. Clear old items if updating
            await db.promise().query('DELETE FROM purchase_items WHERE purchase_id = ?', [purchase_id]);

            // 3. Insert Purchase Items
            if (items && items.length > 0) {
                const itemValues = items.map(item => [
                    purchase_id, item.medicine_id, item.batch_no, item.mfg_date || null, item.expiry_date || null,
                    item.qty, item.free_qty || 0, item.purchase_rate || 0, item.mrp || 0,
                    item.discount_amount || 0, item.tax_amount || 0, item.line_total || 0
                ]);
                await db.promise().query(
                    'INSERT INTO purchase_items (purchase_id, medicine_id, batch_no, mfg_date, expiry_date, qty, free_qty, purchase_rate, mrp, discount_amount, tax_amount, line_total) VALUES ?',
                    [itemValues]
                );
            }

            // 4. If Status is CONFIRMED, Trigger Inventory and Ledger updates
            if (status === 'CONFIRMED') {
                await processConfirmation(db, purchase_id, client_id);
            }

            db.commit((err) => {
                if (err) throw err;
                res.json({ message: 'Purchase saved successfully', purchase_id });
            });
        } catch (error) {
            db.rollback(() => {
                res.status(500).json({ error: error.message });
            });
        }
    });
});

async function processConfirmation(db, purchase_id, client_id) {
    // Fetch purchase and items
    const [purchases] = await db.promise().query('SELECT * FROM purchases WHERE id = ?', [purchase_id]);
    const purchase = purchases[0];
    const [items] = await db.promise().query('SELECT * FROM purchase_items WHERE purchase_id = ?', [purchase_id]);

    for (const item of items) {
        const received_qty = item.qty + item.free_qty;

        // A. Get current stock and cost for Weighted Average
        const [meds] = await db.promise().query('SELECT * FROM medicines WHERE id = ?', [item.medicine_id]);
        const medicine = meds[0];

        // Calculate current total stock
        const [stockRes] = await db.promise().query('SELECT SUM(quantity) as total FROM stocks WHERE medicine_id = ?', [item.medicine_id]);
        const old_stock = stockRes[0].total || 0;
        const old_avg_cost = medicine.avg_cost || 0;

        // Weighted Average Cost: (old_stock*old_avg_cost + received_qty*purchase_rate) / (old_stock + received_qty)
        const new_total_stock = old_stock + received_qty;
        let new_avg_cost = old_avg_cost;
        if (new_total_stock > 0) {
            new_avg_cost = ((old_stock * old_avg_cost) + (received_qty * item.purchase_rate)) / new_total_stock;
        }

        // B. Update Medicine Master
        await db.promise().query(
            'UPDATE medicines SET avg_cost = ?, last_purchase_rate = ?, low_stock_threshold = low_stock_threshold WHERE id = ?',
            [new_avg_cost, item.purchase_rate, item.medicine_id]
        );

        // C. Update/Create Stock Batch
        // Find existing batch
        const [batches] = await db.promise().query(
            'SELECT id FROM stocks WHERE medicine_id = ? AND batch_number = ? AND expiry_date = ? AND client_id = ?',
            [item.medicine_id, item.batch_no, item.expiry_date, client_id]
        );

        if (batches.length > 0) {
            await db.promise().query(
                'UPDATE stocks SET quantity = quantity + ?, purchase_price = ?, selling_price = ?, purchase_item_id = ?, mfg_date = ? WHERE id = ?',
                [received_qty, item.purchase_rate, item.mrp, item.id, item.mfg_date, batches[0].id]
            );
        } else {
            await db.promise().query(
                'INSERT INTO stocks (client_id, medicine_id, vendor_id, batch_number, mfg_date, expiry_date, quantity, purchase_price, selling_price, purchase_item_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                [client_id, item.medicine_id, purchase.supplier_id, item.batch_no, item.mfg_date, item.expiry_date, received_qty, item.purchase_rate, item.mrp, item.id]
            );
        }
    }

    // D. Update Supplier Ledger
    const due_amount = purchase.grand_total - purchase.paid_amount;

    // Get last balance
    const [lastLedger] = await db.promise().query(
        'SELECT balance FROM supplier_ledger WHERE supplier_id = ? AND client_id = ? ORDER BY id DESC LIMIT 1',
        [purchase.supplier_id, client_id]
    );
    const old_balance = lastLedger.length > 0 ? parseFloat(lastLedger[0].balance) : 0;
    const new_balance = old_balance + due_amount;

    await db.promise().query(
        'INSERT INTO supplier_ledger (supplier_id, client_id, transaction_type, transaction_id, debit, credit, balance, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        [purchase.supplier_id, client_id, 'PURCHASE', purchase_id, 0, due_amount, new_balance, `Purchase GRN: ${purchase.grn_no}, Inv: ${purchase.invoice_no}`]
    );
}

// --- GET SUPPLIER BALANCE ---
router.get('/suppliers/:id/balance', (req, res) => {
    const db = getDb(req);
    const sql = 'SELECT balance FROM supplier_ledger WHERE supplier_id = ? AND client_id = ? ORDER BY id DESC LIMIT 1';
    db.query(sql, [req.params.id, req.user.client_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ balance: results.length > 0 ? results[0].balance : 0 });
    });
});

// --- GET CONFIRMED PURCHASES (FOR RETURNS) ---
router.get('/purchases/confirmed', (req, res) => {
    const db = getDb(req);
    const sql = `
        SELECT p.*, v.name as supplier_name 
        FROM purchases p 
        JOIN vendors v ON p.supplier_id = v.id 
        WHERE p.client_id = ? AND p.status = 'CONFIRMED'
        ORDER BY p.purchase_date DESC
    `;
    db.query(sql, [req.user.client_id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// --- GET PURCHASE ITEMS (FOR RETURNS) ---
router.get('/purchases/:id/items', (req, res) => {
    const db = getDb(req);
    const sql = `
        SELECT pi.*, m.name as medicine_name, m.strength
        FROM purchase_items pi
        JOIN medicines m ON pi.medicine_id = m.id
        WHERE pi.purchase_id = ?
    `;
    db.query(sql, [req.params.id], (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// --- PROCESS PURCHASE RETURN ---
router.post('/purchases/return', async (req, res) => {
    const db = getDb(req);
    const { purchase_id, return_date, notes, items } = req.body;
    const client_id = req.user.client_id;
    const user_id = req.user.id;

    const return_no = `PR-${Date.now()}`;

    db.beginTransaction(async (err) => {
        if (err) return res.status(500).json({ error: err.message });

        try {
            let total_amount = 0;
            items.forEach(i => {
                total_amount += parseFloat(i.line_total || 0);
            });

            // 1. Create Return Header
            const [rResult] = await db.promise().query(
                'INSERT INTO purchase_returns (purchase_id, client_id, return_no, return_date, total_amount, notes, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
                [purchase_id, client_id, return_no, return_date, total_amount, notes, user_id]
            );
            const return_id = rResult.insertId;

            // 2. Create Return Items & Update Stock
            for (const item of items) {
                await db.promise().query(
                    'INSERT INTO purchase_return_items (return_id, medicine_id, batch_no, qty, rate, line_total) VALUES (?, ?, ?, ?, ?, ?)',
                    [return_id, item.medicine_id, item.batch_no, item.qty, item.rate, item.line_total]
                );

                // Update Stock Batch
                const [batches] = await db.promise().query(
                    'SELECT id, quantity FROM stocks WHERE medicine_id = ? AND batch_number = ? AND client_id = ?',
                    [item.medicine_id, item.batch_no, client_id]
                );

                if (batches.length > 0) {
                    if (batches[0].quantity < item.qty) {
                        throw new Error(`Insufficient stock for ${item.medicine_id} batch ${item.batch_no}`);
                    }
                    await db.promise().query('UPDATE stocks SET quantity = quantity - ? WHERE id = ?', [item.qty, batches[0].id]);
                } else {
                    throw new Error(`Batch ${item.batch_no} not found in stock`);
                }
            }

            // 3. Update Supplier Ledger
            const [pRes] = await db.promise().query('SELECT supplier_id FROM purchases WHERE id = ?', [purchase_id]);
            const supplier_id = pRes[0].supplier_id;

            // Updated: Also update current_due in vendors table (Safe update with COALESCE)
            await db.promise().query(
                'UPDATE vendors SET current_due = COALESCE(current_due, 0) - ? WHERE id = ? AND client_id = ?',
                [total_amount, supplier_id, client_id]
            );

            const [lastLedger] = await db.promise().query(
                'SELECT balance FROM supplier_ledger WHERE supplier_id = ? AND client_id = ? ORDER BY id DESC LIMIT 1',
                [supplier_id, client_id]
            );
            const old_balance = lastLedger.length > 0 ? parseFloat(lastLedger[0].balance) : 0;
            const new_balance = old_balance - total_amount;

            await db.promise().query(
                'INSERT INTO supplier_ledger (supplier_id, client_id, transaction_type, transaction_id, debit, credit, balance, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                [supplier_id, client_id, 'PURCHASE_RETURN', return_id, total_amount, 0, new_balance, `Purchase Return: ${return_no} for GRN ID: ${purchase_id}`]
            );

            db.commit((err) => {
                if (err) throw err;
                res.json({ message: 'Purchase return processed successfully', return_id });
            });
        } catch (error) {
            db.rollback(() => {
                res.status(500).json({ error: error.message });
            });
        }
    });
});

module.exports = router;

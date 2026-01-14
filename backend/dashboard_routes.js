const express = require('express');
const router = express.Router();

// Helper to execute query
const query = (req, sql, params) => {
    return new Promise((resolve, reject) => {
        req.app.get('db').query(sql, params, (err, results) => {
            if (err) reject(err);
            else resolve(results);
        });
    });
};

// 1. KPI Endpoint
router.get('/dashboard/kpi', async (req, res) => {
    try {
        const today = new Date().toISOString().slice(0, 10);

        // A. Sales Today
        const salesSql = `
            SELECT 
                COALESCE(SUM(grand_total), 0) as total_amount, 
                COUNT(*) as count,
                COALESCE(SUM(CASE WHEN payment_category = 'CASH' THEN grand_total ELSE 0 END), 0) as cash_amount,
                COALESCE(SUM(CASE WHEN payment_category = 'DIGITAL' THEN grand_total ELSE 0 END), 0) as digital_amount
            FROM sales 
            WHERE DATE(created_at) = CURDATE()
        `;
        const [sales] = await query(req, salesSql);

        // B. Estimated Profit Today (Selling - Purchase) * Qty
        // Using stocks.purchase_price if available, else 0
        const profitSql = `
            SELECT 
                COALESCE(SUM((si.unit_price - COALESCE(s.purchase_price, 0)) * si.quantity), 0) as profit
            FROM sale_items si
            JOIN sales sa ON si.sale_id = sa.id
            LEFT JOIN stocks s ON si.medicine_id = s.medicine_id AND si.batch_no = s.batch_number
            WHERE DATE(sa.created_at) = CURDATE()
        `;
        const [profit] = await query(req, profitSql);

        // C. Purchases Today (Confirmed)
        const purchaseSql = `
            SELECT 
                COALESCE(SUM(total_amount), 0) as total_amount, 
                COUNT(*) as count 
            FROM purchases 
            WHERE status = 'CONFIRMED' AND DATE(created_at) = CURDATE()
        `;
        const [purchases] = await query(req, purchaseSql);

        // D. Stock Summary
        const stockSql = `
            SELECT 
                COUNT(DISTINCT medicine_id) as products, 
                COALESCE(SUM(quantity), 0) as total_qty 
            FROM stocks
        `;
        const [stock] = await query(req, stockSql);

        // Low Stock (Fixed threshold 10 for now) & Expiring (90 days)
        const alertsSql = `
            SELECT 
                (SELECT COUNT(*) FROM stocks WHERE quantity < 10) as low_stock,
                (SELECT COUNT(*) FROM stocks WHERE expiry_date <= DATE_ADD(CURDATE(), INTERVAL 90 DAY)) as expiring
        `;
        const [alerts] = await query(req, alertsSql);

        res.json({
            sales: sales,
            profit: profit.profit,
            purchases: purchases,
            stock: { ...stock, ...alerts },
            due: { customer: 0, supplier: 0 } // Placeholder until ledgers are implemented
        });

    } catch (err) {
        console.error("KPI Error:", err);
        res.status(500).json({ error: err.message });
    }
});

// 2. Charts Endpoint
router.get('/dashboard/charts', async (req, res) => {
    try {
        // Sales Trend (Last 30 Days)
        const trendSql = `
            SELECT DATE(created_at) as date, SUM(grand_total) as amount 
            FROM sales 
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) 
            GROUP BY DATE(created_at) 
            ORDER BY date
        `;
        const trend = await query(req, trendSql);

        // Payment Mix (Today)
        const mixSql = `
            SELECT payment_category, COUNT(*) as count, SUM(grand_total) as amount 
            FROM sales 
            WHERE DATE(created_at) = CURDATE() 
            GROUP BY payment_category
        `;
        const mix = await query(req, mixSql);

        res.json({
            trend,
            mix
        });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 3. Alerts Endpoint
router.get('/dashboard/alerts', async (req, res) => {
    try {
        // Expiry (Top 10)
        const expirySql = `
            SELECT 
                s.id, m.name as medicine_name, s.batch_number, s.expiry_date, s.quantity,
                v.name as vendor_name
            FROM stocks s
            JOIN medicines m ON s.medicine_id = m.id
            LEFT JOIN vendors v ON s.vendor_id = v.id
            WHERE s.expiry_date <= DATE_ADD(CURDATE(), INTERVAL 90 DAY)
            ORDER BY s.expiry_date ASC
            LIMIT 10
        `;
        const expiry = await query(req, expirySql);

        // Low Stock (Top 10)
        const lowStockSql = `
            SELECT 
                s.id, m.name as medicine_name, s.batch_number, s.quantity, 10 as threshold,
                v.name as vendor_name, s.expiry_date
            FROM stocks s
            JOIN medicines m ON s.medicine_id = m.id
            LEFT JOIN vendors v ON s.vendor_id = v.id
            WHERE s.quantity < 10
            ORDER BY s.quantity ASC
            LIMIT 10
        `;
        const lowStock = await query(req, lowStockSql);

        res.json({ expiry, lowStock });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 4. Activity Endpoint
router.get('/dashboard/activity', async (req, res) => {
    try {
        // Recent Audit Logs
        const logsSql = `
            SELECT al.action, al.details, al.created_at, u.name as user
            FROM audit_logs al
            LEFT JOIN users u ON al.user_id = u.id
            ORDER BY al.created_at DESC
            LIMIT 20
        `;
        const logs = await query(req, logsSql);
        res.json(logs);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

module.exports = router;

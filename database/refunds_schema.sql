-- Refunds table
CREATE TABLE IF NOT EXISTS refunds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    refund_id VARCHAR(20) UNIQUE,
    bill_id INT NOT NULL,
    customer_id INT NULL,
    refund_type ENUM('FULL', 'PARTIAL') NOT NULL,
    refund_amount DECIMAL(10,2) NOT NULL,
    payment_mode ENUM('cash', 'digital', 'credit') NOT NULL,
    reason ENUM('wrong_item', 'expired', 'damaged', 'returned', 'other') NOT NULL,
    reason_notes TEXT,
    status ENUM('PENDING', 'APPROVED', 'REJECTED') DEFAULT 'PENDING',
    requested_by INT NOT NULL,
    approved_by INT NULL,
    admin_remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP NULL,
    FOREIGN KEY (bill_id) REFERENCES sales(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (requested_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

-- Refund items table (for partial refunds)
CREATE TABLE IF NOT EXISTS refund_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    refund_id INT NOT NULL,
    sale_item_id INT NOT NULL,
    medicine_id INT NOT NULL,
    batch_no VARCHAR(50),
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (refund_id) REFERENCES refunds(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
);

-- Indexes for performance
CREATE INDEX idx_refund_status ON refunds(status);
CREATE INDEX idx_refund_bill ON refunds(bill_id);
CREATE INDEX idx_refund_date ON refunds(created_at);

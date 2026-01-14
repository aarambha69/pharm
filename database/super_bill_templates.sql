-- Add Super Admin Bill Templates table
CREATE TABLE IF NOT EXISTS super_bill_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    design_data LONGTEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Add Client Bill Design Assignments table (to link clients with designs)
CREATE TABLE IF NOT EXISTS client_bill_designs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    bill_design_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_client (client_id),
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (bill_design_id) REFERENCES super_bill_templates(id) ON DELETE CASCADE
);

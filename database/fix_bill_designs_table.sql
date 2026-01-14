-- Fix bill_designs table by recreating it with correct schema
-- First, drop any foreign key constraints that reference this table
SET FOREIGN_KEY_CHECKS = 0;

-- Drop the incorrectly structured bill_designs table
DROP TABLE IF EXISTS bill_designs;

-- Bill Designs Table (for custom bill templates per client - ADMIN users)
CREATE TABLE bill_designs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    paper_size VARCHAR(20) DEFAULT 'A5',
    orientation VARCHAR(20) DEFAULT 'PORTRAIT',
    config TEXT,
    stamp_image MEDIUMBLOB,
    signature_image MEDIUMBLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_client_design (client_id),
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

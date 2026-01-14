USE Pharmacy_Management;

-- Bill Designs Table (for custom bill templates)
CREATE TABLE IF NOT EXISTS bill_designs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    paper_size VARCHAR(20) DEFAULT 'A5',
    orientation VARCHAR(20) DEFAULT 'PORTRAIT',
    config TEXT,
    stamp_image MEDIUMBLOB,
    signature_image MEDIUMBLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

-- Also add any missing columns to other tables if needed
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS profile_pic TEXT,
ADD COLUMN IF NOT EXISTS permissions TEXT;

ALTER TABLE clients 
ADD COLUMN IF NOT EXISTS logo_path VARCHAR(255),
ADD COLUMN IF NOT EXISTS owner_photo_path VARCHAR(255);

ALTER TABLE announcements
ADD COLUMN IF NOT EXISTS target_client_id INT,
ADD COLUMN IF NOT EXISTS expiry_date DATE;

-- Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    user_id INT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

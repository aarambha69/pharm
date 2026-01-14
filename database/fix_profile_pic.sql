-- Fix profile_pic column to support large base64 images
ALTER TABLE users MODIFY COLUMN profile_pic LONGTEXT;

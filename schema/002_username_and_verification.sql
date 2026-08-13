-- Run once against tourneydatabase after schema/users.sql.
ALTER TABLE users
    ADD COLUMN username VARCHAR(50) NOT NULL UNIQUE AFTER name,
    ADD COLUMN email_verified_at TIMESTAMP NULL,
    ADD COLUMN verification_token_hash VARCHAR(64) NULL,
    ADD COLUMN verification_token_expires_at TIMESTAMP NULL;

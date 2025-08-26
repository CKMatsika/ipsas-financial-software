-- IPSAS Financial Software Database Initialization
-- PostgreSQL 12+ compatible

-- Create database if it doesn't exist
-- Note: This should be run as a superuser or database owner

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create custom types if needed
DO $$
BEGIN
    -- Create enum types for better data integrity
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role_enum') THEN
        CREATE TYPE user_role_enum AS ENUM (
            'admin', 'accountant', 'auditor', 'viewer', 'manager'
        );
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'entry_status_enum') THEN
        CREATE TYPE entry_status_enum AS ENUM (
            'draft', 'pending', 'approved', 'posted', 'rejected', 'cancelled'
        );
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'statement_type_enum') THEN
        CREATE TYPE statement_type_enum AS ENUM (
            'sfp', 'sfp_performance', 'scf', 'scna', 'ppes', 'ips', 
            'notes', 'budget_vs_actual', 'segment', 'consolidated'
        );
    END IF;
END$$;

-- Create database user for application (optional)
-- CREATE USER ipsas_user WITH PASSWORD 'secure_password_here';
-- GRANT ALL PRIVILEGES ON DATABASE ipsas_financial TO ipsas_user;

-- Set default privileges for future tables
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ipsas_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ipsas_user;

-- Create indexes for better performance
-- These will be created automatically by Django, but you can add custom ones here

-- Create views for common queries (optional)
-- CREATE OR REPLACE VIEW active_accounts AS
-- SELECT * FROM chart_of_accounts WHERE is_active = true;

-- Create functions for common calculations (optional)
-- CREATE OR REPLACE FUNCTION calculate_account_balance(account_id INTEGER)
-- RETURNS DECIMAL AS $$
-- BEGIN
--     -- Implementation here
--     RETURN 0.00;
-- END;
-- $$ LANGUAGE plpgsql;

-- Grant execute permissions on functions
-- GRANT EXECUTE ON FUNCTION calculate_account_balance(INTEGER) TO ipsas_user;

-- Create initial data (optional)
-- INSERT INTO chart_of_accounts_categories (name, code, category_type, description) VALUES
-- ('Assets', 'A', 'assets', 'All asset accounts'),
-- ('Liabilities', 'L', 'liabilities', 'All liability accounts'),
-- ('Equity', 'E', 'equity', 'All equity accounts'),
-- ('Revenue', 'R', 'revenue', 'All revenue accounts'),
-- ('Expenses', 'X', 'expenses', 'All expense accounts');

COMMENT ON DATABASE ipsas_financial IS 'IPSAS Financial Software Database - International Public Sector Accounting Standards compliant financial management system';

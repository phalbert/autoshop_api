CREATE OR REPLACE VIEW account_holders AS
SELECT 'customer' as group, uuid, name as name FROM customer UNION
SELECT 'vendor' as group, uuid, name FROM vendor UNION
SELECT 'entity' as group, uuid, name FROM entity UNION
SELECT 'payment type' as group, uuid, name FROM payment_type;


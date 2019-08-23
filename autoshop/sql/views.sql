CREATE OR REPLACE VIEW account_holders AS
SELECT 'customer' as group, uuid, name as name FROM customer UNION
SELECT 'vendor' as group, uuid, name FROM vendor UNION
SELECT 'entity' as group, uuid, name FROM entity UNION
SELECT 'payment type' as group, uuid, name FROM payment_type;

CREATE FUNCTION get_sales(start_date date, end_date date) RETURNS NUMERIC AS $$
    SELECT sum(amount) FROM item_log
    WHERE category='sale'
    and date_created>=start_date
    and date_created<=end_date;
$$ LANGUAGE SQL;

CREATE FUNCTION get_expenses(start_date date, end_date date) RETURNS NUMERIC AS $$
    SELECT sum(cast(amount as NUMERIC)) FROM expense
    WHERE date_created>=start_date
    and date_created<=end_date;
$$ LANGUAGE SQL;

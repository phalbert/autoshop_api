CREATE OR REPLACE VIEW account_holders AS
SELECT 'customer' as group, uuid, name as name FROM customer UNION
SELECT 'vendor' as group, uuid, name FROM vendor UNION
SELECT 'entity' as group, uuid, name FROM entity UNION
SELECT 'payment type' as group, uuid, name FROM payment_type;

CREATE OR REPLACE FUNCTION get_sales(date DATE) RETURNS NUMERIC AS $$
    SELECT sum(cast(amount as NUMERIC)) FROM item_log
    WHERE TO_CHAR(date_created :: DATE, 'yyyy-mm-dd')=cast(date as VARCHAR)
$$ LANGUAGE SQL;



CREATE OR REPLACE FUNCTION get_expenses(date DATE) RETURNS NUMERIC AS $$
    SELECT sum(cast(amount as NUMERIC)) FROM expense
    WHERE TO_CHAR(date_created :: DATE, 'yyyy-mm-dd')=cast(date as VARCHAR)
$$ LANGUAGE SQL;



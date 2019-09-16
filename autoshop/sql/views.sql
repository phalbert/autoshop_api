CREATE OR REPLACE VIEW account_holders AS
SELECT 'customer' as group, uuid, name as name FROM customer UNION
SELECT 'vendor' as group, uuid, name FROM vendor UNION
SELECT 'entity' as group, uuid, name FROM entity UNION
SELECT 'commission account' as group, uuid, name FROM commission_account UNION
SELECT 'payment type' as group, uuid, name FROM payment_type;

CREATE OR REPLACE FUNCTION get_sales(date DATE) RETURNS NUMERIC AS $$
    SELECT sum(cast(amount as NUMERIC)) FROM item_log
    WHERE TO_CHAR(date_created :: DATE, 'yyyy-mm-dd')=cast(date as VARCHAR)
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_expenses(date DATE) RETURNS NUMERIC AS $$
    SELECT sum(cast(amount as NUMERIC)) FROM expense
    WHERE TO_CHAR(date_created :: DATE, 'yyyy-mm-dd')=cast(date as VARCHAR)
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_total_sales(start_date date, end_date date) RETURNS NUMERIC AS $$
    SELECT sum(amount) FROM item_log
    WHERE category='sale'
    and date_created>=start_date
    and date_created<=end_date;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_total_expenses(start_date date, end_date date) RETURNS NUMERIC AS $$
    SELECT sum(cast(amount as NUMERIC)) FROM expense
    WHERE date_created>=start_date
    and date_created<=end_date;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_item_trans(item VARCHAR, category_id VARCHAR, date DATE) RETURNS NUMERIC AS $$
    SELECT sum(cast(amount as NUMERIC)) FROM item_log
    WHERE TO_CHAR(date_created :: DATE, 'yyyy-mm-dd')=cast(date as VARCHAR)
    and item_log.item_id=item and item_log.category=category_id
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_item_total(item VARCHAR, category_id VARCHAR, date DATE) RETURNS NUMERIC AS $$
    SELECT sum(cast(quantity as NUMERIC)) FROM item_log
    WHERE TO_CHAR(date_created :: DATE, 'yyyy-mm-dd')=cast(date as VARCHAR)
    and item_log.item_id=item and item_log.category=category_id
$$ LANGUAGE SQL;
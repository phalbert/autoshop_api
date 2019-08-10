CREATE OR REPLACE VIEW item_accounts AS
SELECT 'item' as group, uuid, id, name as name FROM item UNION
SELECT 'vendor' as group, uuid, id, name FROM vendor UNION
SELECT 'entity' as group, uuid, id, name FROM entity;


CREATE OR REPLACE VIEW item_ledger(
	entry_id,
    log_id,
    reference,
    account_id,
    item_id,
	tran_category,
    quantity,
	amount,
	entity_id,
	date_created,
	accounting_date,
	accounting_period
) AS
	SELECT
		item_log.id,
        item_log.uuid,
        item_log.reference,
		item_log.credit,
		item_log.item_id,
		'credit',
        item_log.quantity,
		item_log.amount,
		item_log.entity_id,
		item_log.date_created,
		item_log.accounting_date,
    	item_log.accounting_period
	FROM
		item_log
	UNION ALL
	SELECT
	    item_log.id,
        item_log.uuid,
        item_log.reference,
		item_log.debit,
		item_log.item_id,
		'debit',
        (0 - item_log.quantity),
		(0.0 - item_log.amount),
		item_log.entity_id,
		item_log.date_created,
		item_log.accounting_date,
    	item_log.accounting_period
	FROM
		item_log;

CREATE MATERIALIZED VIEW item_balances(
	-- Materialized so financial reports run fast.
	-- Modification of accounts and item_log will require a
	-- REFRESH MATERIALIZED VIEW, which we can trigger
	-- automatically.
	uuid, -- INTEGER REFERENCES accounts(id) NOT NULL UNIQUE
	quantity, -- INTEGER NOT NULL
    balance -- NUMERIC NOT NULL
) AS
	SELECT
		item_accounts.uuid,
        COALESCE(sum(item_ledger.quantity), 0.0),
		COALESCE(sum(item_ledger.amount), 0.0)
	FROM
		item_accounts
		LEFT OUTER JOIN item_ledger
		ON item_accounts.uuid = item_ledger.account_id
	GROUP BY item_accounts.uuid;

CREATE UNIQUE INDEX ON item_balances(uuid);

CREATE OR REPLACE FUNCTION update_item_balances() RETURNS TRIGGER AS $$
BEGIN
	REFRESH MATERIALIZED VIEW item_balances;
	RETURN NULL;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_fix_balance_item_log
AFTER INSERT 
OR UPDATE OF quantity, amount, credit, debit 
OR DELETE OR TRUNCATE
ON item_log
FOR EACH STATEMENT
EXECUTE PROCEDURE update_item_balances();

-- -- CREATE TRIGGER trigger_fix_balance_accounts
-- -- AFTER INSERT 
-- -- OR UPDATE OF uuid 
-- -- OR DELETE OR TRUNCATE
-- -- ON item_accounts
-- -- FOR EACH STATEMENT
-- -- EXECUTE PROCEDURE update_item_balances();
-- --  Views cannot have TRUNCATE triggers

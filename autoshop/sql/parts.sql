CREATE OR REPLACE VIEW part_accounts AS
SELECT 'part' as group, uuid, id, name as name FROM part UNION
SELECT 'vendor' as group, uuid, id, name FROM vendor UNION
SELECT 'entity' as group, uuid, id, name FROM entity;


CREATE OR REPLACE VIEW part_ledger(
	entry_id,
    log_id,
    reference,
    account_id,
    part_id,
	tran_category,
    quantity,
	amount,
	entity_id,
	date_created,
	accounting_date,
	accounting_period
) AS
	SELECT
		part_log.id,
        part_log.uuid,
        part_log.reference,
		part_log.credit,
		part_log.part_id,
		'credit',
        part_log.quantity,
		part_log.amount,
		part_log.entity_id,
		part_log.date_created,
		part_log.accounting_date,
    	part_log.accounting_period
	FROM
		part_log
	UNION ALL
	SELECT
	    part_log.id,
        part_log.uuid,
        part_log.reference,
		part_log.credit,
		part_log.part_id,
		'debit',
        (0 - part_log.quantity),
		(0.0 - part_log.amount),
		part_log.entity_id,
		part_log.date_created,
		part_log.accounting_date,
    	part_log.accounting_period
	FROM
		part_log;

CREATE MATERIALIZED VIEW part_balances(
	-- Materialized so financial reports run fast.
	-- Modification of accounts and part_log will require a
	-- REFRESH MATERIALIZED VIEW, which we can trigger
	-- automatically.
	uuid, -- INTEGER REFERENCES accounts(id) NOT NULL UNIQUE
	quantity, -- INTEGER NOT NULL
    balance -- NUMERIC NOT NULL
) AS
	SELECT
		part_accounts.uuid,
        COALESCE(sum(part_ledger.quantity), 0.0),
		COALESCE(sum(part_ledger.amount), 0.0)
	FROM
		part_accounts
		LEFT OUTER JOIN part_ledger
		ON part_accounts.uuid = part_ledger.account_id
	GROUP BY part_accounts.uuid;

CREATE UNIQUE INDEX ON part_balances(uuid);

CREATE OR REPLACE FUNCTION update_part_balances() RETURNS TRIGGER AS $$
BEGIN
	REFRESH MATERIALIZED VIEW part_balances;
	RETURN NULL;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_fix_balance_part_log
AFTER INSERT 
OR UPDATE OF quantity, amount, credit, debit 
OR DELETE OR TRUNCATE
ON part_log
FOR EACH STATEMENT
EXECUTE PROCEDURE update_part_balances();

-- -- CREATE TRIGGER trigger_fix_balance_accounts
-- -- AFTER INSERT 
-- -- OR UPDATE OF uuid 
-- -- OR DELETE OR TRUNCATE
-- -- ON part_accounts
-- -- FOR EACH STATEMENT
-- -- EXECUTE PROCEDURE update_part_balances();
-- --  Views cannot have TRUNCATE triggers

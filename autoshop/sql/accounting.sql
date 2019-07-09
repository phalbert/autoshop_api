CREATE INDEX ON entries(credit);
CREATE INDEX ON entries(debit);

CREATE VIEW account_ledgers(
	entry_id,
    reference,
    account_id,
    tran_type,
	tran_category,
	category,
	amount,
	entity_id,
	date_created,
	accounting_date,
	accounting_period
) AS
	SELECT
		entries.id,
        entries.reference,
		entries.credit,
		entries.tran_type,
		'credit',
		entries.category,
		entries.amount,
		entries.entity_id,
		entries.date_created,
		entries.accounting_date,
    	entries.accounting_period
	FROM
		entries
	UNION ALL
	SELECT
	    entries.id,
        entries.reference,
		entries.debit,
		entries.tran_type,
		'debit',
		entries.category,
		(0.0 - entries.amount),
		entries.entity_id,
		entries.date_created,
		entries.accounting_date,
    	entries.accounting_period
	FROM
		entries;

CREATE MATERIALIZED VIEW account_balances(
	-- Materialized so financial reports run fast.
	-- Modification of accounts and entries will require a
	-- REFRESH MATERIALIZED VIEW, which we can trigger
	-- automatically.
	id, -- INTEGER REFERENCES accounts(id) NOT NULL UNIQUE
	balance -- NUMERIC NOT NULL
) AS
	SELECT
		accounts.id,
		COALESCE(sum(account_ledgers.amount), 0.0)
	FROM
		accounts
		LEFT OUTER JOIN account_ledgers
		ON accounts.id = account_ledgers.account_id
	GROUP BY accounts.id;

CREATE UNIQUE INDEX ON account_balances(id);

CREATE OR REPLACE FUNCTION update_balances() RETURNS TRIGGER AS $$
BEGIN
	REFRESH MATERIALIZED VIEW account_balances;
	RETURN NULL;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_fix_balance_entries
AFTER INSERT 
OR UPDATE OF amount, credit, debit 
OR DELETE OR TRUNCATE
ON entries
FOR EACH STATEMENT
EXECUTE PROCEDURE update_balances();

CREATE TRIGGER trigger_fix_balance_accounts
AFTER INSERT 
OR UPDATE OF id 
OR DELETE OR TRUNCATE
ON accounts
FOR EACH STATEMENT
EXECUTE PROCEDURE update_balances();

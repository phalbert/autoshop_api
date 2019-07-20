CREATE OR REPLACE VIEW account_holders AS
SELECT 'customer' as group, uuid, name as name FROM customer UNION
SELECT 'vendor' as group, uuid, name FROM vendor UNION
SELECT 'entity' as group, uuid, name FROM entity UNION
SELECT 'payment type' as group, uuid, name FROM payment_type;


CREATE OR REPLACE MATERIALIZED VIEW account_balances(
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

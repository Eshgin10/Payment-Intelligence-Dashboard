CREATE TABLE IF NOT EXISTS countries (
 country_code char(2) PRIMARY KEY, country_name text NOT NULL,
 currency char(3) NOT NULL, eur_rate numeric(12,6) NOT NULL CHECK (eur_rate > 0)
);
CREATE TABLE IF NOT EXISTS payment_methods (payment_method_id integer PRIMARY KEY, name text NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS merchants (merchant_id integer PRIMARY KEY, merchant_name text NOT NULL);
CREATE TABLE IF NOT EXISTS failure_reasons (failure_reason_id integer PRIMARY KEY, name text NOT NULL UNIQUE, retryable boolean NOT NULL);
CREATE TABLE IF NOT EXISTS customers (
 customer_id integer PRIMARY KEY, customer_name text NOT NULL,
 customer_segment text NOT NULL CHECK (customer_segment IN ('Consumer','SMB','Enterprise')),
 country_code char(2) NOT NULL REFERENCES countries,
 signup_date date NOT NULL, risk_level text NOT NULL CHECK (risk_level IN ('Low','Medium','High')),
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS payments (
 payment_id text PRIMARY KEY, customer_id integer NOT NULL REFERENCES customers,
 merchant_id integer NOT NULL REFERENCES merchants,
 payment_method_id integer NOT NULL REFERENCES payment_methods,
 country_code char(2) NOT NULL REFERENCES countries,
 amount numeric(14,2) NOT NULL CHECK (amount > 0), currency char(3) NOT NULL,
 amount_eur numeric(14,2) NOT NULL CHECK (amount_eur > 0),
 status text NOT NULL CHECK (status IN ('successful','failed','pending','recovered','refunded')),
 failure_reason_id integer REFERENCES failure_reasons,
 initial_failure_reason_id integer REFERENCES failure_reasons,
 attempt_count smallint NOT NULL CHECK (attempt_count BETWEEN 1 AND 3),
 payment_date timestamptz NOT NULL, settled_at timestamptz,
 is_outlier boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL DEFAULT now(),
 CHECK ((status = 'failed') = (failure_reason_id IS NOT NULL)),
 CHECK ((status IN ('successful','recovered','refunded')) = (settled_at IS NOT NULL)),
 CHECK (settled_at IS NULL OR settled_at >= payment_date),
 CHECK (status <> 'recovered' OR (attempt_count > 1 AND initial_failure_reason_id IS NOT NULL))
);
CREATE TABLE IF NOT EXISTS payment_attempts (
 attempt_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 payment_id text NOT NULL REFERENCES payments ON DELETE CASCADE,
 attempt_number smallint NOT NULL CHECK (attempt_number BETWEEN 1 AND 3),
 attempt_date timestamptz NOT NULL,
 status text NOT NULL CHECK (status IN ('successful','failed','pending')),
 failure_reason_id integer REFERENCES failure_reasons,
 processor_response text NOT NULL,
 UNIQUE(payment_id, attempt_number),
 CHECK ((status = 'failed') = (failure_reason_id IS NOT NULL))
);
CREATE TABLE IF NOT EXISTS pipeline_runs (
 run_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, completed_at timestamptz NOT NULL DEFAULT now(),
 summary jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS payments_date_idx ON payments(payment_date);
CREATE INDEX IF NOT EXISTS payments_country_date_idx ON payments(country_code,payment_date);
CREATE INDEX IF NOT EXISTS payments_status_date_idx ON payments(status,payment_date DESC);
CREATE INDEX IF NOT EXISTS payments_customer_idx ON payments(customer_id);
CREATE INDEX IF NOT EXISTS payments_method_date_idx ON payments(payment_method_id,payment_date);

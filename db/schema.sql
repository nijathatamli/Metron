-- ============================================================================
-- Metron — PostgreSQL schema
-- ============================================================================
-- Run: psql -U metron -d metron -f db/schema.sql
-- ============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── 1. users ────────────────────────────────────────────────────────────────

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metro_card_id   VARCHAR(32)  NOT NULL UNIQUE,      -- physical metro card number
    coin_balance    NUMERIC(12,2) NOT NULL DEFAULT 0.00
                    CHECK (coin_balance >= 0),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_metro_card ON users (metro_card_id);

-- ── 2. metro_trips ──────────────────────────────────────────────────────────

CREATE TABLE metro_trips (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    station_id      VARCHAR(16)  NOT NULL,              -- e.g. "IC-01"
    direction       VARCHAR(10)  NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    timestamp       TIMESTAMPTZ  NOT NULL,
    density_score   NUMERIC(5,4) NOT NULL CHECK (density_score BETWEEN 0 AND 1),
    fare_azn        NUMERIC(8,2) NOT NULL DEFAULT 0.50,
    cashback_percent INTEGER     NOT NULL CHECK (cashback_percent BETWEEN 0 AND 100),
    coins_earned    NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_trips_user      ON metro_trips (user_id);
CREATE INDEX idx_trips_station   ON metro_trips (station_id, timestamp);
CREATE INDEX idx_trips_timestamp ON metro_trips (timestamp);

-- ── 3. coin_transactions ────────────────────────────────────────────────────

CREATE TYPE coin_tx_type AS ENUM ('earn', 'spend');

CREATE TABLE coin_transactions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type            coin_tx_type  NOT NULL,
    amount          NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    reference_id    UUID,                                -- FK to metro_trips.id or redemptions.id
    description     TEXT,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE INDEX idx_coin_tx_user    ON coin_transactions (user_id);
CREATE INDEX idx_coin_tx_type    ON coin_transactions (user_id, type);
CREATE INDEX idx_coin_tx_ref     ON coin_transactions (reference_id);

-- ── 4. partners ─────────────────────────────────────────────────────────────

CREATE TABLE partners (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(128)  NOT NULL,
    category            VARCHAR(64)   NOT NULL,          -- "cafe", "restaurant", …
    api_key             VARCHAR(128)  NOT NULL UNIQUE,
    settlement_balance  NUMERIC(14,2) NOT NULL DEFAULT 0.00,
    is_active           BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE INDEX idx_partners_active ON partners (is_active) WHERE is_active = TRUE;

-- ── 5. redemptions ──────────────────────────────────────────────────────────

CREATE TABLE redemptions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    partner_id      UUID          NOT NULL REFERENCES partners(id) ON DELETE RESTRICT,
    product_price   NUMERIC(10,2) NOT NULL CHECK (product_price >= 0),
    coins_used      NUMERIC(12,2) NOT NULL CHECK (coins_used >= 0),
    cash_paid       NUMERIC(10,2) NOT NULL CHECK (cash_paid >= 0),
    idempotency_key VARCHAR(128)  UNIQUE,                -- prevents duplicate transactions
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE INDEX idx_redemptions_user    ON redemptions (user_id);
CREATE INDEX idx_redemptions_partner ON redemptions (partner_id);
CREATE INDEX idx_redemptions_idemp   ON redemptions (idempotency_key)
    WHERE idempotency_key IS NOT NULL;

-- ── 6. View: user_coin_summary ──────────────────────────────────────────────

CREATE OR REPLACE VIEW user_coin_summary AS
SELECT
    u.id                                            AS user_id,
    u.metro_card_id,
    u.coin_balance                                  AS current_balance,
    COALESCE(e.total_earned, 0)                     AS total_earned,
    COALESCE(s.total_spent,  0)                     AS total_spent,
    COALESCE(e.earn_count,   0)                     AS earn_transactions,
    COALESCE(s.spend_count,  0)                     AS spend_transactions,
    u.created_at                                    AS member_since
FROM users u
LEFT JOIN (
    SELECT user_id,
           SUM(amount)   AS total_earned,
           COUNT(*)      AS earn_count
    FROM   coin_transactions
    WHERE  type = 'earn'
    GROUP  BY user_id
) e ON e.user_id = u.id
LEFT JOIN (
    SELECT user_id,
           SUM(amount)   AS total_spent,
           COUNT(*)      AS spend_count
    FROM   coin_transactions
    WHERE  type = 'spend'
    GROUP  BY user_id
) s ON s.user_id = u.id;

-- Personal Finance Manager – MySQL schema
-- Run once to create the database and table.
--
-- Usage:
--   mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS accounting3
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE accounting3;

CREATE TABLE IF NOT EXISTS transactions (
    -- Internal surrogate key
    id                  INT UNSIGNED        NOT NULL AUTO_INCREMENT,

    -- Core fields
    date                DATE                NOT NULL COMMENT 'Datum zauctovani – posting/accounting date',
    value_date          DATE                         COMMENT 'Datum provedeni – execution/value date',
    description         VARCHAR(500)        NOT NULL DEFAULT '' COMMENT 'Popis pro me',
    amount              DECIMAL(15, 4)      NOT NULL COMMENT 'Castka',
    currency            VARCHAR(10)         NOT NULL DEFAULT '' COMMENT 'Mena',

    -- Counterparty
    counterparty_id     VARCHAR(100)        NOT NULL DEFAULT '' COMMENT 'Protistrana',
    counterparty_name   VARCHAR(255)        NOT NULL DEFAULT '' COMMENT 'Nazev protiuctu',

    -- Original (foreign-currency) amount
    original_amount     DECIMAL(15, 4)               COMMENT 'Originalni castka',
    original_currency   VARCHAR(10)         NOT NULL DEFAULT '' COMMENT 'Originalni mena',
    exchange_rate       DECIMAL(15, 6)               COMMENT 'Smenny kurz',

    -- Czech payment symbols
    variable_symbol     VARCHAR(20)         NOT NULL DEFAULT '' COMMENT 'VS',
    constant_symbol     VARCHAR(20)         NOT NULL DEFAULT '' COMMENT 'KS',
    specific_symbol     VARCHAR(20)         NOT NULL DEFAULT '' COMMENT 'SS',

    -- Bank transaction metadata
    transaction_id      VARCHAR(100)                 COMMENT 'Identifikace transakce – NULL when absent (allows multiple NULLs)',
    transaction_type    VARCHAR(100)        NOT NULL DEFAULT '' COMMENT 'Typ transakce',

    -- Messages / references
    recipient_message   VARCHAR(500)        NOT NULL DEFAULT '' COMMENT 'Zprava pro prijemce',
    payment_reference   VARCHAR(255)        NOT NULL DEFAULT '' COMMENT 'Reference platby',
    bic_swift           VARCHAR(20)         NOT NULL DEFAULT '' COMMENT 'BIC / SWIFT',

    -- Fee
    fee                 DECIMAL(15, 4)               COMMENT 'Poplatek',

    PRIMARY KEY (id),

    -- Bank transaction IDs are unique when present; NULL is allowed multiple times
    -- (MySQL UNIQUE treats each NULL as distinct, so this is safe)
    UNIQUE KEY uq_transaction_id (transaction_id),

    -- Common query patterns
    KEY idx_date        (date),
    KEY idx_currency    (currency),
    KEY idx_counterparty(counterparty_name(64))
)
ENGINE = InnoDB
DEFAULT CHARSET = utf8mb4
COLLATE = utf8mb4_unicode_ci;

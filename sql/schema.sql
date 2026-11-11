-- Fichiers déjà traités : la contrainte UNIQUE garantit qu'un même contenu
-- n'est inséré qu'une seule fois.
CREATE TABLE IF NOT EXISTS fichier_traite (
    id            BIGSERIAL PRIMARY KEY,
    nom           TEXT        NOT NULL,
    empreinte     CHAR(64)    NOT NULL UNIQUE,
    nb_lignes     INTEGER     NOT NULL CHECK (nb_lignes > 0),
    traite_le     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS transaction_financiere (
    id                   BIGSERIAL PRIMARY KEY,
    fichier_id           BIGINT         NOT NULL REFERENCES fichier_traite (id),
    numero_ligne         INTEGER        NOT NULL,
    datetime_transaction TIMESTAMP      NOT NULL,
    iban_origine         VARCHAR(34)    NOT NULL,
    pays_source          TEXT           NOT NULL,
    banque_source        TEXT           NOT NULL,
    iban_destinataire    VARCHAR(34)    NOT NULL,
    pays_destinataire    TEXT           NOT NULL,
    montant              NUMERIC(14, 2) NOT NULL CHECK (montant > 0),
    flag                 BOOLEAN        NOT NULL,
    UNIQUE (fichier_id, numero_ligne)
);

CREATE INDEX IF NOT EXISTS idx_transaction_flag
    ON transaction_financiere (flag) WHERE flag;

CREATE TABLE IF NOT EXISTS total_envoye_par_iban (
    iban  VARCHAR(34)    PRIMARY KEY,
    total NUMERIC(16, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS total_envoye_par_banque (
    banque TEXT           PRIMARY KEY,
    total  NUMERIC(16, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS total_recu_par_iban (
    iban  VARCHAR(34)    PRIMARY KEY,
    total NUMERIC(16, 2) NOT NULL
);

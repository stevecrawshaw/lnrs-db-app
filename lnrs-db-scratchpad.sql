duckdb

ATTACH 'data/lnrs_3nf_o1.duckdb' AS lnrs_db;

.tables

ATTACH 'md:';

-- md authentication is in the .env variable

CREATE OR REPLACE DATABASE lnrs_3nf_o1 FROM lnrs_db;

.quit
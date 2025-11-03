duckdb

ATTACH 'data/lnrs_3nf_o1.duckdb' AS lnrs_db;

.tables

SELECT COUNT() FROM lnrs_db.apmg_slim_vw;

SELECT COUNT() FROM lnrs_db.measure;

SELECT COUNT() FROM lnrs_db.apmg_slim_vw;

SELECT COUNT() FROM lnrs_db.source_table_recreated_vw;

.quit
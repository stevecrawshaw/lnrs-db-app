-- ====================================================================
-- EXPORT LNRS DATABASE TO MOTHERDUCK WITH FULL CONSTRAINTS
-- ====================================================================
-- This script creates the lnrs_weca database on MotherDuck with:
-- - All table structures with PRIMARY KEY and FOREIGN KEY constraints
-- - All sequences
-- - All data copied in dependency order
-- - All views

-- We need to use this approach rather than copying the local database
-- directly to MotherDuck, as FOREIGN KEY constraints are not preserved
-- when copying a DuckDB database file.

-- Start duckdb CLI before running this script:
duckdb
INSTALL SPATIAL;
LOAD SPATIAL;
-- Connect to local LNRS DuckDB database - Further down
ATTACH 'data/lnrs_3nf_o1.duckdb' AS lnrs;

-- Connect to MotherDuck
ATTACH 'md:';

-- Drop and recreate database
DROP DATABASE IF EXISTS lnrs_weca CASCADE;
CREATE DATABASE lnrs_weca;

-- Set the database context to lnrs_weca
USE lnrs_weca;

-- ====================================================================
-- STEP 1: CREATE SEQUENCES
-- ====================================================================

CREATE SEQUENCE lnrs_weca.seq_measure_type_id START 1;
CREATE SEQUENCE lnrs_weca.seq_stakeholder_id START 1;

-- ====================================================================
-- STEP 2: CREATE PARENT TABLES (NO FOREIGN KEY DEPENDENCIES)
-- ====================================================================

------------------------------------------------------------------
-- MEASURE
------------------------------------------------------------------
CREATE TABLE lnrs_weca.measure (
    measure_id  INTEGER NOT NULL PRIMARY KEY,
    measure     VARCHAR,
    other_priorities_delivered VARCHAR,
    core_supplementary        VARCHAR,
    mapped_unmapped           VARCHAR,
    relevant_map_layer        VARCHAR,
    link_to_further_guidance  VARCHAR,
    concise_measure           VARCHAR
);

------------------------------------------------------------------
-- MEASURE_TYPE
------------------------------------------------------------------
CREATE TABLE lnrs_weca.measure_type (
    measure_type_id INTEGER NOT NULL PRIMARY KEY DEFAULT nextval('seq_measure_type_id'),
    measure_type    VARCHAR
);

------------------------------------------------------------------
-- STAKEHOLDER
------------------------------------------------------------------
CREATE TABLE lnrs_weca.stakeholder (
    stakeholder_id INTEGER NOT NULL PRIMARY KEY DEFAULT nextval('seq_stakeholder_id'),
    stakeholder    VARCHAR
);

------------------------------------------------------------------
-- AREA
------------------------------------------------------------------
CREATE TABLE lnrs_weca.area (
    area_id          INTEGER NOT NULL PRIMARY KEY,
    area_name        VARCHAR,
    area_description VARCHAR,
    area_link        VARCHAR,
    bng_hab_mgt      VARCHAR,
    bng_hab_creation VARCHAR
);

------------------------------------------------------------------
-- PRIORITY
------------------------------------------------------------------
CREATE TABLE lnrs_weca.priority (
    priority_id INTEGER NOT NULL PRIMARY KEY,
    biodiversity_priority           VARCHAR,
    simplified_biodiversity_priority VARCHAR,
    theme                           VARCHAR
);

------------------------------------------------------------------
-- SPECIES
------------------------------------------------------------------
CREATE TABLE lnrs_weca.species (
    taxa VARCHAR,
    common_name VARCHAR,
    assemblage VARCHAR,
    species_link VARCHAR,
    linnaean_name VARCHAR,
    species_id INTEGER PRIMARY KEY,
    usage_key VARCHAR,
    scientific_name VARCHAR,
    status VARCHAR,
    kingdom VARCHAR,
    phylum VARCHAR,
    "order" VARCHAR,
    "family" VARCHAR,
    genus VARCHAR,
    species VARCHAR,
    kingdom_key VARCHAR,
    phylum_key VARCHAR,
    class_key VARCHAR,
    order_key VARCHAR,
    family_key VARCHAR,
    genus_key VARCHAR,
    species_key VARCHAR,
    "synonym" VARCHAR,
    "class" VARCHAR,
    accepted_usage_key VARCHAR,
    verbatim_name VARCHAR,
    verbatim_index BIGINT,
    gbif_species_url VARCHAR,
    image_url VARCHAR,
    license VARCHAR,
    attribution VARCHAR,
    photo_url VARCHAR
);

------------------------------------------------------------------
-- GRANT_TABLE
------------------------------------------------------------------
CREATE TABLE lnrs_weca.grant_table (
    grant_id              VARCHAR NOT NULL PRIMARY KEY,
    grant_name            VARCHAR,
    grant_scheme          VARCHAR,
    url                   VARCHAR,
    grant_summary         VARCHAR
);

------------------------------------------------------------------
-- BENEFITS
------------------------------------------------------------------
CREATE TABLE lnrs_weca.benefits (
    benefit_id INTEGER NOT NULL PRIMARY KEY,
    benefit VARCHAR
);

------------------------------------------------------------------
-- HABITAT
------------------------------------------------------------------
CREATE TABLE lnrs_weca.habitat (
    habitat_id INTEGER NOT NULL PRIMARY KEY,
    habitat VARCHAR
);

------------------------------------------------------------------
-- SOURCE_TABLE (no FKs, used for reference)
------------------------------------------------------------------
CREATE TABLE lnrs_weca.source_table (
    measure_id BIGINT,
    priority_id BIGINT,
    measure VARCHAR,
    other_priorities_delivered VARCHAR,
    core_supplementary VARCHAR,
    mapped_unmapped VARCHAR,
    measure_type VARCHAR,
    stakeholder VARCHAR,
    relevant_map_layer VARCHAR,
    link_to_further_guidance VARCHAR,
    area_id BIGINT,
    grant_id VARCHAR,
    area_name VARCHAR,
    area_description VARCHAR,
    area_link VARCHAR,
    bng_hab_mgt VARCHAR,
    bng_hab_creation VARCHAR,
    theme VARCHAR,
    biodiversity_priority VARCHAR,
    simplified_biodiversity_priority VARCHAR,
    grant_name VARCHAR,
    grant_scheme VARCHAR,
    grant_summary VARCHAR,
    url VARCHAR,
    concise_measure VARCHAR
);

-- ====================================================================
-- STEP 3: CREATE BRIDGE TABLES (WITH FOREIGN KEY CONSTRAINTS)
-- ====================================================================

------------------------------------------------------------------
-- MEASURE_HAS_TYPE
------------------------------------------------------------------
CREATE TABLE lnrs_weca.measure_has_type (
    measure_id      INTEGER NOT NULL,
    measure_type_id INTEGER NOT NULL,
    PRIMARY KEY (measure_id, measure_type_id),
    FOREIGN KEY (measure_id)      REFERENCES measure(measure_id),
    FOREIGN KEY (measure_type_id) REFERENCES measure_type(measure_type_id)
);

------------------------------------------------------------------
-- MEASURE_HAS_STAKEHOLDER
------------------------------------------------------------------
CREATE TABLE lnrs_weca.measure_has_stakeholder (
    measure_id     INTEGER NOT NULL,
    stakeholder_id INTEGER NOT NULL,
    PRIMARY KEY (measure_id, stakeholder_id),
    FOREIGN KEY (measure_id)     REFERENCES measure(measure_id),
    FOREIGN KEY (stakeholder_id) REFERENCES stakeholder(stakeholder_id)
);

------------------------------------------------------------------
-- MEASURE_AREA_PRIORITY
------------------------------------------------------------------
CREATE TABLE lnrs_weca.measure_area_priority (
    measure_id  INTEGER NOT NULL,
    area_id     INTEGER NOT NULL,
    priority_id INTEGER NOT NULL,
    PRIMARY KEY (measure_id, area_id, priority_id),
    FOREIGN KEY (measure_id)  REFERENCES measure(measure_id),
    FOREIGN KEY (area_id)     REFERENCES area(area_id),
    FOREIGN KEY (priority_id) REFERENCES priority(priority_id)
);

------------------------------------------------------------------
-- SPECIES_AREA_PRIORITY
------------------------------------------------------------------
CREATE TABLE lnrs_weca.species_area_priority (
    species_id INTEGER NOT NULL,
    area_id INTEGER NOT NULL,
    priority_id INTEGER NOT NULL,
    PRIMARY KEY (species_id, area_id, priority_id),
    FOREIGN KEY (species_id) REFERENCES species(species_id),
    FOREIGN KEY (area_id) REFERENCES area(area_id),
    FOREIGN KEY (priority_id) REFERENCES priority(priority_id)
);

------------------------------------------------------------------
-- AREA_FUNDING_SCHEMES
------------------------------------------------------------------
CREATE TABLE lnrs_weca.area_funding_schemes (
    id INTEGER NOT NULL PRIMARY KEY,
    area_id INTEGER NOT NULL,
    area_name VARCHAR NOT NULL,
    local_funding_schemes VARCHAR NOT NULL,
    FOREIGN KEY (area_id) REFERENCES area(area_id)
);

------------------------------------------------------------------
-- MEASURE_HAS_BENEFITS
------------------------------------------------------------------
CREATE TABLE lnrs_weca.measure_has_benefits (
    measure_id INTEGER NOT NULL,
    benefit_id INTEGER NOT NULL,
    PRIMARY KEY (measure_id, benefit_id),
    FOREIGN KEY (measure_id) REFERENCES measure(measure_id),
    FOREIGN KEY (benefit_id) REFERENCES benefits(benefit_id)
);

------------------------------------------------------------------
-- MEASURE_HAS_SPECIES
------------------------------------------------------------------
CREATE TABLE lnrs_weca.measure_has_species (
    measure_id INTEGER NOT NULL,
    species_id INTEGER NOT NULL,
    PRIMARY KEY (measure_id, species_id),
    FOREIGN KEY (measure_id) REFERENCES measure(measure_id),
    FOREIGN KEY (species_id) REFERENCES species(species_id)
);

------------------------------------------------------------------
-- HABITAT_CREATION_AREA
------------------------------------------------------------------
CREATE TABLE lnrs_weca.habitat_creation_area (
    area_id INTEGER NOT NULL,
    habitat_id INTEGER NOT NULL,
    PRIMARY KEY (habitat_id, area_id),
    FOREIGN KEY (habitat_id) REFERENCES habitat(habitat_id),
    FOREIGN KEY (area_id) REFERENCES area(area_id)
);

------------------------------------------------------------------
-- HABITAT_MANAGEMENT_AREA
------------------------------------------------------------------
CREATE TABLE lnrs_weca.habitat_management_area (
    area_id INTEGER NOT NULL,
    habitat_id INTEGER NOT NULL,
    PRIMARY KEY (habitat_id, area_id),
    FOREIGN KEY (habitat_id) REFERENCES habitat(habitat_id),
    FOREIGN KEY (area_id) REFERENCES area(area_id)
);

------------------------------------------------------------------
-- AREA_GEOM (no FK constraint in original schema)
------------------------------------------------------------------
CREATE TABLE lnrs_weca.area_geom (
    geo_point_2d GEOMETRY,
    geo_shape GEOMETRY,
    area_id INTEGER
);

-- ====================================================================
-- STEP 4: CREATE DEPENDENT TABLES (DEPEND ON BRIDGE TABLES)
-- ====================================================================

------------------------------------------------------------------
-- MEASURE_AREA_PRIORITY_GRANT
------------------------------------------------------------------
CREATE TABLE lnrs_weca.measure_area_priority_grant (
    measure_id  INTEGER NOT NULL,
    area_id     INTEGER NOT NULL,
    priority_id INTEGER NOT NULL,
    grant_id    VARCHAR,
    FOREIGN KEY (measure_id, area_id, priority_id)
        REFERENCES measure_area_priority (measure_id, area_id, priority_id),
    FOREIGN KEY (grant_id) REFERENCES grant_table(grant_id)
);

-- ====================================================================
-- STEP 5: INSERT DATA IN DEPENDENCY ORDER
-- ====================================================================
ATTACH 'data/lnrs_3nf_o1.duckdb' AS lnrs;
-- Parent tables first (no dependencies)
INSERT INTO lnrs_weca.measure SELECT * FROM lnrs.measure;
INSERT INTO lnrs_weca.measure_type SELECT * FROM lnrs.measure_type;
INSERT INTO lnrs_weca.stakeholder SELECT * FROM lnrs.stakeholder;
INSERT INTO lnrs_weca.area SELECT * FROM lnrs.area;
INSERT INTO lnrs_weca.priority SELECT * FROM lnrs.priority;
INSERT INTO lnrs_weca.species SELECT * FROM lnrs.species;
INSERT INTO lnrs_weca.grant_table SELECT * FROM lnrs.grant_table;
INSERT INTO lnrs_weca.benefits SELECT * FROM lnrs.benefits;
INSERT INTO lnrs_weca.habitat SELECT * FROM lnrs.habitat;
-- source table has 25 cols - 26 were supplied
-- needed?
INSERT INTO lnrs_weca.source_table SELECT * FROM lnrs.source_table;

-- Bridge tables (depend on parent tables)
INSERT INTO lnrs_weca.measure_has_type SELECT * FROM lnrs.measure_has_type;
INSERT INTO lnrs_weca.measure_has_stakeholder SELECT * FROM lnrs.measure_has_stakeholder;
INSERT INTO lnrs_weca.measure_area_priority SELECT * FROM lnrs.measure_area_priority;
INSERT INTO lnrs_weca.species_area_priority SELECT * FROM lnrs.species_area_priority;
INSERT INTO lnrs_weca.area_funding_schemes SELECT * FROM lnrs.area_funding_schemes;
INSERT INTO lnrs_weca.measure_has_benefits SELECT * FROM lnrs.measure_has_benefits;
INSERT INTO lnrs_weca.measure_has_species SELECT * FROM lnrs.measure_has_species;
INSERT INTO lnrs_weca.habitat_creation_area SELECT * FROM lnrs.habitat_creation_area;
INSERT INTO lnrs_weca.habitat_management_area SELECT * FROM lnrs.habitat_management_area;
INSERT INTO lnrs_weca.area_geom SELECT * FROM lnrs.area_geom;

-- Dependent tables (depend on bridge tables)
INSERT INTO lnrs_weca.measure_area_priority_grant SELECT * FROM lnrs.measure_area_priority_grant;

-- ====================================================================
-- STEP 6: CREATE VIEWS
-- ====================================================================

------------------------------------------------------------------
-- SOURCE_TABLE_RECREATED_VW
------------------------------------------------------------------
CREATE VIEW lnrs_weca.source_table_recreated_vw AS
SELECT
    /* Measures */
    m.measure_id,
    m.measure,
    m.concise_measure,
    m.core_supplementary,
    m.mapped_unmapped,
    m.link_to_further_guidance,

    /* Measure Types */
    mt.measure_type,

    /* Stakeholders */
    stkh.stakeholder,

    /* Area */
    map.area_id,
    a.area_name,
    a.area_description,
    a.area_link,
    a.bng_hab_mgt,
    a.bng_hab_creation,

    /* Priority */
    map.priority_id,
    p.biodiversity_priority,
    p.simplified_biodiversity_priority,
    p.theme,

    /* Grant */
    mag.grant_id,
    g.grant_name,
    g.grant_scheme,
    g.grant_summary,
    g.url

FROM lnrs_weca.measure_area_priority AS map
LEFT JOIN lnrs_weca.measure AS m
  ON map.measure_id = m.measure_id
LEFT JOIN lnrs_weca.area AS a
  ON map.area_id = a.area_id
LEFT JOIN lnrs_weca.priority AS p
  ON map.priority_id = p.priority_id

-- Many-to-many from measure -> measure_type
LEFT JOIN lnrs_weca.measure_has_type AS mht
       ON m.measure_id = mht.measure_id
LEFT JOIN lnrs_weca.measure_type AS mt
       ON mht.measure_type_id = mt.measure_type_id

-- Many-to-many from measure -> stakeholder
LEFT JOIN lnrs_weca.measure_has_stakeholder AS mhs
       ON m.measure_id = mhs.measure_id
LEFT JOIN lnrs_weca.stakeholder AS stkh
       ON mhs.stakeholder_id = stkh.stakeholder_id

-- Potential multiple grants per measureareapriority
LEFT JOIN lnrs_weca.measure_area_priority_grant AS mag
       ON  map.measure_id  = mag.measure_id
       AND map.area_id     = mag.area_id
       AND map.priority_id = mag.priority_id
LEFT JOIN lnrs_weca.grant_table AS g
       ON mag.grant_id = g.grant_id;

------------------------------------------------------------------
-- APMG_SLIM_VW
------------------------------------------------------------------
CREATE VIEW lnrs_weca.apmg_slim_vw AS
SELECT
    core_supplementary
    , measure_type
    , stakeholder
    , area_name
    , area_id
    , grant_id
    , priority_id
    , biodiversity_priority
    , measure
    , concise_measure
    , measure_id
    , link_to_further_guidance
    , grant_name
    , "url"
FROM lnrs_weca.source_table_recreated_vw;

-- ====================================================================
-- VERIFICATION QUERIES
-- ====================================================================

-- Verify row counts match
SELECT 'measure' AS table_name, COUNT(*) AS count FROM lnrs_weca.measure
UNION ALL
SELECT 'area', COUNT(*) FROM lnrs_weca.area
UNION ALL
SELECT 'priority', COUNT(*) FROM lnrs_weca.priority
UNION ALL
SELECT 'species', COUNT(*) FROM lnrs_weca.species
UNION ALL
SELECT 'grant_table', COUNT(*) FROM lnrs_weca.grant_table
UNION ALL
SELECT 'measure_area_priority', COUNT(*) FROM lnrs_weca.measure_area_priority
UNION ALL
SELECT 'measure_area_priority_grant', COUNT(*) FROM lnrs_weca.measure_area_priority_grant;

-- Verify views work
SELECT COUNT(*) AS view_count FROM lnrs_weca.apmg_slim_vw;

-- Done!
SELECT 'Database successfully exported to MotherDuck!' AS status;

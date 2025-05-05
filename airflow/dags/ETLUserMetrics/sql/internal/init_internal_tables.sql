DROP TABLE IF EXISTS persons_anonymized;

CREATE TABLE IF NOT EXISTS persons_anonymized (
    faker_id INTEGER,
    email VARCHAR,
    age_group VARCHAR,
    gender VARCHAR,
    city VARCHAR,
    country VARCHAR,
    country_code VARCHAR,
    ingestion_date DATE

);

DROP TABLE IF EXISTS metadata_log;

CREATE TABLE IF NOT EXISTS metadata_log (
    ingestion_time TIMESTAMP,
    records_inserted INTEGER,
    filepath TEXT,
    column_count INTEGER,
    column_list TEXT,
    schema_signature TEXT
);


-- transfprmed file
-- can create another table country with mapping to its each city for creating more dimentions
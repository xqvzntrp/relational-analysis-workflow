CREATE OR REPLACE VIEW prepared_attribute AS
SELECT
    trim(attribute_id) AS attribute_id,
    trim(attribute_name) AS attribute_name
FROM source_attribute;

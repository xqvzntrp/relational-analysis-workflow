CREATE OR REPLACE VIEW prepared_product_attribute AS
SELECT
    trim(product_id) AS product_id,
    trim(attribute_id) AS attribute_id,
    trim(attribute_value) AS attribute_value
FROM source_product_attribute;

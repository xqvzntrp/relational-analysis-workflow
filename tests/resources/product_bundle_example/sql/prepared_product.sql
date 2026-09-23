CREATE OR REPLACE VIEW prepared_product AS
SELECT
    trim(product_id) AS product_id,
    trim(product_name) AS product_name,
    trim(product_type) AS product_type
FROM source_product;

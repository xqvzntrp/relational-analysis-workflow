CREATE OR REPLACE VIEW prepared_product AS
SELECT
    product_id,
    product_name,
    upper(product_name) AS product_name_upper
FROM source_product;

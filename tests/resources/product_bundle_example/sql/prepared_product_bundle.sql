CREATE OR REPLACE VIEW prepared_product_bundle AS
SELECT
    trim(bundle_id) AS bundle_id,
    trim(product_id) AS product_id,
    cast(quantity AS integer) AS quantity,
    cast(sort_order AS integer) AS sort_order
FROM source_product_bundle;

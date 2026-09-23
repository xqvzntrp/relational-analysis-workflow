CREATE OR REPLACE VIEW business_bundle AS
SELECT
    bundle_id,
    bundle_name,
    active_wayfair_listing_id,
    distinct_product_count,
    total_unit_count,
    sofa_count,
    pillow_count,
    coffee_table_count,
    sofa_with_two_pillows
FROM inform_bundle;

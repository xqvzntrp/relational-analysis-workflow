CREATE OR REPLACE VIEW review_bundle AS
SELECT
    b.bundle_id,
    b.bundle_name,
    b.active_wayfair_listing_id,
    count(distinct pb.product_id) AS distinct_product_count,
    sum(pb.quantity) AS total_unit_count,
    sum(case when p.product_type = 'sofa' then pb.quantity else 0 end) AS sofa_count,
    sum(case when p.product_type = 'pillow' then pb.quantity else 0 end) AS pillow_count,
    sum(case when p.product_type = 'coffee_table' then pb.quantity else 0 end) AS coffee_table_count
FROM prepared_bundle b
LEFT JOIN prepared_product_bundle pb ON pb.bundle_id = b.bundle_id
LEFT JOIN prepared_product p ON p.product_id = pb.product_id
GROUP BY 1,2,3;

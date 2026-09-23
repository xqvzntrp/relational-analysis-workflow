CREATE OR REPLACE VIEW prepared_bundle AS
SELECT
    trim(bundle_id) AS bundle_id,
    trim(bundle_name) AS bundle_name,
    trim(active_wayfair_listing_id) AS active_wayfair_listing_id
FROM source_bundle;

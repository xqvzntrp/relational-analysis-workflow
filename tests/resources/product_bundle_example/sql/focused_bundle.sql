CREATE OR REPLACE VIEW focused_bundle AS
SELECT
    *,
    sofa_count >= 1 AS has_sofa,
    pillow_count >= 2 AS has_two_or_more_pillows
FROM review_bundle;

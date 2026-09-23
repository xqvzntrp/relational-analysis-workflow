CREATE OR REPLACE VIEW inform_bundle AS
SELECT
    *,
    has_sofa AND has_two_or_more_pillows AS sofa_with_two_pillows
FROM focused_bundle;

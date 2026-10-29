-- organisations
--
-- required parameters: none (exports every organisation)
--
-- output columns and units:
-- organisation_id: UUID as text
-- organisation_name: text

SELECT
    id::text AS organisation_id,
    name AS organisation_name
FROM organisation
ORDER BY name;

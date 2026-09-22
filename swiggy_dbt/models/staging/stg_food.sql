{{ config(materialized='view') }}

SELECT
    TRIM(f_id) AS food_id,
    TRIM(item) AS item,
    TRIM(veg_or_non_veg) AS veg_or_non_veg
FROM {{ source('swiggy_raw', 'food') }}
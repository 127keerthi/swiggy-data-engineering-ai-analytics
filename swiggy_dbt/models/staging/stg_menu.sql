{{ config(materialized='view') }}

SELECT
    TRIM(menu_id) AS menu_id,
    TRIM(r_id) AS restaurant_id,
    TRIM(f_id) AS food_id,
    TRIM(cuisine) AS cuisine,
    TRY_TO_DECIMAL(price, 10, 2) AS price
FROM {{ source('swiggy_raw', 'menu') }}
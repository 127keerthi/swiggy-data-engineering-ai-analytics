{{ config(materialized='table') }}

SELECT
    food_id,
    item,
    veg_or_non_veg
FROM {{ ref('stg_food') }}
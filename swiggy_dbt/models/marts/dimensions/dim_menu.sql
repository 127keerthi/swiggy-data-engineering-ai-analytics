{{ config(materialized='table') }}

SELECT
    menu_id,
    restaurant_id,
    food_id,
    cuisine,
    price
FROM {{ ref('stg_menu') }}
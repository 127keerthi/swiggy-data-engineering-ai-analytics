{{ config(materialized='table') }}

SELECT
    restaurant_id,
    restaurant_name,
    city,
    rating,
    rating_count,
    cost,
    cuisine,
    license_no,
    restaurant_link,
    address,
    menu
FROM {{ ref('stg_restaurants') }}
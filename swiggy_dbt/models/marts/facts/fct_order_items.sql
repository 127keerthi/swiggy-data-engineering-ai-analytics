{{ config(materialized='table') }}

SELECT
    order_item_id,
    order_id,
    restaurant_id,
    food_id,
    price,
    quantity,
    line_amount
FROM {{ ref('stg_order_items') }}
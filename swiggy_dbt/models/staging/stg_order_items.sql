{{ config(materialized='view') }}

SELECT
    TRIM(order_item_id) AS order_item_id,
    TRIM(order_id) AS order_id,
    TRIM(r_id) AS restaurant_id,
    TRIM(f_id) AS food_id,
    TRY_TO_DECIMAL(price, 10, 2) AS price,
    TRY_TO_NUMBER(quantity) AS quantity,
    TRY_TO_DECIMAL(line_amount, 12, 2) AS line_amount
FROM {{ source('swiggy_raw', 'order_items') }}
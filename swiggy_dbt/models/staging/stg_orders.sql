{{ config(materialized='view') }}

SELECT
    TRIM(order_id) AS order_id,

    TRY_TO_TIMESTAMP_NTZ(order_timestamp) AS order_timestamp,

    TRY_TO_DATE(order_date) AS order_date,

    TRIM(user_id) AS user_id,
    TRIM(r_id) AS restaurant_id,

    TRIM(restaurant_city) AS restaurant_city,
    TRIM(cuisine) AS cuisine,

    TRY_TO_NUMBER(items_count) AS items_count,
    TRY_TO_NUMBER(sales_qty) AS sales_qty,

    TRY_TO_DECIMAL(subtotal, 12, 2) AS subtotal,
    TRY_TO_DECIMAL(discount, 12, 2) AS discount,
    TRY_TO_DECIMAL(delivery_fee, 12, 2) AS delivery_fee,
    TRY_TO_DECIMAL(gst, 12, 2) AS gst,
    TRY_TO_DECIMAL(sales_amount, 12, 2) AS sales_amount,

    TRIM(currency) AS currency,
    TRIM(payment_method) AS payment_method,
    TRIM(order_status) AS order_status,

    TRY_TO_DECIMAL(customer_rating, 3, 2) AS customer_rating,
    TRY_TO_NUMBER(delivery_time_min) AS delivery_time_min,

    TRIM(delivery_agent_id) AS delivery_agent_id,
    TRIM(coupon_code) AS coupon_code

FROM {{ source('swiggy_raw', 'orders') }}
WHERE order_id IS NOT NULL
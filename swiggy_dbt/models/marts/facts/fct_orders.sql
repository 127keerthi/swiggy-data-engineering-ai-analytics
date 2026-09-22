{{ config(materialized='table') }}

SELECT
    order_id,
    order_timestamp,
    order_date,
    user_id,
    restaurant_id,
    restaurant_city,
    cuisine,
    items_count,
    sales_qty,
    subtotal,
    discount,
    delivery_fee,
    gst,
    sales_amount,
    currency,
    payment_method,
    order_status,
    customer_rating,
    delivery_time_min,
    delivery_agent_id,
    coupon_code
FROM {{ ref('stg_orders') }}
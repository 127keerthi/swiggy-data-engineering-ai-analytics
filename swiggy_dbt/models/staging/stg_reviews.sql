{{ config(materialized='view') }}

SELECT
    TRIM(review_id) AS review_id,
    TRIM(order_id) AS order_id,
    TRIM(user_id) AS user_id,
    TRIM(restaurant_id) AS restaurant_id,

    TRY_TO_DECIMAL(rating, 3, 2) AS rating,

    NULLIF(TRIM(comment), '') AS comment,

    TRY_TO_DATE(review_date) AS review_date

FROM {{ source('swiggy_raw', 'reviews') }}
WHERE review_id IS NOT NULL
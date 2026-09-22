{{ config(materialized='table') }}

SELECT
    review_id,
    order_id,
    user_id,
    restaurant_id,
    rating,
    comment,
    review_date
FROM {{ ref('stg_reviews') }}
WHERE review_id IS NOT NULL
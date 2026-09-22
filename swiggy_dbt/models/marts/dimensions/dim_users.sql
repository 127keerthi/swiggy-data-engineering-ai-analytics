{{ config(materialized='table') }}

SELECT
    user_id,
    name,
    email,
    age,
    gender,
    marital_status,
    occupation,
    monthly_income,
    education,
    family_size
FROM {{ ref('stg_users') }}
WHERE user_id IS NOT NULL
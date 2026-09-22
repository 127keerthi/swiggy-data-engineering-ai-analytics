{{ config(materialized='view') }}

SELECT
    TRIM(user_id) AS user_id,
    TRIM(name) AS name,
    LOWER(TRIM(email)) AS email,

    TRY_TO_NUMBER(age) AS age,

    NULLIF(TRIM(gender), '') AS gender,
    NULLIF(TRIM(marital_status), '') AS marital_status,
    NULLIF(TRIM(occupation), '') AS occupation,
    NULLIF(TRIM(monthly_income), '') AS monthly_income,
    NULLIF(TRIM(education), '') AS education,

    TRY_TO_NUMBER(family_size) AS family_size

FROM {{ source('swiggy_raw', 'users') }}
WHERE user_id IS NOT NULL
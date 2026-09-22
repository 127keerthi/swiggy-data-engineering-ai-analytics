{{ config(materialized='view') }}

SELECT
    TRIM(id) AS restaurant_id,
    TRIM(name) AS restaurant_name,
    TRIM(city) AS city,

    CASE
        WHEN TRIM(rating) IN ('', '--') THEN NULL
        ELSE TRY_TO_DECIMAL(TRIM(rating), 3, 2)
    END AS rating,

    CASE
        WHEN TRIM(rating_count) IN ('', 'Too Few Ratings') THEN NULL
        ELSE TRY_TO_NUMBER(
            REGEXP_REPLACE(TRIM(rating_count), '[^0-9]', '')
        )
    END AS rating_count,

    TRY_TO_DECIMAL(
        REGEXP_REPLACE(cost, '[^0-9.]', ''),
        10,
        2
    ) AS cost,

    TRIM(cuisine) AS cuisine,
    TRIM(lic_no) AS license_no,
    TRIM(link) AS restaurant_link,
    TRIM(address) AS address,
    TRIM(menu) AS menu

FROM {{ source('swiggy_raw', 'restaurants') }}
WHERE id IS NOT NULL
{% snapshot snap_restaurants %}

{{
    config(
        target_schema='SNAPSHOTS',
        unique_key='restaurant_id',
        strategy='check',
        check_cols=[
            'restaurant_name',
            'city',
            'rating',
            'rating_count',
            'cost',
            'cuisine',
            'license_no',
            'restaurant_link',
            'address',
            'menu'
        ]
    )
}}

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

{% endsnapshot %}
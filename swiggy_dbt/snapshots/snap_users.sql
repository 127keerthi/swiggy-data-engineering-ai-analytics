{% snapshot snap_users %}

{{
    config(
        target_database='SWIGGY',
        target_schema='SNAPSHOTS',
        unique_key='user_id',
        strategy='check',
        check_cols=[
            'name',
            'email',
            'age',
            'gender',
            'marital_status',
            'occupation',
            'monthly_income',
            'education',
            'family_size'
        ]
    )
}}

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

{% endsnapshot %}
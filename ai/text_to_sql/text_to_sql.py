# ============================================================
# SWIGGY TEXT-TO-SQL AI
# ============================================================
# User Question
#       ↓
# Natural Language Understanding
#       ↓
# SQL Generation
#       ↓
# SQL Safety Validation
#       ↓
# Snowflake Execution
#       ↓
# Result
# ============================================================

import re
import sys
import pandas as pd
import snowflake.connector


# ============================================================
# 1. SNOWFLAKE CONFIGURATION
# ============================================================

ACCOUNT = "TBMPXKR-PE66235"
DATABASE = "SWIGGY"
SCHEMA = "MARTS"
WAREHOUSE = "SWIGGY_WH"
ROLE = "DBT_ROLE"


# ============================================================
# 2. HEADER
# ============================================================

print("=" * 70)
print("SWIGGY TEXT-TO-SQL AI")
print("=" * 70)

print("""
Available data:

1. Users
2. Restaurants
3. Food
4. Menu
5. Orders
6. Order Items
7. Reviews

You can ask questions such as:

- How many orders are there?
- What is the total sales?
- What are the top 10 restaurants?
- Which city has the highest sales?
- What is the average customer rating?
- How many orders are completed?
- What are the most popular cuisines?
- Show total sales by city.
- Show orders by payment method.
""")


# ============================================================
# 3. GET SNOWFLAKE CREDENTIALS
# ============================================================

username = input(
    "Enter your Snowflake username: "
).strip()

password = input(
    "Enter your Snowflake password: "
)


# ============================================================
# 4. CONNECT TO SNOWFLAKE
# ============================================================

print("\nConnecting to Snowflake...")

try:

    conn = snowflake.connector.connect(
        account=ACCOUNT,
        user=username,
        password=password,
        warehouse=WAREHOUSE,
        database=DATABASE,
        schema=SCHEMA,
        role=ROLE
    )

    print("Snowflake connection successful!")

except Exception as e:

    print("\nSnowflake connection failed.")
    print("Error:", e)

    sys.exit(1)


# ============================================================
# 5. DATABASE TABLES
# ============================================================

TABLES = {
    "users": "SWIGGY.MARTS.DIM_USERS",
    "restaurants": "SWIGGY.MARTS.DIM_RESTAURANTS",
    "food": "SWIGGY.MARTS.DIM_FOOD",
    "menu": "SWIGGY.MARTS.DIM_MENU",
    "orders": "SWIGGY.MARTS.FCT_ORDERS",
    "order_items": "SWIGGY.MARTS.FCT_ORDER_ITEMS",
    "reviews": "SWIGGY.MARTS.FCT_REVIEWS"
}


# ============================================================
# 6. SQL SAFETY VALIDATION
# ============================================================

def validate_sql(sql):

    sql_upper = sql.upper().strip()

    # Only SELECT statements are allowed

    if not sql_upper.startswith("SELECT"):

        return False, "Only SELECT queries are allowed."


    # Block dangerous SQL commands

    dangerous_keywords = [
        "DROP ",
        "DELETE ",
        "UPDATE ",
        "INSERT ",
        "ALTER ",
        "TRUNCATE ",
        "CREATE ",
        "MERGE ",
        "GRANT ",
        "REVOKE ",
        "EXECUTE ",
        "CALL "
    ]

    for keyword in dangerous_keywords:

        if keyword in sql_upper:

            return False, (
                f"Blocked SQL keyword detected: {keyword}"
            )


    # Prevent multiple statements

    if ";" in sql_upper[:-1]:

        return False, "Multiple SQL statements are not allowed."


    return True, "SQL validation successful."


# ============================================================
# 7. NATURAL LANGUAGE → SQL
# ============================================================

def generate_sql(question):

    q = question.lower().strip()


    # --------------------------------------------------------
    # TOTAL NUMBER OF ORDERS
    # --------------------------------------------------------

    if (
        "how many orders" in q
        or "number of orders" in q
        or "total orders" in q
    ):

        return """
SELECT
    COUNT(*) AS total_orders
FROM SWIGGY.MARTS.FCT_ORDERS
"""


    # --------------------------------------------------------
    # TOTAL SALES
    # --------------------------------------------------------

    if (
        "total sales" in q
        or "total revenue" in q
        or "overall sales" in q
        or "overall revenue" in q
    ):

        return """
SELECT
    ROUND(SUM(sales_amount), 2) AS total_sales
FROM SWIGGY.MARTS.FCT_ORDERS
"""


    # --------------------------------------------------------
    # AVERAGE ORDER VALUE
    # --------------------------------------------------------

    if (
        "average order value" in q
        or "avg order value" in q
        or "average order amount" in q
    ):

        return """
SELECT
    ROUND(AVG(sales_amount), 2) AS average_order_value
FROM SWIGGY.MARTS.FCT_ORDERS
"""


    # --------------------------------------------------------
    # AVERAGE CUSTOMER RATING
    # --------------------------------------------------------

    if (
        "average rating" in q
        or "avg rating" in q
        or "customer rating" in q
    ):

        return """
SELECT
    ROUND(AVG(customer_rating), 2) AS average_customer_rating
FROM SWIGGY.MARTS.FCT_ORDERS
"""


    # --------------------------------------------------------
    # COMPLETED ORDERS
    # --------------------------------------------------------

    if (
        "completed orders" in q
        or "successful orders" in q
    ):

        return """
SELECT
    COUNT(*) AS completed_orders
FROM SWIGGY.MARTS.FCT_ORDERS
WHERE UPPER(order_status) IN ('COMPLETED', 'DELIVERED')
"""


    # --------------------------------------------------------
    # CANCELLED ORDERS
    # --------------------------------------------------------

    if (
        "cancelled orders" in q
        or "canceled orders" in q
    ):

        return """
SELECT
    COUNT(*) AS cancelled_orders
FROM SWIGGY.MARTS.FCT_ORDERS
WHERE UPPER(order_status) = 'CANCELLED'
"""


    # --------------------------------------------------------
    # SALES BY CITY
    # --------------------------------------------------------

    if (
        "sales by city" in q
        or "revenue by city" in q
        or "city wise sales" in q
        or "sales for each city" in q
    ):

        return """
SELECT
    restaurant_city AS city,
    ROUND(SUM(sales_amount), 2) AS total_sales
FROM SWIGGY.MARTS.FCT_ORDERS
GROUP BY restaurant_city
ORDER BY total_sales DESC
"""


    # --------------------------------------------------------
    # ORDERS BY CITY
    # --------------------------------------------------------

    if (
        "orders by city" in q
        or "city wise orders" in q
        or "number of orders by city" in q
    ):

        return """
SELECT
    restaurant_city AS city,
    COUNT(*) AS total_orders
FROM SWIGGY.MARTS.FCT_ORDERS
GROUP BY restaurant_city
ORDER BY total_orders DESC
"""


    # --------------------------------------------------------
    # SALES BY CUISINE
    # --------------------------------------------------------

    if (
        "sales by cuisine" in q
        or "revenue by cuisine" in q
        or "cuisine wise sales" in q
    ):

        return """
SELECT
    cuisine,
    ROUND(SUM(sales_amount), 2) AS total_sales
FROM SWIGGY.MARTS.FCT_ORDERS
GROUP BY cuisine
ORDER BY total_sales DESC
"""


    # --------------------------------------------------------
    # ORDERS BY CUISINE
    # --------------------------------------------------------

    if (
        "orders by cuisine" in q
        or "cuisine wise orders" in q
    ):

        return """
SELECT
    cuisine,
    COUNT(*) AS total_orders
FROM SWIGGY.MARTS.FCT_ORDERS
GROUP BY cuisine
ORDER BY total_orders DESC
"""


    # --------------------------------------------------------
    # PAYMENT METHOD
    # --------------------------------------------------------

    if (
        "payment method" in q
        or "payment methods" in q
        or "orders by payment" in q
    ):

        return """
SELECT
    payment_method,
    COUNT(*) AS total_orders,
    ROUND(SUM(sales_amount), 2) AS total_sales
FROM SWIGGY.MARTS.FCT_ORDERS
GROUP BY payment_method
ORDER BY total_orders DESC
"""


    # --------------------------------------------------------
    # ORDER STATUS
    # --------------------------------------------------------

    if (
        "order status" in q
        or "orders by status" in q
        or "status wise orders" in q
    ):

        return """
SELECT
    order_status,
    COUNT(*) AS total_orders
FROM SWIGGY.MARTS.FCT_ORDERS
GROUP BY order_status
ORDER BY total_orders DESC
"""


    # --------------------------------------------------------
    # TOP RESTAURANTS
    # --------------------------------------------------------

    if (
        "top restaurants" in q
        or "best restaurants" in q
        or "highest sales restaurants" in q
        or "restaurants with highest sales" in q
    ):

        return """
SELECT
    r.restaurant_id,
    r.restaurant_name,
    r.city,
    r.rating,
    SUM(o.sales_amount) AS total_sales
FROM SWIGGY.MARTS.FCT_ORDERS o
JOIN SWIGGY.MARTS.DIM_RESTAURANTS r
    ON o.restaurant_id = r.restaurant_id
GROUP BY
    r.restaurant_id,
    r.restaurant_name,
    r.city,
    r.rating
ORDER BY total_sales DESC
LIMIT 10
"""


    # --------------------------------------------------------
    # TOP RESTAURANTS BY RATING
    # --------------------------------------------------------

    if (
        "highest rated restaurants" in q
        or "top rated restaurants" in q
        or "best rated restaurants" in q
    ):

        return """
SELECT
    restaurant_id,
    restaurant_name,
    city,
    rating,
    rating_count
FROM SWIGGY.MARTS.DIM_RESTAURANTS
WHERE rating IS NOT NULL
ORDER BY rating DESC, rating_count DESC
LIMIT 10
"""


    # --------------------------------------------------------
    # FOOD ITEMS
    # --------------------------------------------------------

    if (
        "food items" in q
        or "number of food items" in q
        or "how many food" in q
    ):

        return """
SELECT
    COUNT(*) AS total_food_items
FROM SWIGGY.MARTS.DIM_FOOD
"""


    # --------------------------------------------------------
    # VEG / NON-VEG
    # --------------------------------------------------------

    if (
        "veg and non veg" in q
        or "veg or non veg" in q
        or "vegetarian" in q
    ):

        return """
SELECT
    veg_or_non_veg,
    COUNT(*) AS total_items
FROM SWIGGY.MARTS.DIM_FOOD
GROUP BY veg_or_non_veg
ORDER BY total_items DESC
"""


    # --------------------------------------------------------
    # MENU PRICE
    # --------------------------------------------------------

    if (
        "average food price" in q
        or "average menu price" in q
        or "average price" in q
    ):

        return """
SELECT
    ROUND(AVG(price), 2) AS average_price
FROM SWIGGY.MARTS.DIM_MENU
"""


    # --------------------------------------------------------
    # TOTAL USERS
    # --------------------------------------------------------

    if (
        "how many users" in q
        or "total users" in q
        or "number of users" in q
    ):

        return """
SELECT
    COUNT(*) AS total_users
FROM SWIGGY.MARTS.DIM_USERS
"""


    # --------------------------------------------------------
    # USERS BY CITY
    # --------------------------------------------------------

    if (
        "restaurants by city" in q
        or "number of restaurants by city" in q
        or "restaurant count by city" in q
    ):

        return """
SELECT
    city,
    COUNT(*) AS restaurant_count
FROM SWIGGY.MARTS.DIM_RESTAURANTS
GROUP BY city
ORDER BY restaurant_count DESC
"""


    # --------------------------------------------------------
    # RESTAURANT COUNT
    # --------------------------------------------------------

    if (
        "how many restaurants" in q
        or "total restaurants" in q
        or "number of restaurants" in q
    ):

        return """
SELECT
    COUNT(*) AS total_restaurants
FROM SWIGGY.MARTS.DIM_RESTAURANTS
"""


    # --------------------------------------------------------
    # REVIEWS
    # --------------------------------------------------------

    if (
        "how many reviews" in q
        or "total reviews" in q
        or "number of reviews" in q
    ):

        return """
SELECT
    COUNT(*) AS total_reviews
FROM SWIGGY.MARTS.FCT_REVIEWS
"""


    # --------------------------------------------------------
    # REVIEW RATING
    # --------------------------------------------------------

    if (
        "average review rating" in q
        or "review rating" in q
    ):

        return """
SELECT
    ROUND(AVG(rating), 2) AS average_review_rating
FROM SWIGGY.MARTS.FCT_REVIEWS
"""


    # --------------------------------------------------------
    # SALES BY PAYMENT
    # --------------------------------------------------------

    if (
        "sales by payment method" in q
        or "revenue by payment method" in q
    ):

        return """
SELECT
    payment_method,
    ROUND(SUM(sales_amount), 2) AS total_sales
FROM SWIGGY.MARTS.FCT_ORDERS
GROUP BY payment_method
ORDER BY total_sales DESC
"""


    # --------------------------------------------------------
    # DELIVERY TIME
    # --------------------------------------------------------

    if (
        "average delivery time" in q
        or "avg delivery time" in q
        or "delivery time" in q
    ):

        return """
SELECT
    ROUND(AVG(delivery_time_min), 2)
        AS average_delivery_time_minutes
FROM SWIGGY.MARTS.FCT_ORDERS
WHERE delivery_time_min IS NOT NULL
"""


    # --------------------------------------------------------
    # SALES BY DATE
    # --------------------------------------------------------

    if (
        "sales by date" in q
        or "daily sales" in q
        or "sales each day" in q
    ):

        return """
SELECT
    order_date,
    ROUND(SUM(sales_amount), 2) AS total_sales
FROM SWIGGY.MARTS.FCT_ORDERS
GROUP BY order_date
ORDER BY order_date
"""


    # --------------------------------------------------------
    # ORDERS BY DATE
    # --------------------------------------------------------

    if (
        "orders by date" in q
        or "daily orders" in q
        or "orders each day" in q
    ):

        return """
SELECT
    order_date,
    COUNT(*) AS total_orders
FROM SWIGGY.MARTS.FCT_ORDERS
GROUP BY order_date
ORDER BY order_date
"""


    # ========================================================
    # FALLBACK
    # ========================================================

    return None


# ============================================================
# 8. DISPLAY SQL
# ============================================================

def display_sql(sql):

    print("\n" + "-" * 70)

    print("GENERATED SQL")

    print("-" * 70)

    print(sql.strip())

    print("-" * 70)


# ============================================================
# 9. EXECUTE SQL
# ============================================================

def execute_sql(sql):

    try:

        df = pd.read_sql(sql, conn)

        return df

    except Exception as e:

        print("\nSQL execution failed.")

        print("Error:", e)

        return None


# ============================================================
# 10. DISPLAY RESULTS
# ============================================================

def display_results(df):

    if df is None:

        return


    if df.empty:

        print("\nNo results found.")

        return


    print("\n" + "=" * 70)

    print("QUERY RESULT")

    print("=" * 70)

    print(
        df.to_string(index=False)
    )

    print("=" * 70)

    print(
        f"Rows returned: {len(df)}"
    )


# ============================================================
# 11. MAIN CHATBOT
# ============================================================

print("\n" + "=" * 70)

print("TEXT-TO-SQL CHATBOT READY")

print("=" * 70)

print(
    "\nType 'exit' to close the chatbot."
)


while True:

    try:

        question = input(
            "\nYou: "
        ).strip()

    except KeyboardInterrupt:

        print("\n\nStopping chatbot...")

        break


    if question.lower() in [
        "exit",
        "quit",
        "q"
    ]:

        print(
            "\nSWIGGY Text-to-SQL chatbot stopped."
        )

        break


    if not question:

        continue


    print(
        "\nUnderstanding question..."
    )


    # Generate SQL

    sql = generate_sql(
        question
    )


    # No matching intent

    if sql is None:

        print(
            "\nI could not generate SQL for that question."
        )

        print(
            "\nTry one of these:"
        )

        print(
            "- What is the total sales?"
        )

        print(
            "- How many orders are there?"
        )

        print(
            "- What are the top restaurants?"
        )

        print(
            "- Which city has the highest sales?"
        )

        print(
            "- What is the average customer rating?"
        )

        print(
            "- How many completed orders are there?"
        )

        continue


    # Display generated SQL

    display_sql(sql)


    # Validate SQL

    valid, message = validate_sql(
        sql
    )


    if not valid:

        print(
            "\nSQL BLOCKED:"
        )

        print(message)

        continue


    print(
        "SQL safety check: PASSED"
    )


    # Execute SQL

    print(
        "\nExecuting query on Snowflake..."
    )


    result = execute_sql(
        sql
    )


    # Display result

    display_results(
        result
    )


# ============================================================
# 12. CLOSE CONNECTION
# ============================================================

try:

    conn.close()

    print(
        "\nSnowflake connection closed."
    )

except:

    pass


print(
    "\nSWIGGY TEXT-TO-SQL PIPELINE COMPLETED."
)
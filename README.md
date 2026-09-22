\# Swiggy Food Delivery Data Engineering \& AI Analytics



An end-to-end data engineering and analytics project built using \*\*Python, SQL, Snowflake, dbt, Apache Airflow and Streamlit\*\*.



The project takes food-delivery data through ingestion, transformation, data quality validation and analytics. It also includes customer review sentiment analysis, review search using TF-IDF and cosine similarity, and a controlled Text-to-SQL interface.



\## Architecture



!\[Project Architecture](screenshots/architecture.png)



\## Technologies



\- Python

\- SQL

\- Snowflake

\- dbt

\- Apache Airflow

\- Pandas

\- TextBlob

\- TF-IDF

\- Cosine Similarity

\- Streamlit

\- Docker

\- Git \& GitHub



\## Data Engineering



The project uses Snowflake as the central data warehouse.



The warehouse is organized into:



```text

SWIGGY

│

├── RAW

├── STAGING

├── MARTS

│   ├── Dimensions

│   └── Facts

│

└── AI


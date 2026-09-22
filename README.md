\# Swiggy Food Delivery Data Engineering \& AI Analytics



An end-to-end food delivery data engineering and analytics platform built using \*\*Python, SQL, Snowflake, dbt, Apache Airflow and Streamlit\*\*.



The project processes food delivery data through ingestion, transformation, data quality validation, analytical modeling and AI/NLP-based review analysis. It also provides an interactive dashboard for business, operational and customer-review analytics.



\## Project Overview



This project demonstrates how raw food delivery data can be transformed into an analytical platform using modern data engineering tools.



The complete workflow covers:



\*\*Data Ingestion → Snowflake → dbt Transformation → Data Quality → Airflow Orchestration → AI/NLP Processing → Streamlit Analytics\*\*



The project was built as a practical end-to-end data engineering project with additional AI-driven analytics features.



\## What I Built



\- Built a structured \*\*Snowflake data warehouse\*\* using RAW, STAGING, MARTS and AI layers.

\- Developed \*\*dbt staging and mart models\*\* for transforming raw food delivery data.

\- Implemented analytical \*\*dimension and fact models\*\* for users, restaurants, food, menu, orders, order items and reviews.

\- Built an \*\*Apache Airflow pipeline\*\* to orchestrate environment checks, dbt execution, testing, sentiment processing and validation.

\- Implemented \*\*data quality testing\*\*, with 20/20 mart tests passing successfully.

\- Processed \*\*300,000 customer reviews\*\* using TextBlob sentiment analysis.

\- Built a review retrieval system using \*\*TF-IDF and cosine similarity\*\*.

\- Implemented a controlled, \*\*read-only Text-to-SQL interface\*\* for analytical queries.

\- Developed an interactive \*\*Streamlit dashboard\*\* for executive, business, operational and customer-review analytics.

\- Added dashboard views for \*\*sentiment intelligence, review search, Text-to-SQL and pipeline monitoring\*\*.



\## Architecture



!\[Project Architecture](screenshots/architecture.png)



\## Technologies Used



\### Data Engineering



\- Python

\- SQL

\- Snowflake

\- dbt

\- Apache Airflow

\- Docker



\### Data \& Analytics



\- Pandas

\- Streamlit

\- Data Warehousing

\- Dimensional Modeling

\- ETL / ELT

\- Data Quality Testing



\### AI / NLP



\- TextBlob

\- Sentiment Analysis

\- TF-IDF

\- Cosine Similarity

\- RAG

\- Text-to-SQL



\### Development Tools



\- Git

\- GitHub

\- VS Code



\## Dataset Scale



The project processes approximately \*\*5.9 million records\*\* across multiple datasets.



| Dataset | Records |

| --- | ---: |

| Users | 100,000 |

| Restaurants | 148,541 |

| Food | 371,560 |

| Menu | 1,178,743 |

| Orders | 1,641,321 |

| Order Items | 3,774,958 |

| Reviews | 300,000 |



\## Data Warehouse



Snowflake is used as the central data warehouse.



The warehouse is organized into multiple layers:



```text

SWIGGY

│

├── RAW

│

├── STAGING

│

├── MARTS

│   ├── Dimensions

│   └── Facts

│

└── AI


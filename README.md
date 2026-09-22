\# Swiggy Food Delivery Data Engineering and AI Analytics Platform



This project is an end-to-end food delivery data engineering and analytics platform built around a Swiggy dataset. The project covers the complete workflow from raw data ingestion and data warehouse modeling to transformation, orchestration, analytics and AI-based review analysis.



The main technologies used in the project are Python, SQL, Snowflake, dbt, Apache Airflow and Streamlit. I also implemented a local sentiment analysis pipeline, a review retrieval system using TF-IDF and cosine similarity, and a controlled Text-to-SQL interface for querying the analytical data.



\## Project Overview



The objective of this project was to build a complete data engineering workflow rather than only creating a dashboard.



Raw food delivery data is first organized through a local data lake and loaded into Snowflake. dbt is then used to clean and transform the data into staging and analytical models. Apache Airflow manages the execution of the pipeline and the associated data quality checks.



The processed data is used by the Streamlit application for business analysis, operational reporting and customer review intelligence.



The overall flow is:



\*\*Local Data Lake → Snowflake → dbt → Airflow → AI/NLP Processing → Streamlit Analytics\*\*



\## Architecture



!\[Swiggy Data Engineering Architecture](screenshots/architecture.png)



The warehouse follows a layered structure consisting of RAW, STAGING, MARTS and AI schemas.



The RAW layer contains the source data. The STAGING layer contains cleaned and standardized models, while the MARTS layer contains the business-ready fact and dimension tables. The AI layer contains the processed review sentiment data.



\## Data Warehouse



The Snowflake warehouse contains the following main analytical tables:



\- DIM\_USERS

\- DIM\_RESTAURANTS

\- DIM\_FOOD

\- DIM\_MENU

\- FCT\_ORDERS

\- FCT\_ORDER\_ITEMS

\- FCT\_REVIEWS

\- REVIEW\_SENTIMENT



The dataset used in the project contains approximately:



| Dataset | Records |

| --- | ---: |

| Users | 100,000 |

| Restaurants | 148,541 |

| Food | 371,560 |

| Menu | 1,178,743 |

| Orders | 1,641,321 |

| Order Items | 3,774,958 |

| Reviews | 300,000 |



\## Data Engineering Pipeline



\### Data Ingestion



The project uses a local filesystem as the initial data lake. This was chosen so that the complete pipeline could be developed and tested locally without depending on cloud object storage.



The raw data is loaded into the Snowflake RAW layer before transformation.



\### dbt Transformation



dbt is used to transform the raw Snowflake tables into staging and mart models.



The staging layer contains models for users, restaurants, food, menu, orders, order items and reviews.



The mart layer contains the dimensional and fact models used by the analytics application.



The project also includes dbt tests for the analytical models. During testing, all 20 mart-level tests passed successfully.



\### Apache Airflow



Apache Airflow is used to orchestrate the pipeline.



The main workflow is:



```text

check\_environment

&#x20;       |

&#x20;       v

dbt\_debug

&#x20;       |

&#x20;       v

dbt\_run\_staging

&#x20;       |

&#x20;       v

dbt\_test\_staging

&#x20;       |

&#x20;       v

dbt\_run\_marts

&#x20;       |

&#x20;       v

dbt\_test\_marts

&#x20;       |

&#x20;       v

review\_sentiment

&#x20;       |

&#x20;       v

validate\_sentiment

&#x20;       |

&#x20;       v

pipeline\_complete


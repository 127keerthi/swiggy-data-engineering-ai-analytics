\# 🍔 Swiggy Food Delivery Data Engineering \& AI Analytics Platform



An end-to-end food delivery data engineering and AI analytics platform built using \*\*Snowflake, dbt, Apache Airflow, Python, NLP, RAG, Text-to-SQL and Streamlit\*\*.



The project demonstrates how raw food-delivery data can be transformed into a modern analytical platform with automated data pipelines, dimensional data modeling, data quality testing, sentiment intelligence, RAG-based review search, controlled Text-to-SQL and interactive business dashboards.



\---



\## 🚀 Project Overview



This project implements a complete data engineering and analytics workflow:



\*\*Raw Data → Local Data Lake → Snowflake → dbt → Airflow → AI/NLP → Analytics → Streamlit\*\*



The platform processes food-delivery data and creates analytical models for:



\- Customer analytics

\- Restaurant performance

\- Food and menu analytics

\- Order analytics

\- Revenue analysis

\- Review analysis

\- Sentiment intelligence

\- Operational analytics

\- AI-powered review search

\- Natural-language SQL analytics



\---



\## 🏗️ Architecture



!\[Swiggy Data Engineering Architecture](screenshots/architecture.png)



\### Pipeline Flow



```text

Food Delivery Dataset

&#x20;       │

&#x20;       ▼

Local Data Lake

&#x20;       │

&#x20;       ▼

Snowflake RAW Layer

&#x20;       │

&#x20;       ▼

dbt Staging Layer

&#x20;       │

&#x20;       ▼

dbt Mart Layer

&#x20;       │

&#x20;       ▼

Apache Airflow

&#x20;       │

&#x20;       ├── Data Quality Tests

&#x20;       ├── Sentiment Analysis

&#x20;       └── Pipeline Validation

&#x20;       │

&#x20;       ▼

Snowflake AI Layer

&#x20;       │

&#x20;       ├── Sentiment Intelligence

&#x20;       ├── RAG Search

&#x20;       └── Text-to-SQL

&#x20;       │

&#x20;       ▼

Streamlit Analytics Platform


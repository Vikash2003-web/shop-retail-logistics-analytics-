# 📦 UAE Retail & Logistics Analytics

An end-to-end data analytics project simulating a UAE-based retail e-commerce company
(online + in-store) with a regional delivery/logistics layer — the kind of business
question a Business/Data Analyst would face at an MNC operating in the UAE (retail,
e-commerce, or supply chain).

**Business question:** *Where is revenue concentrated, who are our highest-value
customers, and where is our delivery network underperforming?*

---

## 🗺️ Why this project

The UAE economy runs on two things: **retail/consumer spending** and its role as a
**global logistics hub**. This project intentionally combines both — sales analytics
*and* delivery performance analytics — because that combination reflects how MNCs like
Majid Al Futtaim, Noon, Aramex, or DP World actually think about their data.

---

## 🏗️ Architecture

```
Synthetic Data Generation (Python/Faker)
            │
            ▼
   CSV files (data/*.csv)
            │
            ▼
  SQLite Data Warehouse (star schema)
   ┌─────────────────────────────┐
   │ Dimensions: customers,      │
   │ products, suppliers,        │
   │ warehouses                  │
   │ Facts: orders, order_items, │
   │ deliveries                  │
   └─────────────────────────────┘
            │
   ┌────────┴─────────┐
   ▼                   ▼
SQL Analysis      Streamlit Dashboard
(sql/*.sql)       (dashboard/app.py)
   │
   ▼
Jupyter Notebook (notebooks/analysis.ipynb)
```

## 📁 Repository Structure

```
uae-retail-analytics/
├── data/                       # Generated CSVs + SQLite database
├── sql/
│   ├── 01_schema.sql           # Star-schema DDL
│   └── 02_business_queries.sql # 10 analytical queries (RFM, cohorts, delivery KPIs...)
├── python/
│   ├── generate_data.py        # Synthetic UAE retail dataset generator
│   ├── etl.py                  # CSV -> SQLite loader
│   └── build_notebook.py       # Generates the analysis notebook
├── notebooks/
│   └── analysis.ipynb          # Narrative EDA with charts + business recommendations
├── dashboard/
│   └── app.py                  # Interactive Streamlit dashboard
├── requirements.txt
└── README.md
```

## 📊 Dataset

Fully synthetic, generated with realistic UAE-specific parameters:

| Entity | Volume | Notes |
|---|---|---|
| Customers | 3,000 | Distributed across all 7 Emirates (weighted toward Dubai/Abu Dhabi) |
| Products | 400 | 5 categories: Electronics, Fashion, Grocery, Home & Living, Beauty |
| Suppliers | 25 | Mix of UAE-local and international (China, India, Germany, USA...) |
| Orders | 18,000 | Jan 2024 – Dec 2025, across Online App / Website / In-Store |
| Order Items | ~54,000 | Line-item grain |
| Deliveries | ~14,400 | Online orders only, with courier, dispatch/promised/actual dates |

Business logic is baked into the generator — e.g. delivery delay risk increases with
supplier lead time and distance from major hubs, VIP customers order more frequently —
so the analysis surfaces genuine, explainable patterns rather than pure noise.

## 🔍 What's analyzed

**SQL (`sql/02_business_queries.sql`)** — 10 queries covering:
- Monthly revenue & order trend
- Revenue by Emirate / category / channel / payment method
- **RFM customer segmentation** (window functions: `NTILE`)
- **Monthly cohort retention** analysis
- Delivery performance by Emirate & courier
- Supplier lead time → delivery delay correlation
- Top products, customer segment value

**Streamlit Dashboard (`dashboard/app.py`)** — interactive, filterable by date range,
Emirate, channel, and customer segment, with 4 sections: Sales & Revenue, Customer
Insights (RFM + cohort heatmap), Delivery Performance, Product Mix.

**Jupyter Notebook (`notebooks/analysis.ipynb`)** — narrative walkthrough with charts
and written business recommendations, the format most useful for a take-home
assessment or portfolio review.

## ▶️ How to run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate the dataset
python python/generate_data.py

# 3. Load it into SQLite
python python/etl.py

# 4. Explore the SQL queries directly (optional)
sqlite3 data/uae_retail.db < sql/02_business_queries.sql

# 5. Launch the dashboard
streamlit run dashboard/app.py

# 6. Or open the notebook
jupyter notebook notebooks/analysis.ipynb
```

## 🎯 Key findings (see notebook for full detail)

1. Revenue is heavily concentrated in **Dubai and Abu Dhabi** — infrastructure
   investment should prioritize these markets.
2. A small **"Champions/VIP" RFM segment** drives a disproportionate share of
   lifetime revenue — supports a targeted retention program over blanket discounting.
3. **On-time delivery degrades with distance from major hubs** (Fujairah, RAK, UAQ) —
   the clearest lever for improving network-wide delivery SLAs.
4. **Online App** is the leading revenue channel, ahead of Website and In-Store.

## 🛠️ Tech stack

`Python` · `pandas` · `NumPy` · `SQLite` · `SQL (window functions, CTEs)` ·
`Streamlit` · `Plotly` · `Jupyter` · `Faker`

## 📌 Notes for reviewers

This uses a synthetic dataset (clearly disclosed above) so it can be shared publicly
without any confidentiality concerns — but the schema, KPIs, and analytical techniques
(RFM, cohort retention, SLA analysis) mirror what's used on real retail/logistics data.
The star-schema design and query set are meant to demonstrate data modeling judgment,
not just query-writing.

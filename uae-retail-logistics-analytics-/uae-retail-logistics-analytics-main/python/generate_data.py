"""
generate_data.py
-----------------
Generates a realistic synthetic dataset for a UAE-based retail / e-commerce
company with a logistics (delivery) layer, modeling the kind of data an
analyst would encounter at an MNC operating in the UAE market
(e.g. a Majid Al Futtaim, Noon, or Aramex-style business).

Output: CSV files in /data, ready to be loaded into SQLite via etl.py
"""

import numpy as np
import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta
import os

random.seed(42)
np.random.seed(42)
fake = Faker()
Faker.seed(42)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Reference data: UAE-specific geography
# ---------------------------------------------------------------------------
EMIRATES = {
    "Dubai": ["Deira", "Marina", "Downtown", "Jumeirah", "Business Bay"],
    "Abu Dhabi": ["Al Reem Island", "Khalifa City", "Mussafah", "Corniche"],
    "Sharjah": ["Al Majaz", "Al Nahda", "Muwaileh"],
    "Ajman": ["Al Nuaimiya", "Al Rashidiya"],
    "Ras Al Khaimah": ["Al Nakheel", "Al Hamra"],
    "Fujairah": ["Al Faseel", "Sakamkam"],
    "Umm Al Quwain": ["Al Salamah"],
}
EMIRATE_WEIGHTS = [0.42, 0.28, 0.12, 0.06, 0.05, 0.04, 0.03]  # Dubai/AD dominate

CATEGORIES = {
    "Electronics": ["Mobile Phones", "Laptops", "Home Appliances", "Accessories"],
    "Fashion": ["Men's Wear", "Women's Wear", "Footwear", "Watches"],
    "Grocery": ["Fresh Produce", "Packaged Food", "Beverages", "Household"],
    "Home & Living": ["Furniture", "Decor", "Kitchenware"],
    "Beauty & Personal Care": ["Skincare", "Makeup", "Fragrances"],
}

COURIERS = ["Aramex", "Emirates Post", "SMSA", "In-house Fleet", "Fetchr"]
CHANNELS = ["Online App", "Website", "In-Store"]
PAYMENT_METHODS = ["Credit Card", "Cash on Delivery", "Apple Pay", "Tabby (BNPL)"]
CUSTOMER_SEGMENTS = ["Regular", "Premium", "VIP"]

N_CUSTOMERS = 3000
N_SUPPLIERS = 25
N_PRODUCTS = 400
N_WAREHOUSES = 7  # one per emirate
N_ORDERS = 18000
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 12, 31)


def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days),
                              seconds=random.randint(0, 86400))


# ---------------------------------------------------------------------------
# 1. Customers
# ---------------------------------------------------------------------------
customers = []
for cid in range(1, N_CUSTOMERS + 1):
    emirate = random.choices(list(EMIRATES.keys()), weights=EMIRATE_WEIGHTS)[0]
    city = random.choice(EMIRATES[emirate])
    signup_date = random_date(START_DATE, END_DATE - timedelta(days=1))
    segment = random.choices(CUSTOMER_SEGMENTS, weights=[0.65, 0.25, 0.10])[0]
    customers.append({
        "customer_id": cid,
        "customer_name": fake.name(),
        "email": fake.unique.email(),
        "emirate": emirate,
        "city": city,
        "signup_date": signup_date.date(),
        "customer_segment": segment,
        "age": random.randint(18, 65),
        "gender": random.choice(["Male", "Female"]),
    })
customers_df = pd.DataFrame(customers)

# ---------------------------------------------------------------------------
# 2. Suppliers
# ---------------------------------------------------------------------------
supplier_countries = ["UAE", "China", "India", "Germany", "USA", "Turkey", "Saudi Arabia"]
suppliers = []
for sid in range(1, N_SUPPLIERS + 1):
    country = random.choice(supplier_countries)
    lead_time = random.randint(1, 3) if country == "UAE" else random.randint(5, 25)
    suppliers.append({
        "supplier_id": sid,
        "supplier_name": fake.company(),
        "country": country,
        "avg_lead_time_days": lead_time,
    })
suppliers_df = pd.DataFrame(suppliers)

# ---------------------------------------------------------------------------
# 3. Products
# ---------------------------------------------------------------------------
products = []
pid = 1
for category, subcats in CATEGORIES.items():
    for _ in range(N_PRODUCTS // len(CATEGORIES)):
        subcat = random.choice(subcats)
        base_price = {
            "Electronics": (200, 5000),
            "Fashion": (50, 800),
            "Grocery": (5, 150),
            "Home & Living": (80, 3000),
            "Beauty & Personal Care": (30, 500),
        }[category]
        price = round(random.uniform(*base_price), 2)
        products.append({
            "product_id": pid,
            "product_name": f"{subcat} - {fake.word().capitalize()} {fake.word().capitalize()}",
            "category": category,
            "subcategory": subcat,
            "unit_price_aed": price,
            "supplier_id": random.randint(1, N_SUPPLIERS),
        })
        pid += 1
products_df = pd.DataFrame(products)

# ---------------------------------------------------------------------------
# 4. Warehouses (one per emirate)
# ---------------------------------------------------------------------------
warehouses_df = pd.DataFrame([
    {"warehouse_id": i + 1, "emirate": emirate, "city": EMIRATES[emirate][0]}
    for i, emirate in enumerate(EMIRATES.keys())
])

# ---------------------------------------------------------------------------
# 5. Orders + Order Items + Deliveries
# ---------------------------------------------------------------------------
orders = []
order_items = []
deliveries = []
order_item_id = 1

# give repeat-purchase behavior: VIP/Premium customers order more often
cust_weights = customers_df.set_index("customer_id")["customer_segment"].map(
    {"Regular": 1, "Premium": 2.5, "VIP": 5}
).to_dict()
cust_ids = list(cust_weights.keys())
cust_probs = np.array(list(cust_weights.values()))
cust_probs = cust_probs / cust_probs.sum()

for oid in range(1, N_ORDERS + 1):
    cust_id = np.random.choice(cust_ids, p=cust_probs)
    cust_row = customers_df.loc[customers_df.customer_id == cust_id].iloc[0]
    signup = pd.to_datetime(cust_row.signup_date)
    order_date = random_date(max(START_DATE, signup.to_pydatetime()), END_DATE)
    channel = random.choices(CHANNELS, weights=[0.5, 0.3, 0.2])[0]
    payment = random.choice(PAYMENT_METHODS)
    emirate = cust_row.emirate
    warehouse_id = int(warehouses_df.loc[warehouses_df.emirate == emirate, "warehouse_id"].iloc[0])

    orders.append({
        "order_id": oid,
        "customer_id": cust_id,
        "order_date": order_date.date(),
        "channel": channel,
        "payment_method": payment,
        "warehouse_id": warehouse_id,
    })

    # 1-5 line items per order
    n_items = random.randint(1, 5)
    chosen_products = random.sample(range(1, N_PRODUCTS + 1), n_items)
    order_total = 0
    for prod_id in chosen_products:
        prod_row = products_df.loc[products_df.product_id == prod_id].iloc[0]
        qty = random.randint(1, 4)
        discount_pct = random.choices([0, 5, 10, 15, 20], weights=[0.5, 0.2, 0.15, 0.1, 0.05])[0]
        line_price = round(prod_row.unit_price_aed * qty * (1 - discount_pct / 100), 2)
        order_total += line_price
        order_items.append({
            "order_item_id": order_item_id,
            "order_id": oid,
            "product_id": prod_id,
            "quantity": qty,
            "unit_price_aed": prod_row.unit_price_aed,
            "discount_pct": discount_pct,
            "line_total_aed": line_price,
        })
        order_item_id += 1

    # Delivery record (only for Online App / Website orders, not in-store)
    if channel != "In-Store":
        supplier_lead = suppliers_df.loc[
            suppliers_df.supplier_id.isin(
                products_df.loc[products_df.product_id.isin(chosen_products), "supplier_id"]
            ), "avg_lead_time_days"
        ].mean()
        supplier_lead = 3 if pd.isna(supplier_lead) else supplier_lead

        promised_days = random.choice([1, 2, 3])
        dispatch_date = order_date + timedelta(hours=random.randint(2, 30))

        # delay probability increases with supplier lead time & far emirates
        delay_risk = 0.15 + (0.01 * supplier_lead) + (0.05 if emirate in ["Fujairah", "Ras Al Khaimah", "Umm Al Quwain"] else 0)
        is_delayed = random.random() < min(delay_risk, 0.55)
        actual_days = promised_days + (random.randint(1, 4) if is_delayed else random.choice([-1, 0, 0, 0]))
        actual_days = max(actual_days, 0)
        delivery_date = dispatch_date + timedelta(days=actual_days)

        status = "Delivered"
        if random.random() < 0.02:
            status = "Returned"
        elif random.random() < 0.01:
            status = "Cancelled"

        deliveries.append({
            "delivery_id": oid,
            "order_id": oid,
            "warehouse_id": warehouse_id,
            "courier": random.choice(COURIERS),
            "dispatch_date": dispatch_date,
            "promised_date": (order_date + timedelta(days=promised_days)),
            "delivery_date": delivery_date if status == "Delivered" else None,
            "delivery_status": status,
            "on_time": bool(delivery_date <= order_date + timedelta(days=promised_days)) if status == "Delivered" else False,
        })

orders_df = pd.DataFrame(orders)
order_items_df = pd.DataFrame(order_items)
deliveries_df = pd.DataFrame(deliveries)

# ---------------------------------------------------------------------------
# Save all to CSV
# ---------------------------------------------------------------------------
customers_df.to_csv(f"{OUT_DIR}/customers.csv", index=False)
suppliers_df.to_csv(f"{OUT_DIR}/suppliers.csv", index=False)
products_df.to_csv(f"{OUT_DIR}/products.csv", index=False)
warehouses_df.to_csv(f"{OUT_DIR}/warehouses.csv", index=False)
orders_df.to_csv(f"{OUT_DIR}/orders.csv", index=False)
order_items_df.to_csv(f"{OUT_DIR}/order_items.csv", index=False)
deliveries_df.to_csv(f"{OUT_DIR}/deliveries.csv", index=False)

print("Data generation complete:")
print(f"  customers:    {len(customers_df):,}")
print(f"  suppliers:    {len(suppliers_df):,}")
print(f"  products:     {len(products_df):,}")
print(f"  warehouses:   {len(warehouses_df):,}")
print(f"  orders:       {len(orders_df):,}")
print(f"  order_items:  {len(order_items_df):,}")
print(f"  deliveries:   {len(deliveries_df):,}")

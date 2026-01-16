import pandas as pd
from pathlib import Path

# -------------------------------------------------
# PATH CONFIGURATION (ROBUST – WORKS FROM ANYWHERE)
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "department"
OUTPUT_DIR = BASE_DIR / "data" / "clean"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------
# SCHEMA DEFINITIONS (MATCHES YOUR FILES)
# -------------------------------------------------
SCHEMAS = {

    # -----------------------------
    # SALES
    # Grain: order_id + product_id
    # -----------------------------
    "sales_orders.csv": {
        "required_columns": {
            "Order Id": "order_id",
            "order date (DateOrders)": "order_date",
            "Product Card Id": "product_id",
            "Order Item Quantity": "order_qty",
            "Sales per customer": "sales_amount",
            "Order Item Discount": "discount_amount",
            "Order Profit Per Order": "profit_amount"
        },
        "date_columns": ["order_date"],
        "grain": ["order_id", "product_id"]
    },

    # -----------------------------
    # DEMAND (RAW DEMAND INPUT)
    # Grain: product_id + order_date
    # -----------------------------
    "demand_forecast.csv": {
        "required_columns": {
            "order date (DateOrders)": "order_date",
            "Product Card Id": "product_id",
            "Sales per customer": "demand_qty"
        },
        "date_columns": ["order_date"],
        "grain": ["product_id", "order_date"]
    },

    # -----------------------------
    # INVENTORY (MODELED SNAPSHOT)
    # Grain: product_id
    # -----------------------------
    "inventory_snapshot.csv": {
        "required_columns": {
            "Product Card Id": "product_id",
            "Category Name": "product_category",
            "Order Item Quantity": "on_hand_qty",
            "Order Item Product Price": "unit_cost"
        },
        "date_columns": [],
        "grain": ["product_id"]
    },

    # -----------------------------
    # FULFILLMENT
    # Grain: order_id
    # -----------------------------
    "fulfillment_orders.csv": {
        "required_columns": {
            "Order Id": "order_id",
            "Delivery Status": "delivery_status",
            "Days for shipping (real)": "actual_ship_days",
            "Days for shipment (scheduled)": "scheduled_ship_days",
            "Shipping Mode": "shipping_mode"
        },
        "date_columns": [],
        "grain": ["order_id"]
    }
}

# -------------------------------------------------
# VALIDATION + STANDARDIZATION FUNCTION
# -------------------------------------------------
def validate_and_standardize(file_name, config):
    print(f"\nProcessing: {file_name}")

    file_path = INPUT_DIR / file_name
    df = pd.read_csv(file_path)

    # -----------------------------
    # SCHEMA VALIDATION
    # -----------------------------
    expected_cols = set(config["required_columns"].keys())
    actual_cols = set(df.columns)

    missing = expected_cols - actual_cols
    if missing:
        raise ValueError(f"{file_name} → Missing columns: {missing}")

    extra = actual_cols - expected_cols
    if extra:
        raise ValueError(f"{file_name} → Unexpected columns: {extra}")

    # -----------------------------
    # RENAME COLUMNS
    # -----------------------------
    df = df.rename(columns=config["required_columns"])

    # -----------------------------
    # DATE CONVERSION
    # -----------------------------
    for col in config["date_columns"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # -----------------------------
    # DUPLICATE CHECK (GRAIN-AWARE)
    # -----------------------------
    grain_cols = config.get("grain", [])
    if grain_cols:
        dup_count = df.duplicated(subset=grain_cols).sum()
        if dup_count > 0:
            print(
                f"⚠ Warning: {dup_count} duplicate records found "
                f"based on grain {grain_cols}"
            )

    # -----------------------------
    # MISSING VALUE CHECK (NON-DESTRUCTIVE)
    # -----------------------------
    missing_summary = df.isnull().sum()
    missing_cols = missing_summary[missing_summary > 0]

    if not missing_cols.empty:
        print("⚠ Missing values detected:")
        print(missing_cols)

    # -----------------------------
    # SAVE CLEAN OUTPUT
    # -----------------------------
    output_file = OUTPUT_DIR / file_name.replace(".csv", "_clean.csv")
    df.to_csv(output_file, index=False)

    print(f"✓ Saved clean file → {output_file.name}")
    print(f"✓ Rows: {len(df)}")

# -------------------------------------------------
# MAIN EXECUTION
# -------------------------------------------------
if __name__ == "__main__":
    for file_name, config in SCHEMAS.items():
        validate_and_standardize(file_name, config)

    print("\nAll department files validated and standardized successfully.")

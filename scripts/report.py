from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT/"data"/"processed"

EVENT_COL = "event_type"
DATE_COL = "event_time"
MONEY_COL = "price"
CLIENT_COL = "user_id"
SESSION_KEY = "session_key"
ORDER_KEY = "order_key"
PRODUCT_COL = "product_id"
BRAND_COL = "brand"
CAT_COL = "category_code"
CAT_L1 = "category_l1"

def load_tables():
    clean = pd.read_parquet(OUT_DIR/"clean.parquet")
    people = pd.read_parquet(OUT_DIR/"people.parquet")
    return clean, people

def purchases(clean: pd.DataFrame)-> pd.DataFrame:
    return clean[clean[EVENT_COL] == "purchase"].copy()

# Маршрут A - события, сессии, GMV из purchase, время
def kpi_totals(clean: pd.DataFrame)-> None:
    pur = purchases(clean)
    gmv = pur[MONEY_COL].sum()
    orders = pur[ORDER_KEY].nunique()
    aov = gmv / orders if orders else 0
    events = len(clean)
    sessions = clean[SESSION_KEY].nunique()
    users = clean[CLIENT_COL].nunique()
    print("events", events)
    print("sessions", sessions)
    print("users", users)
    print("gmv", gmv, "orders", orders, "aov", aov)
    print("purchase rows", len(pur))
    print("purchase rows / order", round(len(pur) / orders, 2) if orders else 0)
    print("price min/median/max (purchase)", pur[MONEY_COL].min(), pur[MONEY_COL].median(), pur[MONEY_COL].max())
    print("period", clean[DATE_COL].min(), "->", clean[DATE_COL].max())
    print("event_type", clean[EVENT_COL].value_counts().to_dict())

def kpi_funnel(clean: pd.DataFrame)-> None:
    print("--- funnel sessions ---")
    sess = clean.groupby(SESSION_KEY)[EVENT_COL].agg(lambda s: set(s))
    sv = sum("view" in s for s in sess)
    sc = sum("cart" in s for s in sess)
    sp = sum("purchase" in s for s in sess)
    print("sessions view/cart/purchase", sv, sc, sp)
    print("view->cart%", round(sc / sv * 100, 2) if sv else 0)
    print("cart->purchase%", round(sp / sc * 100, 2) if sc else 0)
    print("view->purchase%", round(sp / sv * 100, 2) if sv else 0)
    print("drop view-cart", sv - sc, "drop cart-pur", sc - sp)
    sp_set = [s for s in sess if "purchase" in s]
    no_view = sum(1 for s in sp_set if "view" not in s)
    no_cart = sum(1 for s in sp_set if "cart" not in s)
    print("purchase sess without view", no_view, "without cart", no_cart)
    print("--- funnel users ---")
    usr = clean.groupby(CLIENT_COL)[EVENT_COL].agg(lambda s: set(s))
    uv = sum("view" in s for s in usr)
    uc = sum("cart" in s for s in usr)
    up = sum("purchase" in s for s in usr)
    print("users view/cart/purchase", uv, uc, up)
    print("view->cart%", round(uc / uv * 100, 2) if uv else 0)
    print("cart->purchase%", round(up / uc * 100, 2) if uc else 0)
    print("view->purchase%", round(up / uv * 100, 2) if uv else 0)
    print("drop view-cart", uv - uc, "drop cart-pur", uc - up)

def kpi_year_month(clean: pd.DataFrame)-> pd.DataFrame:
    pur = purchases(clean)
    y_m = pur.copy()
    y_m["year"] = y_m[DATE_COL].dt.year
    y_m["month"] = y_m[DATE_COL].dt.month
    out = y_m.groupby(["year", "month"], as_index=False).agg(
        gmv=(MONEY_COL, "sum"),
        orders=(ORDER_KEY, "nunique"),
        purchase_rows=(ORDER_KEY, "size"))
    out["aov"] = out["gmv"] / out["orders"]
    out = out.sort_values(["year", "month"]).head(5)
    print("year*manth")
    print(out)
    return out

def kpi_hour(clean: pd.DataFrame)-> pd.DataFrame:
    pur = purchases(clean)
    out = pur.groupby("event_hour", as_index=False).agg(
        gmv=(MONEY_COL, "sum"),
        orders=(ORDER_KEY, "nunique"))
    out["aov"] = out["gmv"] / out["orders"]
    out = out.sort_values("event_hour")
    #print(out)
    top = out.sort_values("gmv", ascending=False).head(3)
    print("peak hours")
    print(top)
    return out



def main()-> None:
    clean, people = load_tables()
    kpi_totals(clean)
    kpi_funnel(clean)
    kpi_year_month(clean)
    kpi_hour(clean)


if __name__ == "__main__":
    main()

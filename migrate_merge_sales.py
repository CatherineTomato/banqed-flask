"""One-off migration: fold the old sale_listing table into item.
 
The original schema kept wardrobe items and sale listings in two unrelated
tables, so changing an item's resale willingness could never move it between
the two pages. This merges each sale listing back onto its wardrobe item
(matched by name, which is how the source spreadsheet related them) and then
drops the old table.
 
Safe to run more than once: it skips work that's already been done.
 
    python3 migrate_merge_sales.py
"""
 
from datetime import date, datetime
 
from sqlalchemy import inspect, text
 
from app import app
from models import db, Item, SALES_RESALE
 
DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",   # what the old database stored, e.g. 2026-07-09 00:00:00
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d-%b-%Y",
    "%d %b %Y",
    "%m/%d/%Y",
]
 
 
def parse_date(value):
    """Best-effort parse of the loosely formatted dates in the old table."""
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
 
    text_value = str(value).strip()
    if not text_value:
        return None
 
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text_value, fmt).date()
        except ValueError:
            continue
    print(f"  ! could not parse date {text_value!r}, leaving blank")
    return None
 
 
def parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
 
 
def add_missing_columns(inspector):
    """Add the new sale columns to an existing item table, if absent."""
    existing = {col["name"] for col in inspector.get_columns("item")}
    additions = {
        "sale_status": "VARCHAR(50)",
        "date_listed": "DATE",
        "date_sold": "DATE",
        "listing_price": "FLOAT",
        "sold_for": "FLOAT",
    }
    added = []
    for name, sql_type in additions.items():
        if name not in existing:
            db.session.execute(text(f"ALTER TABLE item ADD COLUMN {name} {sql_type}"))
            added.append(name)
    if added:
        db.session.commit()
        print(f"Added columns to item: {', '.join(added)}")
    else:
        print("Sale columns already present on item.")
 
 
def merge_listings(inspector):
    if "sale_listing" not in inspector.get_table_names():
        print("No sale_listing table found — nothing to merge.")
        return
 
    rows = db.session.execute(text("""
        SELECT item_name, status, date_listed, date_sold,
               listing_price, sold_for
        FROM sale_listing
    """)).fetchall()
 
    merged = 0
    unmatched = []
 
    for row in rows:
        name = (row.item_name or "").strip()
        if not name:
            continue
 
        item = Item.query.filter(
            db.func.lower(Item.item_name) == name.lower()
        ).first()
 
        if item is None:
            unmatched.append(name)
            continue
 
        item.sale_status = (row.status or "").strip() or None
        item.date_listed = parse_date(row.date_listed)
        item.date_sold = parse_date(row.date_sold)
        item.listing_price = parse_float(row.listing_price)
        item.sold_for = parse_float(row.sold_for)
 
        # A listing existing at all means the item was on the Sales page.
        if item.resale_willingness not in SALES_RESALE:
            item.resale_willingness = "Sell now"
 
        merged += 1
 
    db.session.commit()
    print(f"Merged {merged} sale listings onto their wardrobe items.")
    if unmatched:
        print(f"  ! {len(unmatched)} listings had no matching item:")
        for name in unmatched[:10]:
            print(f"    - {name}")
        if len(unmatched) > 10:
            print(f"    ... and {len(unmatched) - 10} more")
 
 
def backfill_listing_prices():
    """Listing price starts as the estimated value entered when lodging."""
    items = Item.query.filter(
        Item.resale_willingness.in_(SALES_RESALE),
        Item.listing_price.is_(None),
        Item.estimated_value.isnot(None),
    ).all()
    for item in items:
        item.listing_price = item.estimated_value
    db.session.commit()
    print(f"Backfilled listing price on {len(items)} items from estimated value.")
 
 
def default_sale_statuses():
    """Anything on the Sales page needs a starting status."""
    items = Item.query.filter(
        Item.resale_willingness.in_(SALES_RESALE),
        (Item.sale_status.is_(None)) | (Item.sale_status == ""),
    ).all()
    for item in items:
        item.sale_status = "To prep"
    db.session.commit()
    print(f"Set default status 'To prep' on {len(items)} items.")
 
 
def drop_old_table(inspector):
    if "sale_listing" in inspector.get_table_names():
        db.session.execute(text("DROP TABLE sale_listing"))
        db.session.commit()
        print("Dropped the sale_listing table.")
 
 
def main():
    with app.app_context():
        inspector = inspect(db.engine)
 
        if "item" not in inspector.get_table_names():
            print("No item table yet — creating a fresh schema.")
            db.create_all()
            return
 
        add_missing_columns(inspector)
        merge_listings(inspect(db.engine))
        backfill_listing_prices()
        default_sale_statuses()
        drop_old_table(inspect(db.engine))
 
        on_sales = Item.query.filter(Item.resale_willingness.in_(SALES_RESALE)).count()
        total = Item.query.count()
        print(f"\nDone. {total} items total, {on_sales} on the Sales page, "
              f"{total - on_sales} in the Wardrobe.")
 
 
if __name__ == "__main__":
    main()
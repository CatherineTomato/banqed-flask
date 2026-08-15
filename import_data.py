import openpyxl
from app import app
from models import db, Item, SaleListing


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def clean_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def import_wardrobe():
    wb = openpyxl.load_workbook("data/BANQED.xlsx", data_only=True)
    ws = wb["Wardrobe"]
    headers = [str(cell.value).strip() if cell.value else "" for cell in ws[1]]

    added = 0
    skipped = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        row_dict = dict(zip(headers, row))
        item_name = clean(row_dict.get("Item Name"))
        if not item_name:
            continue
        existing = Item.query.filter_by(item_name=item_name).first()
        if existing:
            skipped += 1
            continue

        item = Item(
            item_name=item_name,
            category=clean(row_dict.get("Category")),
            item_type=clean(row_dict.get("Item Type")),
            colour=clean(row_dict.get("Colour")),
            detailing=clean(row_dict.get("Detailing")),
            style=clean(row_dict.get("Style")),
            context=clean(row_dict.get("Context")),
            brand=clean(row_dict.get("Brand")),
            source_type=clean(row_dict.get("Source Type")),
            purchase_method=clean(row_dict.get("Purchase Method")),
            source=clean(row_dict.get("Source")),
            country=clean(row_dict.get("Country")),
            location=clean(row_dict.get("Location")),
            wear_frequency=clean(row_dict.get("Wear Frequency")),
            estimated_value=clean_number(row_dict.get("Est. Value")),
            resale_willingness=clean(row_dict.get("Resale Willingness")),
            item_rating=clean(row_dict.get("Item Rating")),
            size=clean(row_dict.get("Size")),
            notes=clean(row_dict.get("Notes")),
            ownership_status=clean(row_dict.get("Ownership Status")) or "Owned",
        )
        db.session.add(item)
        added += 1

    print(f"Imported {count} wardrobe items.")


def import_sales():
    wb = openpyxl.load_workbook("data/BANQED.xlsx", data_only=True)
    ws = wb["Sales"]
    headers = [str(cell.value).strip() if cell.value else "" for cell in ws[1]]

    count = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        row_dict = dict(zip(headers, row))
        item_name = clean(row_dict.get("Item name"))
        if not item_name:
            continue

        listing = SaleListing(
            item_name=item_name,
            status=clean(row_dict.get("Status")),
            category=clean(row_dict.get("Category")),
            item_type=clean(row_dict.get("Item Type")),
            date_listed=clean(row_dict.get("Date Listed")),
            date_sold=clean(row_dict.get("Date Sold")),
            days_to_sell=clean(row_dict.get("Days to sell")),
            listing_price=clean_number(row_dict.get("Listing Price")),
            sold_for=clean_number(row_dict.get("Sold for")),
        )
        db.session.add(listing)
        count += 1

    print(f"Imported {count} sales rows.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        import_wardrobe()
        import_sales()
        db.session.commit()
        print("Done.")
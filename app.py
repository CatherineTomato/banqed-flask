from datetime import date, datetime
 
from flask import Flask, jsonify, redirect, render_template, request, url_for
from sqlalchemy import func
 
from models import (
    db, Item,
    SALES_RESALE, SOLD_STATUSES, SALE_STATUSES,
)
from options import (
    SEED_OPTIONS, SEED_CATEGORY_TYPES, SEED_COUNTRY_CITIES,
    CLOSED_FIELDS, merge_options,
)
 
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///banqed.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
 
db.init_app(app)
 
SINGLE_VALUE_FIELDS = {
    "category": Item.category,
    "source_type": Item.source_type,
    "purchase_method": Item.purchase_method,
    "brand": Item.brand,
    "source": Item.source,
    "country": Item.country,
    "location": Item.location,
    "wear_frequency": Item.wear_frequency,
    "resale_willingness": Item.resale_willingness,
    "item_rating": Item.item_rating,
}
 
MULTI_VALUE_FIELDS = {
    "colour": Item.colour,
    "detailing": Item.detailing,
    "style": Item.style,
    "context": Item.context,
}
 
# Fields a row's edit mode may write to, and how to coerce the incoming value.
EDITABLE_TEXT = {
    "item_name", "category", "item_type", "colour", "detailing", "style",
    "context", "brand", "source_type", "purchase_method", "source",
    "country", "location", "wear_frequency", "resale_willingness",
    "item_rating", "notes", "sale_status",
}
EDITABLE_NUMBER = {"estimated_value", "listing_price", "sold_for"}
EDITABLE_DATE = {"date_listed", "date_sold"}
 
 
def parse_float(value):
    """Convert a form value to a float, or None if it's blank/invalid."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
 
 
def parse_date(value):
    """Parse an ISO date from a date input, or None if blank/invalid."""
    if not value:
        return None
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None
 
 
def get_distinct_single(column):
    rows = db.session.query(column).distinct().all()
    return {r[0].strip() for r in rows if r[0] and r[0].strip()}
 
 
def get_multi_values(column):
    rows = db.session.query(column).all()
    values = set()
    for (val,) in rows:
        if not val:
            continue
        for part in val.split(","):
            part = part.strip()
            if part:
                values.add(part)
    return values
 
 
def build_field_options():
    """Seeded sheet options first, then anything extra already in the database."""
    options = {}
    for field, seed in SEED_OPTIONS.items():
        if field in CLOSED_FIELDS:
            options[field] = list(seed)
        elif field in MULTI_VALUE_FIELDS:
            options[field] = merge_options(seed, get_multi_values(MULTI_VALUE_FIELDS[field]))
        elif field in SINGLE_VALUE_FIELDS:
            options[field] = merge_options(seed, get_distinct_single(SINGLE_VALUE_FIELDS[field]))
        else:
            options[field] = list(seed)
    return options
 
 
def build_nested(seed, parent_column, child_column):
    """Seeded parent/child pairings, plus any pairing already in the database."""
    nested = {parent: list(children) for parent, children in seed.items()}
 
    rows = db.session.query(parent_column, child_column).distinct().all()
    for parent, child in rows:
        if not parent or not parent.strip():
            continue
        parent = parent.strip()
        nested.setdefault(parent, [])
        if child and child.strip():
            child = child.strip()
            known = {value.lower() for value in nested[parent]}
            if child.lower() not in known:
                nested[parent].append(child)
 
    return nested
 
 
def item_type_options():
    """Every item type in use, for the filter menus."""
    return sorted(get_distinct_single(Item.item_type))
 
 
@app.route("/")
def home():
    """The front page: an editorial read on what's actually in the banq.
 
    The figures printed here are the real ones, computed at request time, so
    the front page always describes the wardrobe as it currently stands
    rather than a fixed marketing number.
    """
    items_catalogued = Item.query.count()
    estimated_value = db.session.query(func.sum(Item.estimated_value)).scalar() or 0
    never_worn = Item.query.filter(Item.wear_frequency == "Never worn").count()
    ready_to_resell = db.session.query(func.sum(Item.estimated_value)).filter(
        Item.resale_willingness.in_(SALES_RESALE)
    ).scalar() or 0
 
    # The most-owned category, and how much of it sits unworn — the kind of
    # pattern the whole system exists to surface.
    top_category = (
        db.session.query(Item.category, func.count(Item.id))
        .filter(Item.category.isnot(None), Item.category != "")
        .group_by(Item.category)
        .order_by(func.count(Item.id).desc())
        .first()
    )
 
    return render_template(
        "index.html",
        items_catalogued=items_catalogued,
        estimated_value=estimated_value,
        never_worn=never_worn,
        ready_to_resell=ready_to_resell,
        top_category_name=top_category[0] if top_category else None,
        top_category_count=top_category[1] if top_category else 0,
    )
 
 
@app.route("/wardrobe")
def wardrobe():
    """Items still being kept — everything not headed for the Sales page."""
    items = (
        Item.query
        .filter(~Item.resale_willingness.in_(SALES_RESALE))
        .order_by(Item.item_name)
        .all()
    )
    total_value = sum(item.estimated_value or 0 for item in items)
 
    return render_template(
        "wardrobe.html",
        items=items,
        total_value=total_value,
        field_options=build_field_options(),
        item_types=item_type_options(),
        sale_statuses=SALE_STATUSES,
    )
 
 
@app.route("/sales")
def sales():
    """Items marked for resale, with their sale progress.
 
    The headline figures follow the pipeline: how many items are here, the
    value still being prepared, the value actually listed, and what has been
    earned so far.
    """
    items = (
        Item.query
        .filter(Item.resale_willingness.in_(SALES_RESALE))
        .order_by(Item.item_name)
        .all()
    )
 
    def price(item):
        return item.listing_price if item.listing_price is not None else (item.estimated_value or 0)
 
    revenue = sum(i.sold_for or 0 for i in items if i.is_sold)
    listed_value = sum(price(i) for i in items if i.sale_status == "Listed")
    not_listed_value = sum(
        price(i) for i in items
        if not i.is_sold and i.sale_status != "Listed"
    )
 
    return render_template(
        "sales.html",
        items=items,
        item_count=len(items),
        not_listed_value=not_listed_value,
        listed_value=listed_value,
        revenue=revenue,
        field_options=build_field_options(),
        item_types=item_type_options(),
        sale_statuses=SALE_STATUSES,
        sold_statuses=SOLD_STATUSES,
    )
 
 
@app.route("/opening-your-banq")
def opening_your_banq():
    """Static onboarding guide."""
    return render_template("opening_your_banq.html")
 
 
@app.route("/progress")
def progress():
    """Wardrobe and sales totals computed from the live database."""
    total_value = db.session.query(func.sum(Item.estimated_value)).scalar() or 0
    rarely_worn_value = db.session.query(func.sum(Item.estimated_value)).filter(
        Item.wear_frequency.in_(["Rarely", "Never worn"])
    ).scalar() or 0
    value_to_resell = db.session.query(func.sum(Item.estimated_value)).filter(
        Item.resale_willingness.in_(SALES_RESALE + ["Maybe sell"])
    ).scalar() or 0
 
    items_lodged = Item.query.count()
    items_listed = Item.query.filter(Item.resale_willingness.in_(SALES_RESALE)).count()
    items_sold = Item.query.filter(Item.sale_status.in_(SOLD_STATUSES)).count()
 
    total_revenue = db.session.query(func.sum(Item.sold_for)).filter(
        Item.sale_status.in_(SOLD_STATUSES)
    ).scalar() or 0
    listed_value = db.session.query(func.sum(Item.listing_price)).filter(
        Item.resale_willingness.in_(SALES_RESALE),
        ~Item.sale_status.in_(SOLD_STATUSES),
    ).scalar() or 0
 
    return render_template(
        "progress.html",
        total_value=total_value,
        rarely_worn_value=rarely_worn_value,
        value_to_resell=value_to_resell,
        items_lodged=items_lodged,
        items_listed=items_listed,
        items_sold=items_sold,
        total_revenue=total_revenue,
        listed_value=listed_value,
    )
 
 
@app.route("/api/items/<int:item_id>", methods=["POST"])
def update_item(item_id):
    """Apply inline edits to one item and report where it now belongs.
 
    The response tells the page whether the item has crossed between Wardrobe
    and Sales, so the row can be removed without a full reload.
    """
    item = Item.query.get_or_404(item_id)
    changes = request.get_json(silent=True) or {}
    was_on_sales = item.on_sales
 
    for field, value in changes.items():
        if field in EDITABLE_TEXT:
            setattr(item, field, (value or "").strip())
        elif field in EDITABLE_NUMBER:
            setattr(item, field, parse_float(value))
        elif field in EDITABLE_DATE:
            setattr(item, field, parse_date(value))
 
    # "Keep instead" is the escape hatch on the Sales page: it sends the item
    # back to the wardrobe rather than recording any kind of sale.
    if changes.get("sale_status") == "Keep instead":
        item.resale_willingness = "Keep for now"
        item.sale_status = None
        item.date_listed = None
        item.date_sold = None
        item.sold_for = None
 
    # Newly headed for resale: seed the sale fields so the row is usable.
    if item.on_sales and not was_on_sales:
        if not item.sale_status:
            item.sale_status = "To prep"
        if item.listing_price is None:
            item.listing_price = item.estimated_value
 
    # Marking something sold without a date is almost always today.
    if item.sale_status in SOLD_STATUSES and item.date_sold is None:
        item.date_sold = date.today()
 
    db.session.commit()
 
    return jsonify({
        "ok": True,
        "id": item.id,
        "on_sales": item.on_sales,
        "moved": item.on_sales != was_on_sales,
        "days_to_sell": item.days_to_sell,
        "is_sold": item.is_sold,
        "sale_status": item.sale_status,
        "resale_willingness": item.resale_willingness,
        "listing_price": item.listing_price,
        "sold_for": item.sold_for,
        "date_listed": item.date_listed.isoformat() if item.date_listed else None,
        "date_sold": item.date_sold.isoformat() if item.date_sold else None,
    })
 
 
@app.route("/wardrobe/lodge", methods=["GET", "POST"])
def lodge_item():
    """Show the Lodge an Item form, and save a new item when it's submitted."""
    field_options = build_field_options()
    category_to_types = build_nested(SEED_CATEGORY_TYPES, Item.category, Item.item_type)
    country_to_cities = build_nested(SEED_COUNTRY_CITIES, Item.country, Item.location)
 
    if request.method == "POST":
        item_name = request.form.get("item_name", "").strip()
        if not item_name:
            return render_template(
                "lodge_item.html",
                field_options=field_options,
                category_to_types=category_to_types,
                country_to_cities=country_to_cities,
                closed_fields=sorted(CLOSED_FIELDS),
                error="Item name is required.",
            )
 
        estimated_value = parse_float(request.form.get("estimated_value"))
        resale = request.form.get("resale_willingness", "").strip()
 
        new_item = Item(
            item_name=item_name,
            category=request.form.get("category", "").strip(),
            item_type=request.form.get("item_type", "").strip(),
            colour=", ".join(request.form.getlist("colour")),
            detailing=", ".join(request.form.getlist("detailing")),
            style=", ".join(request.form.getlist("style")),
            context=", ".join(request.form.getlist("context")),
            brand=request.form.get("brand", "").strip(),
            source_type=request.form.get("source_type", "").strip(),
            purchase_method=request.form.get("purchase_method", "").strip(),
            source=request.form.get("source", "").strip(),
            country=request.form.get("country", "").strip(),
            location=request.form.get("location", "").strip(),
            wear_frequency=request.form.get("wear_frequency", "").strip(),
            estimated_value=estimated_value,
            resale_willingness=resale,
            item_rating=request.form.get("item_rating", "").strip(),
            notes=request.form.get("notes", "").strip(),
            ownership_status="Owned",
        )
 
        # Something lodged as already-for-sale lands on the Sales page ready
        # to work with: listing price starts at the value just entered.
        if resale in SALES_RESALE:
            new_item.sale_status = "To prep"
            new_item.listing_price = estimated_value
 
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for("lodge_item", added=1))
 
    return render_template(
        "lodge_item.html",
        field_options=field_options,
        category_to_types=category_to_types,
        country_to_cities=country_to_cities,
        closed_fields=sorted(CLOSED_FIELDS),
    )
 
 
with app.app_context():
    db.create_all()
 
if __name__ == "__main__":
    app.run(debug=True)
 
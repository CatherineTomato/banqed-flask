from flask import Flask, render_template, request, redirect, url_for
from models import db, Item, SaleListing
from options import (
    SEED_OPTIONS,
    SEED_CATEGORY_TYPES,
    SEED_COUNTRY_CITIES,
    CLOSED_FIELDS,
    merge_options,
)
from sqlalchemy import func
 
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///banqed.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
 
db.init_app(app)
 
# Which Item column backs each dropdown, and whether it holds a single value
# or a comma-separated list of them.
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
 
 
def parse_float(value):
    """Convert a form value to a float, or None if it's blank/invalid."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
 
 
def get_distinct_single(column):
    """Every distinct non-empty value in a single-value column."""
    rows = db.session.query(column).distinct().all()
    return {r[0].strip() for r in rows if r[0] and r[0].strip()}
 
 
def get_multi_values(column):
    """Every distinct value from a comma-separated column, split back out."""
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
    """Seeded sheet options first, then anything extra already in the database.
 
    Closed fields (wear frequency, resale willingness, item rating) are fixed
    scales, so they use the seed list exactly and ignore stray database values.
    """
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
    """Seeded parent/child pairings, plus any pairing already in the database.
 
    Used for category -> item types and country -> cities, which behave
    identically: choosing the parent narrows the child's options.
    """
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
 
 
@app.route("/")
def home():
    """Home page."""
    return render_template("index.html")
 
 
@app.route("/wardrobe")
def wardrobe():
    """List every item currently in the wardrobe."""
    items = Item.query.all()
    return render_template("wardrobe.html", items=items)
 
 
@app.route("/sales")
def sales():
    """List every sale listing."""
    listings = SaleListing.query.all()
    return render_template("sales.html", listings=listings)
 
 
@app.route("/opening-your-banq")
def opening_your_banq():
    """Static onboarding guide."""
    return render_template("opening_your_banq.html")
 
 
@app.route("/progress")
def progress():
    """Compute and display wardrobe/sales totals from the live database."""
    total_value = db.session.query(func.sum(Item.estimated_value)).scalar() or 0
    # Casing here must match what's actually stored: the source spreadsheet
    # uses "Never worn", not "Never Worn".
    rarely_worn_value = db.session.query(func.sum(Item.estimated_value)).filter(
        Item.wear_frequency.in_(["Rarely", "Never worn"])
    ).scalar() or 0
    value_to_resell = db.session.query(func.sum(Item.estimated_value)).filter(
        Item.resale_willingness.in_(["Sell now", "Maybe sell", "Sell if price is right"])
    ).scalar() or 0
 
    items_lodged = Item.query.count()
    items_listed = SaleListing.query.count()
 
    completed_statuses = ["Sold", "Posted", "Money received"]
 
    items_sold = SaleListing.query.filter(
        SaleListing.status.in_(completed_statuses)
    ).count()
 
    total_revenue = db.session.query(func.sum(SaleListing.sold_for)).filter(
        SaleListing.status.in_(completed_statuses)
    ).scalar() or 0
    listed_value = db.session.query(func.sum(SaleListing.listing_price)).filter(
        SaleListing.status.notin_(completed_statuses)
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
            estimated_value=parse_float(request.form.get("estimated_value")),
            resale_willingness=request.form.get("resale_willingness", "").strip(),
            item_rating=request.form.get("item_rating", "").strip(),
            notes=request.form.get("notes", "").strip(),
            ownership_status="Owned",
        )
        db.session.add(new_item)
        db.session.commit()
        # Back to the lodge form itself so the splash can play and the form
        # resets, ready for the next item.
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
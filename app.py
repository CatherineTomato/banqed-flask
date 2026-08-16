from flask import Flask, render_template, request, redirect, url_for
from models import db, Item, SaleListing
from sqlalchemy import func

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///banqed.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


def parse_float(value):
    """Convert a form value to a float, or None if it's blank/invalid."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_category_to_types():
    """Build a {category: [item types]} map from item types already in the database."""
    rows = db.session.query(Item.category, Item.item_type).distinct().all()
    category_to_types = {}
    for cat, itype in rows:
        if not cat:
            continue
        category_to_types.setdefault(cat, [])
        if itype and itype not in category_to_types[cat]:
            category_to_types[cat].append(itype)
    for cat in category_to_types:
        category_to_types[cat].sort()
    return category_to_types


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
    rarely_worn_value = db.session.query(func.sum(Item.estimated_value)).filter(
        Item.wear_frequency.in_(["Rarely", "Never Worn"])
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
    category_to_types = get_category_to_types()
    categories = sorted(category_to_types.keys())

    if request.method == "POST":
        item_name = request.form.get("item_name", "").strip()
        if not item_name:
            return render_template(
                "lodge_item.html",
                categories=categories,
                category_to_types=category_to_types,
                error="Item name is required.",
            )

        new_item = Item(
            item_name=item_name,
            category=request.form.get("category", "").strip(),
            item_type=request.form.get("item_type", "").strip(),
            colour=request.form.get("colour", "").strip(),
            brand=request.form.get("brand", "").strip(),
            wear_frequency=request.form.get("wear_frequency", "").strip(),
            estimated_value=parse_float(request.form.get("estimated_value")),
            resale_willingness=request.form.get("resale_willingness", "").strip(),
            size=request.form.get("size", "").strip(),
            notes=request.form.get("notes", "").strip(),
            ownership_status="Owned",
        )
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for("wardrobe"))

    return render_template(
        "lodge_item.html",
        categories=categories,
        category_to_types=category_to_types,
    )


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template
from models import db, Item, SaleListing
from sqlalchemy import func

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///banqed.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/wardrobe")
def wardrobe():
    items = Item.query.all()
    return render_template("wardrobe.html", items=items)

@app.route("/sales")
def sales():
    listings = SaleListing.query.all()
    return render_template("sales.html", listings=listings)

@app.route("/opening-your-banq")
def opening_your_banq():
    return render_template("opening_your_banq.html")

@app.route("/progress")
def progress():
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

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)


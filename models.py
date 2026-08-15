from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))
    item_type = db.Column(db.String(100))
    colour = db.Column(db.String(100))
    detailing = db.Column(db.String(200))
    style = db.Column(db.String(100))
    context = db.Column(db.String(100))
    brand = db.Column(db.String(100))
    source_type = db.Column(db.String(100))
    purchase_method = db.Column(db.String(100))
    source = db.Column(db.String(200))
    country = db.Column(db.String(100))
    location = db.Column(db.String(100))
    wear_frequency = db.Column(db.String(50))
    estimated_value = db.Column(db.Float)
    resale_willingness = db.Column(db.String(50))
    item_rating = db.Column(db.String(50))
    size = db.Column(db.String(50))
    notes = db.Column(db.Text)
    ownership_status = db.Column(db.String(50), default="Owned")

    def __repr__(self):
        return f"<Item {self.item_name}>"


class SaleListing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50))
    category = db.Column(db.String(100))
    item_type = db.Column(db.String(100))
    date_listed = db.Column(db.String(50))
    date_sold = db.Column(db.String(50))
    days_to_sell = db.Column(db.String(50))
    listing_price = db.Column(db.Float)
    sold_for = db.Column(db.Float)

    def __repr__(self):
        return f"<SaleListing {self.item_name}>"
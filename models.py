from flask_sqlalchemy import SQLAlchemy
 
db = SQLAlchemy()
 
# Resale willingness decides which page an item appears on. There is one row
# per garment — Sales is a filtered view of the wardrobe, not a separate list.
SALES_RESALE = ["Sell now", "Sell if price is right"]
WARDROBE_RESALE = ["Keep", "Keep for now", "Maybe sell"]
 
# Sale statuses meaning the item is finished with; hidden on Sales by default.
SOLD_STATUSES = ["Sold", "Posted", "Money received"]
 
SALE_STATUSES = [
    "To prep", "Washing", "Photographed", "Listed",
    "Sold", "Posted", "Money received", "Keep instead",
]
 
 
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
 
    # Identity
    item_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))
    item_type = db.Column(db.String(100))
    colour = db.Column(db.String(200))
    detailing = db.Column(db.String(200))
 
    # Wearing
    style = db.Column(db.String(200))
    context = db.Column(db.String(200))
 
    # Source
    brand = db.Column(db.String(100))
    source_type = db.Column(db.String(100))
    purchase_method = db.Column(db.String(100))
    source = db.Column(db.String(200))
    country = db.Column(db.String(100))
    location = db.Column(db.String(100))
 
    # Usage and value
    wear_frequency = db.Column(db.String(50))
    estimated_value = db.Column(db.Float)
    resale_willingness = db.Column(db.String(50))
    item_rating = db.Column(db.String(50))
    notes = db.Column(db.Text)
    ownership_status = db.Column(db.String(50), default="Owned")
 
    # Sale tracking — only meaningful while the item sits on the Sales page.
    sale_status = db.Column(db.String(50))
    date_listed = db.Column(db.Date)
    date_sold = db.Column(db.Date)
    listing_price = db.Column(db.Float)
    sold_for = db.Column(db.Float)
 
    @property
    def on_sales(self):
        """True when this item belongs on the Sales page rather than Wardrobe."""
        return self.resale_willingness in SALES_RESALE
 
    @property
    def is_sold(self):
        return self.sale_status in SOLD_STATUSES
 
    @property
    def days_to_sell(self):
        """Whole days between listing and sale. None until both dates exist."""
        if not self.date_listed or not self.date_sold:
            return None
        return (self.date_sold - self.date_listed).days
 
    def split(self, field):
        """A comma-separated column as a clean list, for multi-value filtering."""
        raw = getattr(self, field) or ""
        return [part.strip() for part in raw.split(",") if part.strip()]
 
    def __repr__(self):
        return f"<Item {self.item_name}>"
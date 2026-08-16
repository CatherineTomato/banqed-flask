from flask import Flask, render_template
from models import db, Item

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

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)


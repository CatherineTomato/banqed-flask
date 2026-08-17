"""Seed dropdown options, transcribed from the Settings tab of the BANQED
Google Sheet.
 
The order of each list here is deliberate: it controls the order values appear
in each dropdown, exactly as the spreadsheet intended. Any extra values already
present in the database but missing from these lists get appended
alphabetically, so nothing already lodged ever disappears from a dropdown.
"""
 
SEED_OPTIONS = {
    "category": [
        "Tops", "Jumpers", "Trousers", "Activewear", "Dresses", "Shorts",
        "Skirts", "Jackets", "Coats", "Shoes", "Swimwear", "Sleepwear",
        "Accessories",
    ],
    "colour": [
        "Black", "White", "Cream", "Grey", "Navy", "Blue", "Brown", "Beige",
        "Green", "Red", "Pink", "Purple", "Yellow", "Orange", "Gold", "Silver",
        "Khaki", "Multicolour",
    ],
    "detailing": [
        "Collared", "Polka dot", "Striped", "Sequined", "Ribbed", "Panelled",
        "Silk", "Knit", "Lace", "Fluffy", "Floral", "Patterned",
        "Button detailing", "Zip detailing", "Embellished", "Plain",
        "Contrast stitch", "Pleated", "Gingham", "Crochet", "Satin", "Frilled",
        "Fringe", "Pinstripe", "Leather", "Mesh", "Studded", "Glossy",
        "Cotton", "Metallic", "Animal print", "Asymmetric straps",
        "Square toe", "Pointed toe",
    ],
    "style": [
        "Office", "Party", "Minimal", "Funky", "Masculine", "Classic",
        "Feminine", "Streetwear", "Sporty", "Elegant", "Statement", "Casual",
        "Edgy", "Chic", "Basic",
    ],
    "context": [
        "Everyday", "Work", "Smart casual", "Formal", "Party", "Pub",
        "Special occasion", "Active", "Lounging", "Holiday",
    ],
    "source_type": [
        "Retail", "Second-hand", "Gift", "Hand-me-down", "Other",
    ],
    "purchase_method": [
        "Online", "In-person", "Not applicable",
    ],
    "source": [
        "Brand shop", "Charity shop", "Vintage shop", "Vinted", "Depop",
        "eBay", "Market", "Boutique", "My mum", "Family", "Other",
    ],
    "country": [
        "Ireland", "UK", "France", "Italy", "Spain", "Belgium", "Austria",
        "Portugal", "United States", "Online", "Unknown", "Other",
    ],
    "brand": [],  # no seed list in the sheet; built entirely from the database
    # location is nested under country — see SEED_COUNTRY_CITIES below.
    "location": [],
 
    # Fixed scales — closed vocabularies, no "add new".
    "wear_frequency": [
        "Weekly", "Monthly", "Every few months", "1-2 times a year",
        "Once a year", "Rarely", "Never worn",
    ],
    "resale_willingness": [
        "Keep", "Keep for now", "Maybe sell", "Sell if price is right",
        "Sell now",
    ],
    "item_rating": [
        "I love it", "I really like it", "I like it", "High potential",
        "Potential", "Neutral", "I don't like it", "Doesn't Fit",
    ],
}
 
# Fields whose values are a fixed scale — the dropdown offers no "+ Add new".
CLOSED_FIELDS = {"wear_frequency", "resale_willingness", "item_rating"}
 
# Fields that are nested under a parent field: {child: parent}
DEPENDENT_FIELDS = {
    "item_type": "category",
    "location": "country",
}
 
# Item types nested under each category, from Section 2 of the Settings tab.
SEED_CATEGORY_TYPES = {
    "Tops": [
        "Long sleeve top", "Short sleeve top", "Shirt",
        "Long sleeve turtleneck", "Sleveless turtleneck",
        "Short sleeved shirt", "Corset/Bandeau", "Crop top", "Tank top",
        "Halterneck", "Off-the-shoulder top", "Blouse", "Cardigan",
    ],
    "Jumpers": [
        "Turtleneck", "Sweater vest", "Hoodie", "Quarter zip", "Knit jumper",
    ],
    "Trousers": [
        "Jeans", "Cargo trousers", "Suit trousers", "Trousers",
    ],
    "Activewear": [
        "Leggings", "Active jacket", "Sports bra", "Sports top",
        "Sports shorts", "Tennis skirt", "Trackies",
    ],
    "Dresses": [
        "Mini dress", "Midi dress", "Maxi dress", "Evening dress", "Jumpsuit",
    ],
    "Shorts": [
        "Denim shorts", "Cargo shorts",
    ],
    "Skirts": [
        "Mini skirt", "Midi skirt", "Maxi skirt",
    ],
    "Jackets": [
        "Leather jacket", "Denim jacket", "Blazer", "Gilet", "Suit jacket",
        "Faux Fur jacket",
    ],
    "Coats": [
        "Rain coat", "Winter coat", "Trench coat", "Long formal coat",
    ],
    "Shoes": [
        "Slides", "Ballet flats", "Mules", "Heels", "Loafers", "Kitten heels",
        "Sandals", "Trainers", "Boots", "Leather Shoes",
    ],
    "Swimwear": [
        "Bikini", "Swimsuit", "Cover-up",
    ],
    "Sleepwear": [
        "Pyjama set", "Pyjama top", "Pyjama bottoms", "Nightdress", "Robe",
    ],
    "Accessories": [
        "Handbag", "Shoulder bag", "Backpack", "Gym bag", "Suitcase", "Belt",
        "Scarf", "Sun hat", "Knit hat", "Sunglasses", "Ring", "Tote bag",
        "Necklace", "Earrings", "Bracelet",
    ],
}
 
# Cities and towns nested under each country, so choosing a country narrows the
# location list the same way choosing a category narrows item types.
SEED_COUNTRY_CITIES = {
    "Ireland": [
        "Dublin", "Cork", "Galway", "Limerick", "Waterford", "Kilkenny",
        "Sligo", "Wexford", "Killarney", "Dingle", "Westport", "Bray",
        "Dún Laoghaire", "Drogheda", "Ennis", "Tralee", "Athlone",
    ],
    "UK": [
        "London", "Manchester", "Birmingham", "Edinburgh", "Glasgow",
        "Bristol", "Liverpool", "Leeds", "Brighton", "Oxford", "Cambridge",
        "Cardiff", "Belfast", "Newcastle", "Bath", "York", "Nottingham",
    ],
    "France": [
        "Paris", "Lyon", "Marseille", "Bordeaux", "Nice", "Lille", "Toulouse",
        "Nantes", "Strasbourg", "Cannes", "Montpellier",
    ],
    "Italy": [
        "Rome", "Milan", "Florence", "Bologna", "Venice", "Naples", "Turin",
        "Verona", "Treviso", "Palermo", "Genoa", "Bari",
    ],
    "Spain": [
        "Madrid", "Barcelona", "Seville", "Valencia", "Bilbao", "Granada",
        "Malaga", "San Sebastián", "Palma", "Zaragoza",
    ],
    "Belgium": [
        "Brussels", "Antwerp", "Ghent", "Bruges", "Leuven", "Liège",
    ],
    "Austria": [
        "Vienna", "Salzburg", "Innsbruck", "Graz", "Linz",
    ],
    "Portugal": [
        "Lisbon", "Porto", "Faro", "Sintra", "Braga", "Coimbra",
    ],
    "United States": [
        "New York", "Los Angeles", "Chicago", "San Francisco", "Boston",
        "Miami", "Austin", "Seattle", "Portland", "New Orleans",
    ],
    "Online": ["Online"],
    "Unknown": ["Unknown"],
    "Other": ["Other"],
}
 
 
def merge_options(seed, from_db):
    """Seed order first, then any database-only values appended alphabetically.
 
    Comparison is case-insensitive so 'navy' from the database doesn't show up
    as a duplicate alongside the seeded 'Navy'.
    """
    seen = {value.lower() for value in seed}
    extras = sorted({v for v in from_db if v and v.lower() not in seen})
    return list(seed) + extras
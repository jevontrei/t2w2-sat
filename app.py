from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

app = Flask(__name__)

# Connect Flask API/app to database                    DBMS       DB_DRIVER  DB_USER  DB_PASS  URL     PORT DB_NAME
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://apr_stds:123456@localhost:5432/t2w2"
# ^^ can write either local host or ~~~127.0.0.1? ^^

# create object:
db = SQLAlchemy(app)
ma = Marshmallow(app)


# Create a general class/Model [MVC] of a table (this is how you define table):
# no need to __init__ bc of inheritance:


class Product(db.Model):
    # Define the name of the table
    __tablename__ = "products"

    # Define the Primary key object [Column is also a class]:
    id = db.Column(db.Integer, primary_key=True)

    # Define other attributes
    name = db.Column(db.String(100), nullable=False)
    # no string length limit for description:
    description = db.Column(db.String)
    price = db.Column(db.Float)
    stock = db.Column(db.Integer)


# Create a schema (this is how you access table / fetch info from the DB):


class ProductSchema(ma.Schema):
    class Meta:
        # Fields:
        fields = ("id", "name", "description", "price", "stock")


# There are two ways... 1) To handle multiple products:
products_schema = ProductSchema(many=True)

# 2) To handle a single product:
product_schema = ProductSchema()


# CLI Commands - Custom
@app.cli.command("create")
def create_tables():
    db.create_all()
    print("Create all the tables")


# Create another command to seed values to the table:
@app.cli.command("seed")
def seed_tables():
    # Create a product object, there's two ways:
    # 1:
    product1 = Product(
        name="Fruits",
        description="Fresh Fruits",
        price=15.99,
        stock=100
    )

    # 2:
    product2 = Product()
    product2.name = "Vegetables"
    product2.description = "Fresh Vegetables"
    product2.price = 10.99
    product2.stock = 200

    # Another way... could use this instead of the below:
    # products = [product1, product2]
    # db.session.add_all(products)

    # Add to session:
    db.session.add(product1)
    db.session.add(product2)

    # Commit:
    db.session.commit()

    print("Tables seeded.")

# To drop (delete) the tables:


@app.cli.command("drop")
def drop_tables():
    db.drop_all()
    print("Tables dropped successfully.")


# Working with routes:
# Define routes (if methods=[""] is unspecified, it defaults to GET method):


@app.route("/products")
def get_products():
    # Need to convert SQL/HTTP? requests to/with python, send to database, fetch, convert/translate outcome and display:
    # SELECT * FROM products;:

    # stmt ~= statement:
    stmt = db.select(Product)

    # Multiple, not singular:
    products_list = db.session.scalars(stmt)
    # Serialisation
    data = products_schema.dump(products_list)
    return data


# Dynamic routing:


@app.route("/courses/<int:product_id>")
# localhost/products/100
def get_product(product_id):
    # SELECT * FROM products WHERE id = product_id;:
    stmt = db.select(Product).filter_by(id=product_id)

    # Singular, not multiple:
    product = db.session.scalar(stmt)

    # converting from db object to python object?:
    # if product exists:
    if product:
        data = product_schema.dump(product)
        return data
    else:
        return {"error": f"Product with id {product_id} does not exist"}, 404

# RECAP:
# /products, GET => getting all products
# /products/id, GET => get a specific product
# /products, POST => Adding a product
# /products/id, PUT/PATCH => Edit a product
# /products/id, DELETE => Delete a specific product


# ADD/CREATE:
@app.route("/products", methods=["POST"])
def add_product():
    product_fields = request.get_json()

    new_product = Product(
        name=product_fields.get("name"),
        description=product_fields.get("description"),
        price=product_fields.get("price"),
        stock=product_fields.get("stock"),
    )

    db.session.add(new_product)
    db.session.commit()
    return product_schema.dump(new_product), 201


# UPDATE [both put and patch to avoid redundancy]:
@app.route("/products/<int:product_id>", methods=["PUT", "PATCH"])
def update_product(product_id):
    # find product from DB w/ the specific id, product_id:
    stmt = db.select(Product).filter_by(id=product_id)

    # execute:
    product = db.session.scalar(stmt)

    # retrieve data from request body:
    body_data = request.get_json()

    # update [use if/else to generalise]:
    if product:
        product.name = body_data.get("name") or product.name
        product.description = body_data.get(
            "description") or product.description
        product.price = body_data.get("price") or product.price
        product.stock = body_data.get("stock") or product.stock

        # Commit [don't need to add, it's already in the session]:
        db.session.commit()
        return product_schema.dump(product)
    else:
        return {"error": f"Product with id {product_id} does not exist"}, 404

# DELETE:


@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    stmt = db.select(Product).filter_by(id=product_id)
    # OR:
    # stmt = db.select(Product).where(Product.id == product_id)
    # Execute:
    product = db.session.scalar(stmt)

    # if product exists:
    if product:
        db.session.delete(product)
        db.session.commit()
        return {"message": f"Product with id {product_id} has been deleted."}
    else:
        return {"error": f"Product with id {product_id} does not exist"}, 404

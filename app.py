from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

app = Flask(__name__)

# Connect Flask API/app to database BEFORE creating db object...  DBMS  DB_DRIVER  DB_USER  DB_PASS  URL  PORT DB_NAME
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://apr_stds:123456@localhost:5432/t2w2"
# ^^ can write either local host or ~~~127.0.0.1? ^^

# create database object AFTER configuring app / connecting API to DB:
db = SQLAlchemy(app)

# Create Marshmallow object:
ma = Marshmallow(app)


# Create a general class/Model [MVC] of a table (this is how you define a model/table):
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

# ^^ up to this point (and also maybe more after? idk) we're working with DDL... "definition" language ^^

# Create a marshmallow schema to convert SQL to python (this is how you access above table / fetch info from the DB):


class ProductSchema(ma.Schema):
    class Meta:
        # Fields tuple:
        fields = ("id", "name", "description", "price", "stock")


# Now need to create object of class ProductSchema. There are two ways... 1) To handle multiple/all tables?/products:
products_schema = ProductSchema(many=True)

# 2) To handle a single product:
product_schema = ProductSchema()


# CLI Commands - Custom:
# This is to enable typing "flask create" into the terminal (must be connected to correct db first, i.e. command prompt t2w2=#):
# This is a controller/s (MVC)?:
@app.cli.command("create")
def create_tables():
    # We've only create one table (Product) but in reality we'd have more:
    db.create_all()
    print("Create all the tables")


# Create another command to seed values to the table:
@app.cli.command("seed")
def seed_tables():
    # To create a product object, there's two ways:
    # Option 1:
    product1 = Product(
        name="Fruits",
        description="Fresh Fruits",
        price=15.99,
        stock=100
    )

    # Option 2:
    product2 = Product()
    product2.name = "Vegetables"
    product2.description = "Fresh Vegetables"
    product2.price = 10.99
    product2.stock = 200

    # Another way... could use this instead of the below (adding all things at once):
    # products = [product1, product2]
    # db.session.add_all(products)

    # Analogous to Git... Add to session (adding specific things individually... maybe less elegant):
    db.session.add(product1)
    db.session.add(product2)

    # Analogous to Git... Commit to session/database:
    db.session.commit()

    print("Tables seeded.")

# To drop (delete) the tables:


@app.cli.command("drop")
def drop_tables():
    db.drop_all()
    print("Tables dropped successfully.")


# Working with routes:
# Define routes (if methods=[""] is unspecified, it defaults to GET method):
# Static routing:
@app.route("/products")
def get_products():
    # Need to convert SQL/HTTP? requests to/with python, send to database, fetch, convert/translate outcome and display:
    # SELECT * FROM products;:

    # need to define a stmt (statement) that i'll be executing:
    # it's a statement object that represents the query itself:
    stmt = db.select(Product)

    # to execute stmt, we need to define another variable to store result in? as scalar/s:
    # Multiple "products" and "scalars", not singular:
    products_list = db.session.scalars(stmt)
    # Serialisation / and convert for python to understand using the "multiple products" version:
    data = products_schema.dump(products_list)
    return data


# Orrrr Dynamic routing... use <>, the contents of which is gotten from the frontend:
@app.route("/products/<int:product_id>")
# e.g. localhost/products/100
def get_product(product_id):
    # SELECT * FROM products WHERE id = product_id;:
    # In SQLAlchemy, can also use filter() instead of filter_by():
    stmt = db.select(Product).filter_by(id=product_id)
    # ^^ id is from backend; product_id is from frontend ^^

    # Execute stmt using scalar method/value; Singular "product" and "scalar", not multiple:
    product = db.session.scalar(stmt)

    # converting from db object to python object:
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


# The UPDATE request [both put and patch to avoid redundancy]:
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

# The DELETE request:


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

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

# t2w3-sat:
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from datetime import timedelta

# create instance?:
app = Flask(__name__)

# Connect Flask API/app to database BEFORE creating db object...  DBMS  DB_DRIVER  DB_USER  DB_PASS  URL  PORT DB_NAME
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://apr_stds:123456@localhost:5432/t2w2"
# ^^ can write either local host or ~~~127.0.0.1? ^^

# t2w3-sat:
app.config["JWT_SECRET_KEY"] = "secret"

# create database object AFTER configuring app / connecting API to DB:
db = SQLAlchemy(app)

# Create Marshmallow object:
ma = Marshmallow(app)

# t2w3-sat Create object:
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

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

# --------------------------------------------------------------------

# Adding stuff during t2w3-sat:


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# of course, need a schema for the User model/class:


class UserSchema(ma.Schema):
    class Meta:
        # Use a tuple bc it has to be unique:
        fields = ("id", "name", "email", "password", "is_admin")


# Plural:
users_schema = UserSchema(many=True, exclude=["password"])

# Singular:
user_schema = UserSchema(exclude=["password"])

# ?:


@app.route("/auth/register", methods=["POST"])
def register_user():
    # Encapsulate(?):
    try:
        # Body of the request:
        body_data = request.get_json()

        # Extract password from request body:
        password = body_data.get("password")

        # Hash the password [Aamod using single quotes for 'utf8'... important? prob not]:
        hashed_password = bcrypt.generate_password_hash(
            password).decode("utf8")

        # Create a user using the User model:
        user = User(
            name=body_data.get("name"),
            email=body_data.get("email"),
            password=hashed_password
        )

        # Add it to the db session:
        db.session.add(user)

        # Commit:
        db.session.commit()

        # Return something (e.g. acknowledgment message):
        return user_schema.dump(user), 201
    except IntegrityError:
        return {"error": "Email address already exists"}, 400

# NOT WORKING IN INSOMNIA! t2w3sat 11:44am:
# @app.route("/auth/login", methods=["POST"])
# def login_user():
#     # Find the user with that specific email:
#     body_data = request.get_json()

#     # If the user exists and the password matches:
#     # SELECT * FROM uses WHERE email="user1@gmail.com";:
#     stmt = db.select(User).filter_by(email=body_data.get("email"))
#     user = db.session.scalar(stmt)

#     # Create a jwt token (need to decrypt) (and specify expiry timeframe):
#     if user and bcrypt.check_password_hash(user.password, body_data.get("password")):
#         token = create_access_token(identity=str(user.id), expires_delta=timedelta(days=1))
#         # return the token:
#         return {
#             "token": token,
#             "email": user.email,
#             "is_admin": user.is_admin
#         }
#     else:
#         return {"error": "Invalid email or password"}, 401


@app.route("/auth/login", methods=["POST"])
def login_user():
    # Find the user with that email
    body_data = request.get_json()
    # If the user exists and the password matches
    # SELECT * FROM users WHERE email="user1@gmail.com"
    stmt = db.select(User).filter_by(email=body_data.get("email"))
    user = db.session.scalar(stmt)
    # Create a jwt token
    if user and bcrypt.check_password_hash(user.password, body_data.get("password")):
        token = create_access_token(identity=str(
            user.id), expires_delta=timedelta(days=1))
        return {"token": token, "email": user.email, "is_admin": user.is_admin}
    else:
        return {"error": "Invalid email or password"}, 401

# --------------------------------------------------------------------

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

    # Let's try doing it here, not in Insomnia(?):
    users = [
        User(
            name="User 1",
            email="user1@gmail.com",
            password=bcrypt.generate_password_hash("123456").decode("utf8")
        ),
        User(
            email="admin@gmail.com",
            password=bcrypt.generate_password_hash("abc123").decode("utf8"),
            is_admin=True
        )
    ]

    # Add... don't need to commit bc i'm committing down below:
    db.session.add_all(users)

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
    # In SQLAlchemy, can also use filter() instead of filter_by(), both are kinda like WHERE in SQL (python also may have a "where" function: see DELETE request below):
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


# ADD/CREATE a product to the database:
@app.route("/products", methods=["POST"])
# Understand this 11:48am t2w3sat:
@jwt_required()
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
@jwt_required()
def update_product(product_id):
    # find the product from DB w/ the specific id, product_id:
    stmt = db.select(Product).filter_by(id=product_id)

    # execute stmt:
    product = db.session.scalar(stmt)

    # retrieve data from request body:
    body_data = request.get_json()

    # update [use if/else to generalise]:
    # if product exists:
    if product:
        product.name = body_data.get("name") or product.name
        product.description = body_data.get(
            "description") or product.description
        product.price = body_data.get("price") or product.price
        product.stock = body_data.get("stock") or product.stock

        # Commit [don't need to add for put/patch, it's already in the session]:
        db.session.commit()
        return product_schema.dump(product)
    else:
        return {"error": f"Product with id {product_id} does not exist"}, 404

# The DELETE request (don't need anything in JSON body in Insomnia):


@app.route("/products/<int:product_id>", methods=["DELETE"])
# Need this for authentication:
@jwt_required()

def delete_product(product_id):
    
    # Authorise:
    is_admin = authoriseAsAdmin()
    if not is_admin:
        return {"error": "Not authorised to delete a product"}, 403
    
    # define statement:
    stmt = db.select(Product).filter_by(id=product_id)
    # OR (check this, not sure if where() exists like this):
    # stmt = db.select(Product).where(Product.id == product_id)

    # Execute stmt:
    product = db.session.scalar(stmt)

    # if product exists:
    if product:
        db.session.delete(product)
        # still need to commit too:
        db.session.commit()
        return {"message": f"Product with id {product_id} has been deleted."}
    else:
        return {"error": f"Product with id {product_id} does not exist"}, 404

# random/unusual use of pascal case? doesn't matter? just convention?:


def authoriseAsAdmin():
    # get the id of the user from the jwt token:
    user_id = get_jwt_identity()

    # find the user in the db with the id:
    stmt = db.select(User).filter_by(id=user_id)
    user = db.session.scalar(stmt)

    # check whether user is an admin or not:
    return user.is_admin

    # OR Luke Harris's method:
    # Check if the user is an admin
    # if user.is_admin:
    #     return True
    # else:
    #     return False
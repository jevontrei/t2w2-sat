from flask import Flask, request, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, set_access_cookies, jwt_required, get_jwt_identity
from dotenv import load_dotenv
import os
from datetime import timedelta

load_dotenv()


app = Flask(__name__)

# Connect to database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Define a User model that will be used to store user data in the database.
# The model is defined as a class that inherits from the `db.Model` class provided by Flask-SQLAlchemy.
class User (db.Model):
    # The `__tablename__` attribute specifies the name of the database table that will be created to store User data.
    __tablename__ = 'users'
    
    # Define the columns of the User table. Each column is represented by a class attribute that is an instance of the
    # `db.Column` class. The `db.Column` class has several parameters that define the properties of the column, such as
    # its data type, whether it is nullable or not, and whether it is unique.
    
    # The `id` column is an auto-incrementing primary key column that will be used to uniquely identify each user.
    id = db.Column(db.Integer, primary_key=True)
    
    # The `username` column is a unique string column that will store the username of each user.
    username = db.Column(db.String(80), unique=True, nullable=False)
    
    # The `email` column is a unique string column that will store the email address of each user.
    email = db.Column(db.String(120), unique=True, nullable=False)
    
    # The `password` column is a string column that will store the password of each user.
    password = db.Column(db.String(), nullable=False)
    
    # The `is_admin` column is a boolean column that will store whether each user is an admin or not. It defaults to False.
    is_admin = db.Column(db.Boolean, default=False)

# Define a schema for the User class that will be used to serialize and deserialize User objects.
# The schema is defined as a class that inherits from the `ma.Schema` class provided by Flask-Marshmallow.
class UserSchema(ma.Schema):
    # The `Meta` class inside the schema is used to specify additional metadata about the schema.
    # In this case, we specify the fields that should be included in the serialized and deserialized output.
    # The `fields` attribute is a tuple that lists the names of the fields that should be included.
    class Meta:
        # The `fields` attribute is a tuple that lists the names of the fields that should be included.
        # In this case, we include the `id`, `username`, `email`, `password`, and `is_admin` fields.
        fields = ('id', 'username', 'email', 'password', 'is_admin')

user_schema = UserSchema(exclude=['password'])
users_schema = UserSchema(many=True, exclude=['password']) 

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    stock = db.Column(db.Integer)

class ProductSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'price', 'description', 'stock')

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)



@app.cli.command('create_db')
def create_tables():
    """
    This function is a command-line interface (CLI) command that creates the database tables.
    It is executed when the 'flask create_db' command is run from the command line.

    This function does the following:
    - Prints a message to indicate that the tables are being created.
    - Calls the `db.create_all()` function to create all the database tables defined in the Flask-SQLAlchemy `db` object.
    - Prints a message to indicate that the tables have been created.
    """

    # Print a message to indicate that the tables are being created
    print("Creating tables")

    # Call the `db.create_all()` function to create all the database tables defined in the Flask-SQLAlchemy `db` object
    db.create_all()

    # Print a message to indicate that the tables have been created
    print("Tables created")

@app.cli.command('seed')
def seed_db():
    """
    This function is a command-line interface (CLI) command that seeds the database with some initial data.
    It is executed when the 'flask seed' command is run from the command line.

    This function does the following:
    - Prints a message to indicate that the database is being seeded.
    - Creates two instances of the Product model, each with a name, description, price, and stock value.
    - Adds the instances to the database session.
    - Commits the changes to the database.
    - Prints a message to indicate that the database has been seeded.
    """

    # Print a message to indicate that the database is being seeded
    print("Seeding database")

    # Create an instance of the Product model with a name, description, price, and stock value
    product1 = Product(
        name="Fruit",  # The name of the product
        description="Fresh fruit",  # The description of the product
        price=15.99,  # The price of the product
        stock=100  # The stock of the product
    )

    # Create another instance of the Product model with a name, description, price, and stock value
    product2 = Product(
        name="Vegetable",  # The name of the product
        description="Fresh vegetable",  # The description of the product
        price=10.99,  # The price of the product
        stock=100  # The stock of the product
    )

    # Create a list of the two instances
    products = [product1, product2]

    # Add the instances to the database session
    db.session.add_all(products)

    # Commit the changes to the database
    db.session.commit()

    # Print a message to indicate that the database has been seeded
    print("Database seeded")
    

@app.cli.command('drop')  # This decorator is used to define a command-line interface (CLI) command
def drop_db():  # This function is the command-line interface (CLI) command
    # Print a message to indicate that the tables are being dropped
    print("Dropping tables")
    
    # Call the `db.drop_all()` function to drop all the database tables defined in the Flask-SQLAlchemy `db` object
    # This function drops all the database tables associated with the Flask-SQLAlchemy `db` object
    db.drop_all()
    
    # Print a message to indicate that the tables have been dropped
    # This message is printed after the `db.drop_all()` function is called to indicate that the tables have been successfully dropped
    print("Tables dropped")

@app.route("/products")
def get_products():
    stmt = db.select(Product)

    products_list = db.session.scalars(stmt)

    data = products_schema.dump(products_list)

    return data

# Dynamic routing
@app.route("/products/<int:product_id>")
def get_product(product_id):
    # This route defines a dynamic endpoint that returns a product based on its ID
    
    # The `product_id` parameter is an integer that represents the ID of the product we want to retrieve
    
    # We use the Flask-SQLAlchemy `db` object to define a SQLAlchemy query that selects a product from the database
    # The query filters the products table for a row with an ID that matches the `product_id` parameter
    stmt = db.select(Product).filter_by(id=product_id)
    
    # We execute the query and retrieve the first result (if any) using the `scalar()` method
    # The `scalar()` method returns a single result, or None if no result is found
    product = db.session.scalar(stmt)
    
    # If a product is found, we serialize it to JSON using the `jsonify()` method of the `product_schema` object
    # The `jsonify()` method converts a Python object to a JSON response
    # If no product is found, we return a JSON response with a message indicating that the product was not found
    try:
        return product_schema.dump(product)
    except:
        return {"message": "Product not found"}, 404
    
@app.route("/products", methods=["POST"])
@jwt_required() # This line uses the Flask-JWT-Extended library to require a valid JWT (JSON Web Token) for this endpoint
def create_product():
    # This function creates a new product in the database using data sent in a JSON payload in the request body.
    # The function loads the data from the request body into a Python dictionary using the `product_schema.load()` method.
    # This method ensures that the data in the request body is valid according to the schema defined in `product_schema`.
    # The function then creates a new `Product` object using the data from the dictionary and saves it to the database using the `db.session.add()` method.
    # The `db.session.commit()` method saves the changes to the database.
    # After the product is saved to the database, the function retrieves all the products from the database using the `db.session.scalars()` method.
    # The `products_schema.dump()` method serializes the products to JSON and returns them in the response body with a status code of 201 (Created).
    
    # Load the data from the request body into a Python dictionary using the `product_schema.load()` method
    data = product_schema.load(request.json)
    
    # Create a new `Product` object using the data from the dictionary and save it to the database
    product = Product(
        name = data["name"], # Set the name of the product
        price = data["price"], # Set the price of the product
        description = data["description"], # Set the description of the product
        stock = data["stock"] # Set the stock of the product
    )
    db.session.add(product) # Add the product to the database session
    db.session.commit() # Save the changes to the database
    
    # Retrieve all the products from the database
    products = db.session.scalars(db.select(Product))
    
    # Serialize the products to JSON and return them in the response body with a status code of 201 (Created)
    data = products_schema.dump(products)
    
    return data, 201 # Return the JSON response and the status code

@app.route("/products/<int:product_id>", methods=["PUT", "PATCH"])
def update_product(product_id):
    # This route defines a dynamic endpoint that updates a product in the database based on its ID
    
    # Define a SQLAlchemy query that selects a product from the database based on its ID
    stmt = db.select(Product).filter_by(id=product_id)
    
    # Execute the query and retrieve the first result (if any) using the `scalar()` method
    # The `scalar()` method returns a single result, or None if no result is found
    product = db.session.scalar(stmt)
    
    # Check if a product was found
    if product:
        # Load the data from the request body into a Python dictionary using the `product_schema.load()` method
        # This method ensures that the data in the request body is valid according to the schema defined in `product_schema`
        data = product_schema.load(request.json)
        
        # Update the product object with the new data from the request body
        # If a field is not provided in the request body, keep the existing value
        product.name = data["name"] or product.name # Set the name of the product
        product.price = data["price"] or product.price # Set the price of the product
        product.description = data["description"] or product.description # Set the description of the product
        product.stock = data["stock"] or product.stock # Set the stock of the product
        
        # Save the changes to the database
        db.session.commit()
        
        # Retrieve all the products from the database
        products = db.session.scalars(db.select(Product))
        
        # Serialize the products to JSON
        data = products_schema.dump(products)
        
        # Return the JSON response
        return data
    else:
        # Return a JSON response indicating that the product was not found
        return {"message": "Product not found"}, 404
    
def auth_as_admin():
    """
    This function checks if the user making the request is an admin.
    
    It does this by:
    1. Getting the identity (i.e., the user's ID) from the JWT token.
    2. Fetching the user from the database using the identity obtained in step 1.
    3. Checking if the user exists. If not, it returns False.
    4. Checking if the user is an admin. If not, it returns False.
    5. If the user is an admin, it returns True.
    """
    
    # Get the identity from the JWT token
    # The JWT token (JSON Web Token) is a compact, URL-safe means of representing claims between two parties.
    # In this case, the identity refers to the user's ID.
    identity = get_jwt_identity()
    
    # Fetch the user from the database using the identity obtained in step 1
    # The database query filters the users table for a row with an ID that matches the identity.
    # The `first()` method retrieves the first result (if any) from the query result.
    user = User.query.filter_by(id=identity).first()
    
    # Check if the user exists
    # If the user does not exist, return False
    if not user:
        return False
    
    # Check if the user is an admin
    # If the user is not an admin, return False
    if not user.is_admin:
        return False
    
    # If the user is an admin, return True
    return True
    

# This route is used to check if the user making the request is an admin.
# It accepts GET requests and requires a valid JWT token to access the endpoint.
# The route returns a string representation of a boolean value indicating
# whether the user is an admin or not.
@app.route("/is_admin")
@jwt_required()  # This line uses the Flask-JWT-Extended library to require a valid JWT (JSON Web Token) for this endpoint
def is_admin():
    # Call the auth_as_admin() function to check if the user making the request is an admin.
    # The auth_as_admin() function retrieves the identity from the JWT token
    # and fetches the user from the database using the identity.
    # It then checks if the user exists and if the user is an admin.
    # If the user is an admin, the function returns True, otherwise it returns False.
    # The return value of the auth_as_admin() function is converted to a string using the str() function.
    # The string representation of the boolean value is then returned in the response body.
    return str(auth_as_admin())

@app.route("/products/<int:product_id>", methods=["DELETE"])
@jwt_required()
def delete_product(product_id):
    """
    This route is used to delete a product from the database.
    It accepts DELETE requests and requires a valid JWT token to access the endpoint.
    The route parameters include the product ID.
    The route first checks if the user making the request is an admin.
    If the user is not an admin, it returns a 401 Unauthorized response.
    If the user is an admin, it proceeds to delete the product from the database.
    It first constructs a SQLAlchemy query to fetch the product from the database using the product ID.
    It then executes the query and retrieves the first result (if any) using the `scalar()` method.
    If a product is found, it deletes the product from the database session using the `delete()` method.
    It then commits the changes to the database using the `commit()` method.
    Finally, it returns a JSON response indicating that the product has been deleted.
    If no product is found, it returns a JSON response indicating that the product was not found with a 404 Not Found status code.
    """
    
    # Check if the user making the request is an admin
    # If the user is not an admin, return a 401 Unauthorized response
    if not auth_as_admin():
        return {"message": "Unauthorized"}, 401

    # Construct a SQLAlchemy query to fetch the product from the database using the product ID
    stmt = db.select(Product).filter_by(id=product_id)

    # Execute the query and retrieve the first result (if any) using the `scalar()` method
    product = db.session.scalar(stmt)

    # Check if a product was found
    if product:
        # Delete the product from the database session
        db.session.delete(product)

        # Commit the changes to the database
        db.session.commit()

        # Return a JSON response indicating that the product has been deleted
        return {"message": "Product deleted"}
    else:
        # Return a JSON response indicating that the product was not found with a 404 Not Found status code
        return {"message": "Product not found"}, 404

@app.route("/auth/register", methods=["POST"])
def register():
    """
    This function handles the registration of a new user.
    It accepts POST requests to the "/auth/register" endpoint.
    It expects a JSON payload in the request body with the following fields:
    - username: the desired username for the new user
    - email: the desired email for the new user
    - password: the desired password for the new user

    If any of the required fields is missing, it returns a 400 Bad Request response with an error message.
    If the password is less than 8 characters, it returns a 400 Bad Request response with an error message.
    If a user with the same username or email already exists, it returns a 400 Bad Request response with an error message.
    If the input is valid, it hashes the password using bcrypt and creates a new User object with the provided username, email, hashed password, and is_admin flag (defaulting to False if not provided).
    It adds the new user to the database session and commits the changes.
    It returns a JSON response with the newly created user object and a 201 Created status code.
    If any exception occurs during the registration process, it returns a JSON response with the error message and a 500 Internal Server Error status code.
    """
    
    try:
        # Extract the username, email, and password from the request body
        data = request.json
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        # Check if all required fields are present
        if not username or not email or not password:
            return {"message": "Missing username, email, or password"}, 400

        # Check if the password is at least 8 characters long
        if len(password) < 8:
            return {"message": "Password must be at least 8 characters"}, 400

        # Check if a user with the same username or email already exists
        if User.query.filter_by(username=username).first():
            return {"message": "Username already exists"}, 400
        if User.query.filter_by(email=email).first():
            return {"message": "Email already exists"}, 400

        # Hash the password using bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # Create a new User object with the provided data
        user = User(
            username = username,
            email = email,
            password = hashed_password,
            is_admin = data.get("is_admin", False)
        )

        # Add the new user to the database session and commit the changes
        db.session.add(user)
        db.session.commit()

        # Return a JSON response with the newly created user object and a 201 Created status code
        return user_schema.jsonify(user), 201
    except Exception as e:
        # Return a JSON response with the error message and a 500 Internal Server Error status code if an exception occurs
        return {"message": str(e)}, 500


@app.route("/auth/login", methods=["POST"])
def login():
    # Get the JSON data from the request body
    data = request.json

    # Extract the username, email, and password from the request body
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    # Check if either the username or email is missing from the request body
    if not username and not email:
       # If both are missing, return an error message with a 400 status code
       return {"message": "Missing username or email"}, 400

    # Check if the password is missing from the request body
    if not password:
        # If the password is missing, return an error message with a 400 status code
        return {"message": "Missing password"}, 400

    # Attempt to find a user in the database with the provided username
    user = User.query.filter_by(username=username).first()

    # If no user was found with the provided username, attempt to find a user with the provided email
    if not user:
        user = User.query.filter_by(email=email).first()

    # Check if a user was found
    if not user:
        # If no user was found, return an error message with a 401 status code
        return {"message": "Invalid username or password"}, 401

    # Check if the provided password matches the hashed password stored in the database
    if not bcrypt.check_password_hash(user.password, password):
        # If the provided password does not match the hashed password, return an error message with a 401 status code
        return {"message": "Invalid username or password"}, 401
    
    # Generate a JWT token with the user's ID as the identity and a 1-day expiration
    token = create_access_token(identity=str(user.id), expires_delta=timedelta(days=1))

    # Create a response object with the token, user email, and is_admin flag as JSON data
    response = make_response({"token": token, "email": user.email, "is_admin": user.is_admin}, 200)

    # Set the JWT token as an access cookie in the response
    set_access_cookies(response, token)

    # Return the response object with the token, user email, and is_admin flag as JSON data
    return response
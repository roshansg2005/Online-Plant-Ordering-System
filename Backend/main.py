import os
import base64
from werkzeug.security import generate_password_hash
from flask import Flask, request, jsonify,session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from random import randint
from werkzeug.security import generate_password_hash
from config import Config
from flask_cors import CORS
from werkzeug.utils import secure_filename
import json
from sqlalchemy import func

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'my_secret_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:postgres@localhost/plant_ordering_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
CORS(app,resources={r"/*": {"origins": "*"}})



app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'roshansg2005@gmail.com'
app.config['MAIL_PASSWORD'] = 'mngjicvjdppgfljq'  # Use your App Password here
app.config['MAIL_DEFAULT_SENDER'] = 'roshansg2005@gmail.com'

mail = Mail(app)

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)  # Phone number
    street_address = db.Column(db.String(255), nullable=True)  # Address
    city = db.Column(db.String(100), nullable=True)  # City
    state = db.Column(db.String(100), nullable=True)  # State
    postal_code = db.Column(db.String(20), nullable=True)  # Postal Code
    profile_pic = db.Column(db.Text, nullable=True)  #
    otp = db.Column(db.String(6), nullable=True)
    otp_expiration = db.Column(db.DateTime, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='customer')

class Nursery(db.Model):
    __tablename__ = 'nurseries'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    otp = db.Column(db.String(6), nullable=True)
    otp_expiration = db.Column(db.DateTime, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='nursery')
    business_name = db.Column(db.String(255), nullable=True)
    business_hours = db.Column(db.String(255))  # New field
    description = db.Column(db.Text)
    phone_number = db.Column(db.String(20), nullable=True)
    street_address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    profile_pic = db.Column(db.Text, nullable=True)  # Stores base64 image
    nursery_images = db.Column(db.ARRAY(db.Text), nullable=True) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    otp = db.Column(db.String(6), nullable=True)
    otp_expiration = db.Column(db.DateTime, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='admin')

class Plant(db.Model):
    __tablename__ = 'plants'
    id = db.Column(db.Integer, primary_key=True)
    plant_name = db.Column(db.String(255), nullable=False)
    sub_name = db.Column(db.String(255), nullable=False)
    plant_type = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    plant_image = db.Column(db.Text, nullable=True)  # Stores base64 image
    
    # Reference to nursery's email
    nursery_email = db.Column(db.String(100), db.ForeignKey('nurseries.email'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship between Plant and Nursery
    nursery = db.relationship('Nursery', backref='plants')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)

    # Separate address fields
    street_address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    state = db.Column(db.String(100), nullable=False)

    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Price of the product
    nursery_email = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(100), nullable=False)
    order_date = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Order {self.id}>'

    # Total price calculation
    @property
    def total_price(self):
        return self.price * self.quantity

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)

    def __init__(self, name, email, subject, message):
        self.name = name
        self.email = email
        self.subject = subject
        self.message = message


with app.app_context():
    db.create_all()

# OTP Generator
def generate_otp():
    return randint(100000, 999999)

# Send OTP Route for Login
@app.route('/login/send-otp', methods=['POST'])
def send_login_otp():
    data = request.json
    email = data.get('email')

    # Check if the user is an admin, customer, or nursery
    user = Admin.query.filter_by(email=email).first() or \
           Customer.query.filter_by(email=email).first() or \
           Nursery.query.filter_by(email=email).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    # Generate OTP
    otp = str(generate_otp())
    user.otp = otp
    user.otp_expiration = datetime.now() + timedelta(minutes=10)  # OTP valid for 10 minutes
    db.session.commit()

    # Send OTP via email
    msg = Message('Your OTP Code for Login', sender='roshansg2005@gmail.com', recipients=[email])
    msg.body = f'Your OTP is {otp}. It is valid for 10 minutes.'
    mail.send(msg)

    return jsonify({"message": "OTP sent to your email"}), 200

@app.route('/login/verify-otp', methods=['POST'])
def verify_login_otp():
    data = request.json
    email = data.get('email')
    otp = data.get('otp')

    # Check if the user is an admin, customer, or nursery
    user = Admin.query.filter_by(email=email).first() or \
           Customer.query.filter_by(email=email).first() or \
           Nursery.query.filter_by(email=email).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    if user.otp == otp and datetime.now() < user.otp_expiration:
        user.otp = None  # Clear OTP after successful verification
        user.otp_expiration = None
        db.session.commit()

        # Retrieve the correct name based on the user's role
        if isinstance(user, Customer):
            user_name = user.name
        elif isinstance(user, Nursery):
            user_name = user.first_name
        else:
            user_name = "Admin"
        
        return jsonify({
            "message": f"Login successful for {user.role}",
            "role": user.role,
            "email": user.email,  # Return the user's email here
            "user_name": user_name,  # Return the user's name here
            "user_id": user.id,
            "profile_pic":user.profile_pic
        }), 200
    else:
        return jsonify({"message": "Invalid or expired OTP"}), 400

# Resend OTP Route
@app.route('/login/resend-otp', methods=['POST'])
def resend_login_otp():
    data = request.json
    email = data.get('email')

    # Check if user exists in Customer or Nursery
    user = Customer.query.filter_by(email=email).first() or Nursery.query.filter_by(email=email).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    # Generate a new OTP and set expiration
    otp = str(generate_otp())
    user.otp = otp
    user.otp_expiration = datetime.now() + timedelta(minutes=10)
    db.session.commit()

    # Resend OTP via email
    msg = Message('Your OTP Code for Login', sender='roshansg2005@gmail.com', recipients=[email])
    msg.body = f'Your new OTP is {otp}. It is valid for 10 minutes.'
    mail.send(msg)

    return jsonify({"message": "New OTP sent to your email"}), 200

# Customer Registration Route
@app.route('/register/customer', methods=['POST'])
def register_customer():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    role = data.get('role', 'customer')  # Default to 'customer' unless specified otherwise

    # Check if customer already exists
    existing_customer = Customer.query.filter_by(email=email).first()
    if existing_customer:
        return jsonify({"message": "Customer already registered"}), 400

    # Set role to 'nursery' if registering through a nursery
    if role == 'nursery':
        role = 'nursery'

    # Generate OTP and save it to the database
    otp = str(generate_otp())
    customer = Customer(name=name, email=email, otp=otp, otp_expiration=datetime.now() + timedelta(minutes=10), role=role)
    db.session.add(customer)
    db.session.commit()

    # Send OTP via email
    msg = Message('Customer Registration OTP', sender='roshansg2005@gmail.com', recipients=[email])
    msg.body = f'Your OTP is {otp}. It is valid for 10 minutes.'
    mail.send(msg)

    return jsonify({"message": "OTP sent to your email", "role": role}), 200

@app.route('/register/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = data.get('email')
    otp = data.get('otp')

    # Find the customer based on the provided email
    customer = Customer.query.filter_by(email=email).first()

    if customer and customer.otp == otp and customer.otp_expiration > datetime.now():
        return jsonify({"message": "OTP verified successfully"}), 200
    else:
        return jsonify({"message": "Invalid or expired OTP"}), 400


@app.route('/register/send-otp', methods=['POST'])
def send_otp():
    data = request.json
    email = data.get('email')

    # Check if nursery already exists
    existing_nursery = Nursery.query.filter_by(email=email).first()
    if existing_nursery:
        return jsonify({"message": "Nursery already registered"}), 400

    # Generate OTP and send email
    otp = str(generate_otp())
    otp_expiration = datetime.now() + timedelta(minutes=10)

    # Send OTP via email
    msg = Message('Nursery Registration OTP', sender='your_email@gmail.com', recipients=[email])
    msg.body = f'Your OTP is {otp}. It is valid for 10 minutes.'
    mail.send(msg)

    # Create a new nursery entry with only email and OTP for now
    nursery = Nursery(
        first_name='', email=email, password_hash='', otp=otp, otp_expiration=otp_expiration
    )
    db.session.add(nursery)
    db.session.commit()

    return jsonify({"message": "OTP sent to your email"}), 200

# Nursery OTP verification route
@app.route('/register/nursery/verify-otp', methods=['POST'])
def verify_nursery_otp():
    data = request.json
    email = data.get('email')
    otp = data.get('otp')

    # Check if nursery exists and OTP is valid
    nursery = Nursery.query.filter_by(email=email).first()
    if not nursery:
        return jsonify({"message": "Nursery not found"}), 404

    if nursery.otp != otp:
        return jsonify({"message": "Invalid OTP"}), 400

    if datetime.now() > nursery.otp_expiration:
        return jsonify({"message": "OTP has expired"}), 400

    # OTP verified successfully
    return jsonify({"message": "OTP verified successfully"}), 200

# Route for nursery registration (after OTP verification)
@app.route('/register/nursery', methods=['POST'])
def register_nursery():
    data = request.json
    first_name = data.get('first_name')
    email = data.get('email')
    password = data.get('password')
    business_name = data.get('business_name')
    phone_number = data.get('phone_number')
    street_address = data.get('street_address')
    city = data.get('city')
    state = data.get('state')
    postal_code = data.get('postal_code')

    # Find nursery entry by email (created during OTP)
    nursery = Nursery.query.filter_by(email=email).first()

    if not nursery:
        return jsonify({"message": "Nursery not found"}), 404

    if not nursery.otp or datetime.now() > nursery.otp_expiration:
        return jsonify({"message": "OTP verification is required"}), 400

    # Hash the password
    hashed_password = generate_password_hash(password)

    # Update nursery information
    nursery.first_name = first_name
    nursery.password_hash = hashed_password
    nursery.business_name = business_name
    nursery.phone_number = phone_number
    nursery.street_address = street_address
    nursery.city = city
    nursery.state = state
    nursery.postal_code = postal_code

    # Commit changes to the database
    db.session.commit()

    return jsonify({"message": "Nursery registered successfully", "role": "nursery"}), 200


# Route to fetch customer profile by email
@app.route('/customerProfile', methods=['POST'])
def get_customer_profile():
    data = request.get_json()
    email = data.get('email')
    
    customer = Customer.query.filter_by(email=email).first()
    if customer:
        return jsonify({
            "name": customer.name,
            "email": customer.email,
            "phone_number": customer.phone_number,
            "street_address": customer.street_address,
            "city": customer.city,
            "state": customer.state,
            "postal_code": customer.postal_code,
            "profile_pic": customer.profile_pic
        })
    else:
        return jsonify({"error": "Customer not found"}), 404

# Route to update customer profile
@app.route('/updateProfile', methods=['POST'])
def update_profile():
    data = request.json
    email = data.get('email')
    profile_pic_base64 = data.get('profile_pic')  # Get Base64 string

    # Find the customer by email
    customer = Customer.query.filter_by(email=email).first()

    if customer:
        # Update the customer profile details
        customer.name = data.get('name')
        customer.phone_number = data.get('phone_number')
        customer.street_address = data.get('street_address')
        customer.city = data.get('city')
        customer.state = data.get('state')
        customer.postal_code = data.get('postal_code')
        customer.profile_pic = profile_pic_base64  # Store Base64 image

        db.session.commit()

        return jsonify({
            "message": "Profile updated successfully",
            "profile_pic": customer.profile_pic
        }), 200
    else:
        return jsonify({"error": "Customer not found"}), 404

# Route to get a profile
@app.route('/n-get_profile', methods=['GET'])
def get_profile():
    email = request.args.get('email')
    profile = Nursery.query.filter_by(email=email).first()
    
    if profile:
        return jsonify({
            'nurseryName': profile.business_name,
            'contactEmail': profile.email,
            'contactNumber': profile.phone_number,
            'businessHours': profile.business_hours,
            'streetAddress': profile.street_address,
            'city': profile.city,
            'state': profile.state,
            'postalCode': profile.postal_code,
            'description': profile.description,
            'profileImage': profile.profile_pic,
            'nurseryImages': profile.nursery_images
        })
    else:
        return jsonify({'error': 'Profile not found'}), 404

# Route to update a profile
@app.route('/n-update_profile', methods=['PUT'])  # Changed to PUT for updating
def nupdate_profile():
    data = request.json
    print('Received data:', data)  # Log incoming data for debugging

    email = data.get('email')
    profile = Nursery.query.filter_by(email=email).first()

    if not profile:
        return jsonify({'error': 'Profile not found'}), 404

    # Update profile fields
    profile.business_name = data.get('nurseryName')
    profile.phone_number = data.get('contactNumber')
    profile.business_hours = data.get('businessHours')
    profile.description = data.get('description')
    profile.street_address = data.get('streetAddress')
    profile.city = data.get('city')
    profile.state = data.get('state')
    profile.postal_code = data.get('postalCode')

    # Update profile image if available
    if 'profileImage' in data:
        profile.profile_pic = data['profileImage']

    # Update additional nursery images if available
    if 'nurseryImages' in data:
        profile.nursery_images = data['nurseryImages']  # Assuming it's a serialized list

    print('Updated profile:', profile)  # Log the updated profile

    # Save changes to the database
    try:
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully!'})
    except Exception as e:
        print(f'Error updating profile: {e}')
        db.session.rollback()  # Rollback if any error occurs
        return jsonify({'error': 'Error updating profile'}), 500


def encode_image_to_base64(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

@app.route('/add_plant', methods=['POST'])
def add_plant():
    try:
        data = request.json  # Expecting JSON body
        plant_name = data.get('plantName')
        sub_name = data.get('subName')
        plant_type = data.get('plantType')
        quantity = data.get('quantity')
        description = data.get('description')
        price = data.get('price')
        plant_image_base64 = data.get('plantImage')  # Base64 encoded image

        if plant_image_base64:
            # Decode the base64 image data
            plant_image = base64.b64decode(plant_image_base64.split(',')[1])
        else:
            plant_image = None

        nursery_email = data.get('nursery_email')

        # Ensure required fields are provided
        if not all([plant_name, sub_name, plant_type, quantity, description, price, nursery_email]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Save the plant in the database
        new_plant = Plant(
            plant_name=plant_name,
            sub_name=sub_name,
            plant_type=plant_type,
            quantity=quantity,
            description=description,
            price=price,
            plant_image=plant_image_base64,  # Store Base64 image string or decoded data
            nursery_email=nursery_email
        )

        db.session.add(new_plant)
        db.session.commit()

        return jsonify({'message': 'Plant added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/plants/<nursery_email>', methods=['GET'])
def get_plants(nursery_email):
    # Retrieve nursery
    nursery = Nursery.query.filter_by(email=nursery_email).first()

    if not nursery:
        return jsonify({'error': 'Nursery not found'}), 404

    # Retrieve all plants for the nursery
    plants = Plant.query.filter_by(nursery_email=nursery.email).all()

    # Format data for response
    plant_list = [{
        'id': plant.id,
        'plant_name': plant.plant_name,
        'sub_name': plant.sub_name,
        'plant_type': plant.plant_type,
        'quantity': plant.quantity,
        'description': plant.description,
        'price': plant.price,
        'plant_image': plant.plant_image  # Base64 image
    } for plant in plants]

    return jsonify(plant_list), 200

@app.route('/update_plant/<int:plant_id>', methods=['PUT'])
def update_plant(plant_id):
    data = request.json

    # Retrieve the plant by ID
    plant = Plant.query.get(plant_id)

    if not plant:
        return jsonify({'error': 'Plant not found'}), 404

    # Update plant fields
    plant.plant_name = data.get('plant_name', plant.plant_name)
    plant.sub_name = data.get('sub_name', plant.sub_name)
    plant.plant_type = data.get('plant_type', plant.plant_type)
    plant.quantity = data.get('quantity', plant.quantity)
    plant.description = data.get('description', plant.description)
    plant.price = data.get('price', plant.price)
    plant.plant_image = data.get('plant_image', plant.plant_image)  # Base64 image

    db.session.commit()

    return jsonify({'message': 'Plant updated successfully'}), 200

@app.route('/delete_plant/<int:plant_id>', methods=['DELETE'])
def delete_plant(plant_id):
    # Retrieve the plant by ID
    plant = Plant.query.get(plant_id)

    if not plant:
        return jsonify({'error': 'Plant not found'}), 404

    # Delete the plant
    db.session.delete(plant)
    db.session.commit()

    return jsonify({'message': 'Plant deleted successfully'}), 200

@app.route('/showproduct', methods=['GET'])
def get_plantss():
    try:
        # Fetch all plants with nursery details
        plants = db.session.query(Plant, Nursery).join(Nursery, Plant.nursery_email == Nursery.email).all()

        plant_list = []
        for plant, nursery in plants:
            plant_data = {
                'id': plant.id,
                'plant_name': plant.plant_name,
                'sub_name': plant.sub_name,
                'plant_type': plant.plant_type,
                'quantity': plant.quantity,
                'description': plant.description,
                'price': plant.price,
                'plant_image': plant.plant_image,  # Base64 or URL
                'nursery_email': plant.nursery_email,
                'nursery_name': nursery.business_name  # Fetching from Nursery table
            }
            plant_list.append(plant_data)

        return jsonify(plant_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/complete-order', methods=['POST'])
def complete_order():
    try:
        order_data = request.json
        print("Received Order Data:", order_data)  # Debugging print statement

        # Validate the presence of necessary fields
        required_fields = ["customerName", "streetAddress", "city", "postalCode", "state", "cartItems", "paymentMethod", "status", "nurseryEmail", "customerEmail"]
        for field in required_fields:
            if field not in order_data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        cart_items = order_data.get('cartItems', [])
        
        if not cart_items:
            return jsonify({"error": "Cart items cannot be empty"}), 400

        # Process each item in the cart
        for item in cart_items:
            if 'plant_name' not in item or 'quantity' not in item or 'price' not in item:
                return jsonify({"error": "Missing product_name, quantity, or price in cartItems"}), 400

            new_order = Order(
                customer_name=order_data['customerName'],
                street_address=order_data['streetAddress'],
                city=order_data['city'],
                postal_code=order_data['postalCode'],
                state=order_data['state'],
                product_name=item['plant_name'],
                quantity=item['quantity'],
                price=item['price'],
                nursery_email=order_data['nurseryEmail'],
                customer_email=order_data['customerEmail']
            )

            db.session.add(new_order)

        db.session.commit()
        return jsonify({"message": "Order placed successfully"}), 201

    except Exception as e:
        print("Error:", str(e))  # Log the error
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

@app.route('/order-history/<customer_email>', methods=['GET'])
def order_history(customer_email):
    try:
        orders = Order.query.filter_by(customer_email=customer_email).all()
        if not orders:
            return jsonify({"message": "No orders found"}), 404

        order_list = [{
            "id": order.id,
            "customer_name": order.customer_name,
            "street_address": order.street_address,
            "city": order.city,
            "postal_code": order.postal_code,
            "state": order.state,
            "product_name": order.product_name,
            "quantity": order.quantity,
            "price": order.price,
            "total_price": order.total_price,
            "nursery_email": order.nursery_email,
            "order_date": order.order_date.strftime('%Y-%m-%d %H:%M:%S'),
        } for order in orders]

        return jsonify(order_list), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


@app.route('/nursery-stats', methods=['GET'])
def nursery_stats():
    nursery_email = request.args.get('nursery_email')

    if not nursery_email:
        return jsonify({'error': 'Nursery email is required'}), 400

    today = datetime.utcnow().date()
    
    total_plants = Plant.query.filter_by(nursery_email=nursery_email).count()
    total_orders = Order.query.filter_by(nursery_email=nursery_email).filter(db.func.date(Order.order_date) == today).count()
    orders = Order.query.filter_by(nursery_email=nursery_email).filter(db.func.date(Order.order_date) == today).all()

    order_list = [
        {
            'customer_name': order.customer_name,
            'product_name': order.product_name,
            'quantity': order.quantity,
            'street_address': order.street_address,
            'city': order.city,
            'postal_code': order.postal_code,
            'state': order.state,
            'order_date': order.order_date.strftime('%Y-%m-%d')
        }
        for order in orders
    ]

    return jsonify({
        'totalPlants': total_plants,
        'totalOrders': total_orders,
        'orders': order_list
    })

@app.route('/nursery-orders', methods=['GET'])
def get_nursery_orders():
    try:
        nursery_email = request.args.get('nursery_email')

        if not nursery_email:
            return jsonify({"error": "Nursery email is required"}), 400

        # Fetch orders for the given nursery email
        orders = Order.query.filter_by(nursery_email=nursery_email).all()

        order_list = []
        for order in orders:
            order_list.append({
                "order_no": order.id,
                "customer_name": order.customer_name,
                "product_name": order.product_name,
                "quantity": order.quantity,
                "price": order.price,  # Add price field
                "street_address": order.street_address,
                "city": order.city,
                "postal_code": order.postal_code,
                "state": order.state,
                "order_date": order.order_date.strftime("%Y-%m-%d %H:%M:%S")  # Format the date
            })

        return jsonify(order_list)

    except Exception as e:
        print("Error fetching orders:", str(e))
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

@app.route('/showproducts', methods=['GET'])
def show_plantss():
    try:
        search_query = request.args.get('search', '').lower()
        plants = Plant.query.all()
        
        if search_query:
            plants = [plant for plant in plants if search_query in plant.plant_name.lower()]
        
        plant_list = [{
            'id': plant.id,
            'plant_name': plant.plant_name,
            'sub_name': plant.sub_name,
            'plant_type': plant.plant_type,
            'quantity': plant.quantity,
            'description': plant.description,
            'price': plant.price,
            'plant_image': plant.plant_image,
            'nursery_email': plant.nursery_email,
            'nursery_name': Nursery.query.filter_by(email=plant.nursery_email).first().business_name if Nursery.query.filter_by(email=plant.nursery_email).first() else "Unknown"
        } for plant in plants]

        return jsonify(plant_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/getcontact', methods=['POST'])
def get_contact():
    data = request.json
    new_contact = Contact(
        name=data['name'],
        email=data['email'],
        subject=data['subject'],
        message=data['message']
    )
    db.session.add(new_contact)
    db.session.commit()
    return jsonify({"message": "Your message has been received."}), 201

@app.route('/showcontact', methods=['GET'])
def show_contact():
    messages = Contact.query.all()
    return jsonify([
        {"id": msg.id, "name": msg.name, "email": msg.email, "subject": msg.subject, "message": msg.message}
        for msg in messages
    ])

# Fetch all customers
@app.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return jsonify([{ 'id': c.id, 'name': c.name, 'email': c.email } for c in customers])

# Update customer
@app.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    data = request.json
    customer = Customer.query.get(id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    customer.name = data.get('name', customer.name)
    customer.email = data.get('email', customer.email)
    db.session.commit()
    return jsonify({'message': 'Customer updated successfully'})

# Delete customer
@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get(id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message': 'Customer deleted successfully'})

# Fetch all nurseries
@app.route('/nurseries', methods=['GET'])
def get_nurseries():
    nurseries = Nursery.query.all()
    return jsonify([{ 'id': n.id, 'name': n.business_name,'email': n.email } for n in nurseries])

# Update nursery
@app.route('/nurseries/<int:id>', methods=['PUT'])
def update_nursery(id):
    data = request.json
    nursery = Nursery.query.get(id)
    if not nursery:
        return jsonify({'error': 'Nursery not found'}), 404
    nursery.business_name = data.get('name', nursery.business_name)
    nursery.email = data.get('name', nursery.email)
    db.session.commit()
    return jsonify({'message': 'Nursery updated successfully'})

# Delete nursery
@app.route('/nurseries/<int:id>', methods=['DELETE'])
def delete_nursery(id):
    nursery = Nursery.query.get(id)
    if not nursery:
        return jsonify({'error': 'Nursery not found'}), 404
    db.session.delete(nursery)
    db.session.commit()
    return jsonify({'message': 'Nursery deleted successfully'})

@app.route('/get-user', methods=['GET'])
def get_user():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Check both customer and nursery tables
    user = Customer.query.filter_by(email=email).first() or Nursery.query.filter_by(email=email).first()

    if user:
        return jsonify({
            "name": user.name if hasattr(user, 'name') else user.first_name,
            "profile_pic": user.profile_pic
        })
    return jsonify({"error": "User not found"}), 404

@app.route('/nurseries/email/<string:email>', methods=['GET'])
def get_nursery_by_email(email):
    email = email.strip()  # Remove spaces
    nursery = Nursery.query.filter(func.lower(Nursery.email) == email.lower()).first()

    if nursery:
        return jsonify({
            'id': nursery.id,
            'business_name': nursery.business_name,
            'email': nursery.email,
            'phone_number': nursery.phone_number,
            'street_address': nursery.street_address,
            'city': nursery.city,
            'state': nursery.state,
            'postal_code': nursery.postal_code,
            'profile_pic': nursery.profile_pic,
            'nursery_images': nursery.nursery_images,
            'business_hours': nursery.business_hours,
            'description': nursery.description
        })
    
    return jsonify({'error': 'Nursery not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
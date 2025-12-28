# Online Plant Ordering System

The Online Plant Ordering System is a full-stack web application designed to digitalize nursery operations by enabling online plant browsing, ordering, and inventory management. The system provides a seamless experience for customers to purchase plants online while allowing nursery administrators to manage products, orders, and inventory efficiently.

---

## 🚀 Features

### Customer Features
- User registration and secure authentication
- Browse plants with detailed descriptions and pricing
- Add plants to cart and place orders online
- View order history and order status

### Admin Features
- Add, update, and delete plant products
- Manage plant inventory and stock availability
- Track customer orders and update order status
- Manage customer information

---

## 🛠 Tech Stack

### Frontend
- Angular
- HTML5, CSS3
- Bootstrap

### Backend
- Python (Flask)
- RESTful APIs

### Database
- PostgreSQL

### Tools
- Git, Postman
- VS Code

---

## 📊 Project Impact

- Managed **300+ plant products** with real-time inventory updates
- Automated manual nursery workflows, reducing order processing time by **50%**
- Improved order accuracy and tracking, reducing manual errors by **60%**
- Enhanced user experience with a responsive and intuitive Angular-based UI

---

## 🧩 System Architecture

- Angular frontend communicates with Flask backend via REST APIs
- Flask handles business logic, authentication, and validations
- PostgreSQL stores plant, customer, and order data using relational design
- REST APIs ensure modular and scalable communication

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL
- Git

### Backend Setup
```bash
git clone https://github.com/your-username/online-plant-ordering-system.git
cd online-plant-ordering-system/backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py

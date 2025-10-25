# Care Coffee
Care Coffee is a Django-based e-commerce web application that allows users to browse coffee products, manage their shopping cart, and place orders with integrated Chapa payment gateway support. The project focuses on a clean and functional design for a small online coffee business.

## Features
- Product listing and details page (shop)
- Shopping cart management (add, update, delete items)
- Order creation and checkout process
- Online payment integration using Chapa API
- User registration and login (via built-in authentication)
- User profile management (including profile photo upload)
- Docker support for containerized deployment
- Admin dashboard for managing products, orders, and users

## Project Structure
care_coffee/
│
├── care_coffee/ # Project settings and URLs
├── cart/ # Cart app (add, update, remove items)
├── order/ # Order creation, callback, and payment logic
├── shop/ # Product listing and details
├── templates/ # Global and app-specific HTML templates
├── useraccount/ # User registration, login, and profile management
│
├── manage.py
├── db.sqlite3
├── requirements.txt
├── Dockerfile
├── .gitignore
└── README.md


#1. Clone the repository:
git clone https://github.com/SelamZem/Care_Coffee.git
cd care_coffee
#2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
#3. Install dependencies
pip install -r requirements.txt
#4. Apply Migrations
python manage.py migrate
#5. Create Admin
python manage.py createsuperuser
#6. Create the Development Server
python manage.py runserver




### still in progress

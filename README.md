# Amazon Clone with Django

## Description

This is a simple Amazon clone project built using Django. The project aims to replicate some basic functionalities of the Amazon website, allowing users to browse products, add them to their cart, and proceed to checkout.

## Features

- **Product Listing**: Browse through a list of products with details such as name, price, and description.
- **Product Details**: Click on a product to view more details and add it to the cart.
- **Shopping Cart**: Add products to the shopping cart and view the total before proceeding to checkout.
- **User Authentication**: Register, log in, and log out to access personalized features like order history.
- **Order Placement**: Complete the shopping experience by placing an order.

## Technologies Used

- **Django**: Web framework for building the application.
- **PostgreSQL**: Database for storing product and user information.
- **HTML/CSS**: Frontend design and styling.
- **Bootstrap**: Frontend framework for responsive design.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/MohammadrezaAmani/Django-Amazon-Clone.git
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:

   - On Windows:

     ```bash
     venv\Scripts\activate
     ```

   - On macOS and Linux:

     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Run migrations:

   ```bash
   python manage.py migrate
   ```

6. Create a superuser:

   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:

   ```bash
   python manage.py runserver
   ```

8. Access the application at `http://localhost:8000` in your web browser.

## Usage

1. Create an account or log in using the superuser account.
2. Browse through products and add them to the cart.
3. Proceed to checkout and place an order.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

This project is licensed under the [MIT License](LICENSE).

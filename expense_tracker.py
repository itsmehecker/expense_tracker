import mysql.connector
from datetime import datetime
import hashlib

# Initialize the database
def init_db():
    db = mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username
        password="mysql"  # Replace with your MySQL password
    )
    cursor = db.cursor()

    # Check and create the database if it doesn't exist
    cursor.execute("SHOW DATABASES")
    databases = [db[0] for db in cursor.fetchall()]
    if 'expense_tracker' not in databases:
        cursor.execute("CREATE DATABASE expense_tracker")
        print("Database created.")
    db.database = 'expense_tracker'

    # Create required tables if they don't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE,
            password VARCHAR(255)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            category_name VARCHAR(50),
            type ENUM('income', 'expense'),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            category_id INT,
            amount DECIMAL(10, 2),
            transaction_date DATE,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
    """)
    print("Database and tables are ready.")
    cursor.close()
    return db

# Hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# User registration
def register_user(cursor, db):
    username = input("Enter username: ")
    password = input("Enter password: ")
    hashed_password = hash_password(password)
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        db.commit()
        print("User registered successfully.")
    except mysql.connector.errors.IntegrityError:
        print("Username already exists. Please try another one.")

# User login
def login_user(cursor):
    username = input("Enter username: ")
    password = input("Enter password: ")
    hashed_password = hash_password(password)
    cursor.execute("SELECT user_id FROM users WHERE username = %s AND password = %s", (username, hashed_password))
    user = cursor.fetchone()
    if user:
        print("Login successful.")
        return user[0]
    else:
        print("Invalid username or password.")
        return None

# Add a category
def add_category(cursor, db, user_id):
    category_name = input("Enter category name: ")
    category_type = input("Enter category type (income/expense): ").lower()
    cursor.execute("INSERT INTO categories (user_id, category_name, type) VALUES (%s, %s, %s)", 
                   (user_id, category_name, category_type))
    db.commit()
    print("Category added successfully.")

# Update a category
def update_category(cursor, db, user_id):
    cursor.execute("SELECT category_id, category_name FROM categories WHERE user_id = %s", (user_id,))
    categories = cursor.fetchall()
    print("Available Categories:")
    for category in categories:
        print(f"ID: {category[0]}, Name: {category[1]}")
    category_id = input("Enter category ID to update: ")
    new_category_name = input("Enter new category name: ")
    new_category_type = input("Enter new category type (income/expense): ").lower()
    cursor.execute("UPDATE categories SET category_name = %s, type = %s WHERE category_id = %s AND user_id = %s", 
                   (new_category_name, new_category_type, category_id, user_id))
    db.commit()
    print("Category updated successfully.")

# Delete a category
def delete_category(cursor, db, user_id):
    cursor.execute("SELECT category_id, category_name FROM categories WHERE user_id = %s", (user_id,))
    categories = cursor.fetchall()
    print("Available Categories:")
    for category in categories:
        print(f"ID: {category[0]}, Name: {category[1]}")
    category_id = int(input("Enter category ID to delete: "))
    
    # Delete related transactions first
    cursor.execute("DELETE FROM transactions WHERE category_id = %s AND user_id = %s", (category_id, user_id))
    
    # Then delete the category
    cursor.execute("DELETE FROM categories WHERE category_id = %s AND user_id = %s", (category_id, user_id))
    db.commit()
    print("Category and related transactions deleted successfully.")

# Log a transaction
def log_transaction(cursor, db, user_id):
    cursor.execute("SELECT category_id, category_name FROM categories WHERE user_id = %s", (user_id,))
    categories = cursor.fetchall()
    print("Available Categories:")
    for category in categories:
        print(f"ID: {category[0]}, Name: {category[1]}")
    category_id = int(input("Enter category ID: "))
    amount = float(input("Enter amount: "))
    transaction_date = input("Enter transaction date (YYYY-MM-DD): ")
    cursor.execute("INSERT INTO transactions (user_id, category_id, amount, transaction_date) VALUES (%s, %s, %s, %s)", 
                   (user_id, category_id, amount, transaction_date))
    db.commit()
    print("Transaction logged successfully.")

# View summary
def view_summary(cursor, user_id):
    cursor.execute("""
        SELECT c.type, SUM(t.amount) 
        FROM transactions t 
        JOIN categories c ON t.category_id = c.category_id 
        WHERE t.user_id = %s 
        GROUP BY c.type
    """, (user_id,))
    summary = cursor.fetchall()
    total_income = total_expense = 0
    for entry in summary:
        if entry[0] == 'income':
            total_income = entry[1]
        else:
            total_expense = entry[1]
    print(f"Total Income: ${total_income:.2f}")
    print(f"Total Expense: ${total_expense:.2f}")
    print(f"Remaining Budget: ${total_income - total_expense:.2f}")

    cursor.execute("""
        SELECT c.category_name, SUM(t.amount) AS total_spent 
        FROM transactions t 
        JOIN categories c ON t.category_id = c.category_id 
        WHERE t.user_id = %s AND c.type = 'expense' 
        GROUP BY c.category_name 
        ORDER BY total_spent DESC 
        LIMIT 1
    """, (user_id,))
    highest_spending = cursor.fetchone()
    if highest_spending:
        print(f"Highest Spending Category: {highest_spending[0]} (${highest_spending[1]:.2f})")
    else:
        print("No expenses recorded yet.")

# Change user password
def change_password(cursor, db, user_id):
    current_password = input("Enter current password: ")
    hashed_current_password = hash_password(current_password)
    cursor.execute("SELECT user_id FROM users WHERE user_id = %s AND password = %s", (user_id, hashed_current_password))
    user = cursor.fetchone()
    if user:
        new_password = input("Enter new password: ")
        hashed_new_password = hash_password(new_password)
        cursor.execute("UPDATE users SET password = %s WHERE user_id = %s", (hashed_new_password, user_id))
        db.commit()
        print("Password changed successfully.")
    else:
        print("Current password is incorrect.")

# Main function
def main():
    db = init_db()
    cursor = db.cursor()
    while True:
        print("\n1. Register\n2. Login\n3. Exit")
        choice = input("Choose an option: ")
        if choice == '1':
            register_user(cursor, db)
        elif choice == '2':
            user_id = login_user(cursor)
            if user_id:
                while True:
                    print("\n1. Add Category\n2. Log Transaction\n3. View Summary\n4. Change Password\n5. Update Category(&related transactions)\n6. Delete Category\n7. Logout")
                    user_choice = input("Choose an option: ")
                    if user_choice == '1':
                        add_category(cursor, db, user_id)
                    elif user_choice == '2':
                        log_transaction(cursor, db, user_id)
                    elif user_choice == '3':
                        view_summary(cursor, user_id)
                    elif user_choice == '4':
                        change_password(cursor, db, user_id)
                    elif user_choice == '5':
                        update_category(cursor, db, user_id)
                    elif user_choice == '6':
                        delete_category(cursor, db, user_id)
                    elif user_choice == '7':
                        print("Logged out.")
                        break
                    else:
                        print("Invalid option. Try again.")
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()

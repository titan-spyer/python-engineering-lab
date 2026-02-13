import random
import string
import datetime

# Storage for user data and library books
bank_users_db = {}
library_users_db = {}
library_books_db = {}

# Bank Account system Starts from here.
class open_bank:
    def __init__(self, name, age, Dob, number, address, balance=0, password=None):
        self.name = name
        self.age = age
        self.dob = Dob
        self.number = number
        self.address = address
        self.user_id = self.gen_user_id(self.name) if password is None else None # ID handled by DB on login
        self._password = password if password else self.password_validator()
        self.balance = balance
        self.transactions = []
        self.created_at = datetime.datetime.now()
        self.logs = []
        
        # Store user data in the dictionary
        bank_users_db[self.user_id] = {
            "name": self.name,
            "age": self.age,
            "dob": self.dob,
            "number": self.number,
            "address": self.address,
            "password": self._password,
            "balance": self.balance
        }

    # Show the user details.
    def show_user(self):    
        print(f"USER NAME: {self.name} | Age: {self.age} | DOB: {self.dob} | Number: {self.number} | Adress: {self.address}.")
        print(f"User ID: {self.user_id} | Password: {self._password}")
    
    # Show the balance of the user.
    def show_balance(self):
        self.logs.append(f"Balance checked at {datetime.datetime.now()}")
        print(f"Name: {self.name}")
        print(f"Current Balance: {self.balance}")
    
    # Show the transaction history of the user.
    def show_transactions(self):
        print(f"Transaction history for {self.name}:")
        for transaction in self.transactions:
            print(transaction)
    
    # Show the logs of the user.
    def show_logs(self):
        print(f"Logs for {self.name}:")
        for log in self.logs:
            print(log)
    
    # Deposite Funds to the account.
    def deposite(self, amount: float):
        print("To deposite you need to Enter the user id and Password.")
        if not self.user_validator():
            print("User validation failed. Cannot proceed with deposit.")
            self.logs.append(f"FAILED DEPOSIT: Validation failed at {datetime.datetime.now()}")
            return
        self.balance += amount
        self.transactions.append(f"Deposited {amount} at {datetime.datetime.now()}")
        self.logs.append(f"Deposited {amount} at {datetime.datetime.now()}")
        self.show_balance()
    
    # Withdraw Funds from the account.
    def withdrawl(self, amount: float):
        print("To withdraw you need to Enter the user id and Password.")
        if not self.user_validator():
            print("User validation failed. Cannot proceed with withdrawal.")
            self.logs.append(f"FAILED WITHDRAWAL: Validation failed at {datetime.datetime.now()}")
            return
        if amount > self.balance:
            print("Insufficient balance.")
            self.logs.append(f"FAILED WITHDRAWAL: Insufficient funds at {datetime.datetime.now()}")
            return
        self.balance -= amount
        self.transactions.append(f"Withdrew {amount} at {datetime.datetime.now()}")
        self.logs.append(f"Withdrew {amount} at {datetime.datetime.now()}")
        self.show_balance()

    # Transfer Funds to another user.
    def transfer(self, recipient_user_id: str, amount: float):
        print("To transfer you need to Enter the user id and Password.")
        if not self.user_validator():
            print("User validation failed. Cannot proceed with transfer.")
            self.logs.append(f"FAILED TRANSFER: Validation failed at {datetime.datetime.now()}")
            return
        if recipient_user_id not in bank_users_db:
            print("Recipient user ID does not exist.")
            self.logs.append(f"FAILED TRANSFER: Recipient {recipient_user_id} not found at {datetime.datetime.now()}")
            return
        if amount > self.balance:
            print("Insufficient balance.")
            self.logs.append(f"FAILED TRANSFER: Insufficient funds at {datetime.datetime.now()}")
            return
        
        recipient_data = bank_users_db[recipient_user_id]
        recipient_data['balance'] += amount
        self.balance -= amount
        
        self.transactions.append(f"Transferred {amount} to {recipient_user_id} at {datetime.datetime.now()}")
        self.logs.append(f"Transferred {amount} to {recipient_user_id} at {datetime.datetime.now()}")
        
        print(f"Successfully transferred {amount} to {recipient_user_id}.")
        self.show_balance()
    
    # validate the user id and password.
    def user_validator(self):
        print("Validate the user.")
        name = input("Enter the name: ")
        number = input("Enter mobile Number: ")
        user_id = input("Enter user id: ")
        if name == self.name and number == self.number and user_id == self.user_id:
            print("User validated successfully.")
            password = input("Enter the password: ")
            if password == self._password:
                print("Password validated successfully.")
                return True
            else:
                print("Invalid password.")
                return False
        else:
            print("Invalid user.")
            return False

    # Gen a random user id based on the name and a random suffix.
    @staticmethod
    def gen_user_id(name: str, suffix_length=4) -> str:

        clean_name = "".join(name.split()).lower()

        chars = string.ascii_letters + string.digits
        random_suffix = ''.join(random.choice(chars) for _ in range(suffix_length))

        return f"{clean_name}_{random_suffix}"
    
    # Validate the password.
    def password_validator(self):
        def validate_password( password: str):
            if len(password) < 8:
                return "Password must be at least 8 characters long."
            if not any(char.isupper() for char in password):
                return "Password must contain at least one uppercase letter."
            if not any(char.islower() for char in password):
                return "Password must contain at least one lowercase letter."
            if not any(char.isdigit() for char in password):
                return "Password must contain at least one digit."
            return True
        print("Welcome to the password validator...")
        while True:
            print("Enter a password: ")
            password = input()
            result = validate_password(password)
            if result is True:
                return password
            else:
                print(result)

# Library System starts from here.
class Library:
    def __init__(self, name, location, number):
        self.name = name
        self.location = location
        self.number = number
        self.user_id = self.gen_user_id(self.name)
        self.books = []
        self.created_at = datetime.datetime.now()
        self.logs = []
        
        # Store user data in the dictionary
        library_users_db[self.user_id] = {
            "name": self.name,
            "location": self.location,
            "number": self.number,
            "created_at": self.created_at,
            "logs": self.logs
        }

    # User can add books to the library.
    def add_book(self, book):
        if book in library_books_db:
            library_books_db[book] += 1
            self.logs.append(f"Added another copy of '{book}' at {datetime.datetime.now()}")
        else:
            self.logs.append(f"Added '{book}' to the library at {datetime.datetime.now()}")
            library_books_db[book] = 1

    # User can remove books from the library.
    def show_books(self):
        print("Books in the library:")
        for book, count in library_books_db.items():
            print(f"{book}: {count}")

    # Show the user details.
    def show_user(self):
        print(f"Library Name: {self.name} | Location: {self.location} | Number: {self.number}.")
        print(f"User ID: {self.user_id}")
        print(f"Books Borrowed: {', '.join(self.books) if self.books else 'None'}")
        print(f"Created At: {self.created_at}")
        print(f"Logs: {', '.join(self.logs) if self.logs else 'None'}")
    
    
    # User can borrow books from the library.
    def borrow_book(self, book):
        print("To borrow a book you need to Enter the user id...")
        if not self.user_validator():
            print("User validation failed. Cannot proceed with borrowing.")
            self.logs.append(f"FAILED BORROW: Validation failed at {datetime.datetime.now()}")
            return
        if book in library_books_db and library_books_db[book] > 0:
            library_books_db[book] -= 1
            self.logs.append(f"Borrowed '{book}' at {datetime.datetime.now()}")
            self.books.append(book)
            print(f"You have borrowed '{book}'.")
        else:
            print(f"'{book}' is not available in the library.")
            self.logs.append(f"FAILED BORROW: '{book}' unavailable at {datetime.datetime.now()}")

    # Validate the user.
    def user_validator(self):
        print("Validate the user...")
        name = input("Enter the name: ")
        number = input("Enter mobile Number: ")
        user_id = input("Enter user id: ")
        if name == self.name and number == self.number and user_id == self.user_id:
            print("User validated successfully.")
            return True
        else:
            print("Invalid user.")
            return False

    # Gen a random user id based on the name and a random suffix.
    @staticmethod
    def gen_user_id(name: str, suffix_length=4) -> str:
        clean_name = "".join(name.split()).lower()
        chars = string.ascii_letters + string.digits
        random_suffix = ''.join(random.choice(chars) for _ in range(suffix_length))
        return f"{clean_name}_{random_suffix}"

# The bank account functionality and the library system are implemented in the above classes. Below are the functions to interact with these systems.
# Here  is the main function to interact with the bank.
def titan_bank():
    # To handle the bank transactions after login or account creation.
    def bank_transtion(account):
        while True:
            print("\n--- Bank Menu ---")
            print("1. Show Balance")
            print("2. Show Transactions")
            print("3. Show Logs")
            print("4. Deposit")
            print("5. Withdrawl")
            print("6. Transfer")
            print("7. Exit")
            action = input("Enter your choice: ")
            if action == '1':
                account.show_balance()
            elif action == '2':
                account.show_transactions()
            elif action == '3':
                account.show_logs()
            elif action == '4':
                try:
                    amount = float(input("Enter the amount to deposit: "))
                    account.deposite(amount)
                except ValueError:
                    print("Invalid amount.")
            elif action == '5':
                try:
                    amount = float(input("Enter the amount to withdraw: "))
                    account.withdrawl(amount)
                except ValueError:
                    print("Invalid amount.")
            elif action == '6':
                recipient_user_id = input("Enter the recipient user ID: ")
                try:
                    amount = float(input("Enter the amount to transfer: "))
                    account.transfer(recipient_user_id, amount)
                except ValueError:
                    print("Invalid amount.")
            elif action == '7':
                return

    print("Welcome to Titan Bank!")
    print("1. Open a new account")
    print("2. Log in to an existing account")
    print("3. Exit")
    choice = input("Enter your choice: ")
    
    if choice == '1':
        name = input("Enter your name: ")
        try:
            age = int(input("Enter your age: "))
        except ValueError:
            print("Invalid age input. Please enter a number.")
            return
        dob = input("Enter your date of birth (YYYY-MM-DD): ")
        number = input("Enter your mobile number: ")
        address = input("Enter your address: ")
        
        new_account = open_bank(name, age, dob, number, address)
        new_account.show_user()
        bank_transtion(new_account)
    elif choice == '2':
        user_id = input("Enter your user id: ")
        if user_id in bank_users_db:
            user_data = bank_users_db[user_id]
            print("Login successful!")
            account = open_bank(user_data['name'], user_data['age'], user_data['dob'], 
                                user_data['number'], user_data['address'], 
                                balance=user_data['balance'], password=user_data['password'])
            account.user_id = user_id
            account.show_user()
            bank_transtion(account)
        else:
            print("Login failed. Invalid credentials.")


# Here is the main function to interact with the library.
def library_system():
    print("Welcome to the Library System!")
    print("1. Open a new library")
    print("2. Log in to an existing library")
    print("3. Exit")
    choice = input("Enter your choice: ")
    
    if choice == '1':
        name = input("Enter library name: ")
        location = input("Enter library location: ")
        number = input("Enter library contact number: ")
        new_library = Library(name, location, number)
        new_library.show_user()
    elif choice == '2':
        name = input("Enter library name: ")
        location = input("Enter library location: ")
        number = input("Enter library contact number: ")
        user_id = input("Enter library user id: ")
        if user_id in library_users_db and library_users_db[user_id]['name'] == name and library_users_db[user_id]['location'] == location and library_users_db[user_id]['number'] == number:
            print("Login successful!")
            library = Library(name, location, number)
            library.show_user()
        else:
            print("Login failed. Invalid credentials.")
    elif choice == '3':
        print("Thank you for visiting the Library System. Goodbye!")
    else:
        print("Invalid choice. Please try again.")
            
# Here is the main function to interact with both the bank and the library systems.
def main():
    while True:
        print("Choose a model to use:")
        print("1. Titan Bank")
        print("2. Library System")
        print("3. Exit")
        choice = input("Enter your choice: ")
        if choice == '1':
            titan_bank()
        elif choice == '2':
            library_system()
        elif choice == '3':
            print("Thank you for using the system. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
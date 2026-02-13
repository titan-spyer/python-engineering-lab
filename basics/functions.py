# The calculator model starts from here 
def add(a: float, b: float) -> float: return a + b
def subtract(a: float, b: float) -> float: return a - b
def multiply(a: float, b: float) -> float: return a * b
def divide(a: float, b: float) -> float | str:
    if b == 0:
        return "Error: Division by zero is not allowed."
    return a / b

def calculator():
    print("Welcome to calculator...")
    while True:
        print("Enter the first number: ")
        num1 = float(input())
        print("Enter the second number: ")
        num2 = float(input())
        print("Enter the operation (+, -, *, /): ")
        operation = input()
        
        if operation == '+':
            print(f"The result is: {add(num1, num2)}")
        elif operation == '-':
            print(f"The result is: {subtract(num1, num2)}")
        elif operation == '*':
            print(f"The result is: {multiply(num1, num2)}")
        elif operation == '/':
            print(f"The result is: {divide(num1, num2)}")
        else:
            print("Invalid operation. Please try again.")
        
        print("Do you want to perform another calculation? (yes/no)")
        continue_calculation = input().lower()
        if continue_calculation != 'yes':
            break


# A text Processor model starts from here
def get_uppercase(text: str) -> str: return text.upper()
def get_lowercase(text: str) -> str: return text.lower()
def get_char_count(text: str) -> int: return len(text)
def get_reversed(text: str) -> str: return text[::-1]

def text_processor():
    print("Welcome to the text processor...")
    while True:
        print("Enter a string: ")
        text = input()
        
        print("Choose an operation:")
        print("1. Convert to uppercase")
        print("2. Convert to lowercase")
        print("3. Count characters")
        print("4. Reverse the string")
        operation = input()
        
        if operation == '1':
            print(f"Uppercase: {get_uppercase(text)}")
        elif operation == '2':
            print(f"Lowercase: {get_lowercase(text)}")
        elif operation == '3':
            print(f"Character count: {get_char_count(text)}")
        elif operation == '4':
            print(f"Reversed string: {get_reversed(text)}")
        else:
            print("Invalid operation. Please try again.")
        
        print("Do you want to process another string? (yes/no)")
        continue_processing = input().lower()
        if continue_processing != 'yes':
            break

# A simple Password validator model starts from here
def validate_password(password: str) -> str:
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not any(char.isupper() for char in password):
        return "Password must contain at least one uppercase letter."
    if not any(char.islower() for char in password):
        return "Password must contain at least one lowercase letter."
    if not any(char.isdigit() for char in password):
        return "Password must contain at least one digit."
    return "Password is valid."

def password_validator():
    print("Welcome to the password validator...")
    while True:
        print("Enter a password: ")
        password = input()
        print(validate_password(password))
        
        print("Do you want to validate another password? (yes/no)")
        continue_validation = input().lower()
        if continue_validation != 'yes':
            break

# A simple Log praser model starts from here
def parse_log(log_entry: str) -> str:
    if "ERROR" in log_entry:
        return "This is an error log."
    elif "WARNING" in log_entry:
        return "This is a warning log."
    elif "INFO" in log_entry:
        return "This is an info log."
    else:
        return "Unknown log type."

def log_parser():
    print("Welcome to the log parser...")
    while True:
        print("Enter a log entry: ")
        log_entry = input()
        print(parse_log(log_entry))
        
        print("Do you want to parse another log entry? (yes/no)")
        continue_parsing = input().lower()
        if continue_parsing != 'yes':
            break


def main():
    while True:
        print("Choose a model to use:")
        print("1. Calculator")
        print("2. Text Processor")
        print("3. Password Validator")
        print("4. Log Parser")
        print("5. Exit")
        
        choice = input()
        
        if choice == '1':
            calculator()
        elif choice == '2':
            text_processor()
        elif choice == '3':
            password_validator()
        elif choice == '4':
            log_parser()
        elif choice == '5':
            print("Exiting the program. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
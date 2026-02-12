# The calculator model starts from here 
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
            result = num1 + num2
            print(f"The result of {num1} + {num2} is: {result}")
        elif operation == '-':
            result = num1 - num2
            print(f"The result of {num1} - {num2} is: {result}")
        elif operation == '*':
            result = num1 * num2
            print(f"The result of {num1} * {num2} is: {result}")
        elif operation == '/':
            if num2 != 0:
                result = num1 / num2
                print(f"The result of {num1} / {num2} is: {result}")
            else:
                print("Error: Division by zero is not allowed.")
        else:
            print("Invalid operation. Please try again.")
        
        print("Do you want to perform another calculation? (yes/no)")
        continue_calculation = input().lower()
        if continue_calculation != 'yes':
            break


# A text Processor model starts from here
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
            result = text.upper()
            print(f"Uppercase: {result}")
        elif operation == '2':
            result = text.lower()
            print(f"Lowercase: {result}")
        elif operation == '3':
            result = len(text)
            print(f"Character count: {result}")
        elif operation == '4':
            result = text[::-1]
            print(f"Reversed string: {result}")
        else:
            print("Invalid operation. Please try again.")
        
        print("Do you want to process another string? (yes/no)")
        continue_processing = input().lower()
        if continue_processing != 'yes':
            break

# A simple Password validator model starts from here
def password_validator():
    print("Welcome to the password validator...")
    while True:
        print("Enter a password: ")
        password = input()
        
        if len(password) < 8:
            print("Password must be at least 8 characters long.")
        elif not any(char.isupper() for char in password):
            print("Password must contain at least one uppercase letter.")
        elif not any(char.islower() for char in password):
            print("Password must contain at least one lowercase letter.")
        elif not any(char.isdigit() for char in password):
            print("Password must contain at least one digit.")
        else:
            print("Password is valid.")
        
        print("Do you want to validate another password? (yes/no)")
        continue_validation = input().lower()
        if continue_validation != 'yes':
            break

# A simple Log praser model starts from here
def log_parser():
    print("Welcome to the log parser...")
    while True:
        print("Enter a log entry: ")
        log_entry = input()
        
        if "ERROR" in log_entry:
            print("This is an error log.")
        elif "WARNING" in log_entry:
            print("This is a warning log.")
        elif "INFO" in log_entry:
            print("This is an info log.")
        else:
            print("Unknown log type.")
        
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
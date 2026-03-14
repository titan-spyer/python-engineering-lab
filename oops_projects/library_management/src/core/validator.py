import re
from typing import Optional, Tuple, Any, List
from datetime import datetime

from src.models.user import User, UserRole, UserStatus, BorrowingRecord
from src.models.book import Resource, FormatType

class Validator:
    def validate_email(self, email: str) -> Tuple[bool, str]:
        if not email or not isinstance(email, str):
            return False, "Invalid email format"
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            return True, "Valid email format"
        return False, "Invalid email format"
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        if not password or len(password) < 8:
            return False, "Password must be at least 8 characters long"
        has_upper = any(char.isupper() for char in password)
        has_lower = any(char.islower() for char in password)
        has_digit = any(char.isdigit() for char in password)
        has_special = any(not char.isalnum() for char in password)
        if not has_upper:
            return False, "Password must contain at least one uppercase letter"
        if not has_lower:
            return False, "Password must contain at least one lowercase letter"
        if not has_digit:
            return False, "Password must contain at least one digit"
        if not has_special:
            return False, "Password must contain at least one special character"
        return True, "Password meets strength requirements"
    def validate_username(self, username: str) -> Tuple[bool, str]:
        if not username:
            return False, "Username cannot be empty"
        if len(username) < 6:
            return False, "Username must be at least 6 characters long"
        if len(username) > 20:
            return False, "Username cannot exceed 20 characters"
        if not re.match(r'[A-Za-z][A-Za-z0-9_-]*$', username):
            return False, "Invalid username format"
        return True, "Valid username"
    def validate_phone(self, phone: str) -> Tuple[bool, str]:
        if not phone:
            return False, "Phone number cannot be empty"
        cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
        if not cleaned.isdigit():
            return False, "Invalid phone number format"
        if len(cleaned) == 10:
            return True, "Valid phone number (10 digits)"
        return False, "Invalid phone number format"


    def can_user_borrow(self, user: User, resource: Resource) -> Tuple[bool, str]:
        if user.status == UserStatus.BLACKLISTED.value:
            return False, "User is blacklisted"
        if user.status == UserStatus.PENDING_ACTIVATION.value:
            return False, "User is pending activation"
        if user.status == UserStatus.DEACTIVATED.value:
            return False, "User is deactivated"
        if user.status == UserStatus.SUSPENDED.value:
            return False, "User is suspended"
        if user.status == UserStatus.INACTIVE.value:
            return False, "User is inactive"
        if user.status != UserStatus.ACTIVE.value:
            return False, "User is not active status: " + UserStatus.get_name(user.status)
        limits = user.get_borrowing_limits()
        current_borrowings = len(user.current_borrowings)
        if current_borrowings >= limits['max_books']:
            return False, f"Maximum borrowing limit reached ({current_borrowings}/{limits['max_books']})"
        resource_category = getattr(resource, 'category', '')
        restricted_categories = limits.get('restricted_categories', [])
        if resource_category in restricted_categories:
            return False, f"Restricted category: {resource_category}"
        resource_type = resource.type
        if resource_type == 2:
            if not limits.get('journal_access', True):
                return False, "Restricted access to journals"
        if resource_type == 3:
            if not limits.get('research_paper_access', True):
                return False, "Restricted access to research papers"
        outstanding_fines = user.get_outstanding_fines()
        max_fines = limits.get('max_fines_allowed', 0)
        if outstanding_fines > max_fines:
            return False, f"Maximum outstanding fines reached ({outstanding_fines}/{max_fines})"
        if resource.copies <= 0:
            return False, f"No available copies of {resource.title}"
        return True, "Can borrow"

    def can_renew_record(self, user: User, record: BorrowingRecord) -> Tuple[bool, str]:
        if record.status != "active":
            return False, "Record is not active"
        if user.status != UserStatus.ACTIVE.value:
            return False, "User is not active"
        due_date = datetime.strptime(record.due_date, "%Y-%m-%d")
        if datetime.now() > due_date:
            return False, "Record is overdue"
        max_renewals = (user.get_borrowing_limits()).get('max_renewals', 1)
        if record.renewal_count >= max_renewals:
            return False, "Maximum renewals reached"
        return True, "Can renew"
    def can_return_book(self, user: User, copy_id: str) -> Tuple[bool, str, Optional[BorrowingRecord]]:
        active_record = None
        for record in user.current_borrowings:
            if record.copy_id == copy_id:
                active_record = record
                break
        if not active_record:
            return False, "No active borrowing record found", None
        return True, "Can return", active_record

    def is_book_available(self, resource: Resource, quantity: int = 1) -> Tuple[bool, str]:
        if not resource:
            return False, "Resource not Found"
        if resource.copies >= quantity:
            return True, f"{resource.copies} copies available"
        return False, f"Only {resource.copies} copies available, {quantity} required"

    def validate_resource_data(self, resource_data: dict) -> Tuple[bool, str]:
        required_fields = ['title', 'author', 'pages', 'publication_date']
        for field in required_fields:
            if field not in resource_data or not resource_data[field]:
                return False, f"Missing required field: {field}"
        if 'pages' in resource_data:
            try:
                pages = int(resource_data['pages'])
                if pages <= 0:
                    return False, "Invalid number of pages"
            except (ValueError, TypeError):
                return False, "Pages must be a number"
        if 'isbn' in resource_data and resource_data['isbn']:
            isbn = resource_data["isbn"].replace('-', '').replace(' ', '')
            if not (len(isbn) == 10 or len(isbn) == 13) or not isbn.isdigit():
                return False, "Invalid ISBN format"
        return True, "Valid resource data"
    def validate_copy_data(self, copy_data: dict) -> Tuple[bool, str]:
        required_fields = ['copy_id', 'resource_id', 'barcode']
        for field in required_fields:
            if field not in copy_data or not copy_data[field]:
                return False, f"Missing required field: {field}"
        if 'condition' in copy_data:
            if copy_data['condition'] not in [1, 2, 3, 4, 5]:
                return False, "Invalid condition value: " + str(copy_data['condition'])
        return True, "Valid copy data"


    def is_admin(self, user: User) -> bool:
        return user and user.role == UserRole.ADMIN.value

    def is_librarian(self, user: User) -> bool:
        return user and user.role == UserRole.LIBRARIAN.value
    def is_librarian_or_admin(self, user: User) -> bool:
        return user and user.role >= UserRole.LIBRARIAN.value
    def is_faculty(self, user: User) -> bool:
        return user and user.role == UserRole.FACULTY.value
    def is_student(self, user: User) -> bool:
        return user and user.role == UserRole.STUDENT.value
    def can_manage_user(self, user: User) -> bool:
        return self.is_librarian_or_admin(user)
    def can_waive_fines(self, user: User) -> bool:
        return self.is_librarian_or_admin(user)
    def can_override_policies(self, user: User) -> bool:
        return self.is_admin(user)
    def can_manage_system(self, user: User):
        return self.is_admin(user)


    def validate_issue_transaction(self, user: User, resource: Resource) -> Tuple[bool, str]:
        can_borrow, message = self.can_user_borrow(user, resource)
        if not can_borrow:
            return  False, message
        available, avail_message = self.is_book_available(resource)
        if not available:
            return False, avail_message
        return True, "Transaction is Valid"

    def validate_return_transaction(self, user: User, copy_id: str) -> Tuple[bool, str, Optional[BorrowingRecord]]:
        return self.can_return_book(user, copy_id)


    def validate_user_data(self, user_data: dict, is_new: bool = True) -> Tuple[bool, str]:
        if is_new:
            required_fields = ['username', 'email', 'full_name', 'password']
            for field in required_fields:
                if field not in user_data or not user_data[field]:
                    return False, f"missing required field: {field}"
        if 'username' in user_data and user_data['username']:
            valid, msg = self.validate_username(user_data["username"])
            if not valid:
                return False, msg
        if 'email' in user_data and user_data['email']:
            valid, msg = self.validate_email(user_data["email"])
            if not valid:
                return False, msg
        if is_new and 'password' in user_data:
            valid, msg = self.validate_password_strength(user_data['password'])
            if not valid:
                return False, msg
        if 'phone' in user_data and user_data['phone']:
            valid, msg = self.validate_phone(user_data["phone"])
            if not valid:
                return False, msg
        if 'role' in user_data:
            if user_data['role'] not in [1, 2, 3, 4]:
                return False, f"Invalid role: {user_data['role']}. must be 1-4"
        return True, "User Data is Valid"


    def validate_date_format(self, date_str: str, format: str = "%Y-%m-%d") -> Tuple[bool, str]:
        if not date_str:
            return False, "Date cannot be empty"
        try:
            datetime.strptime(date_str, format)
            return True, "Valid date format"
        except ValueError:
            return False, f"Invalid date format. Expected: {format}"
    def validate_due_date(self, due_date: str, borrow_date: Optional[str] = None) -> Tuple[bool, str]:
        valid, msg = self.validate_date_format(due_date)
        if not valid:
            return False, msg
        due = datetime.strptime(due_date, "%Y-%m-%d")
        if due < datetime.now():
            return False, "Due date cannot be in past"
        if borrow_date:
            valid, _ = self.validate_date_format(borrow_date)
            if valid:
                borrow = datetime.strptime(borrow_date, "%Y-%m-%d")
                if due < borrow:
                    return False, "Due date can not be before borrow Date"
        return True, "Due date is Valid"

    def validate_search_query(self, query: str, min_length: int = 2) -> Tuple[bool, str]:
        if not query or not query.strip():
            return False, "Search query cannot be empty"
        if len(query.strip()) < min_length:
            return False, f"Search query must be at least {min_length} characters"
        dangerous_chars = [';', '--', 'DROP', 'DELETE', 'UPDATE', 'INSERT']
        for char in dangerous_chars:
            if char in query.upper():
                return False, "Search query contains invalid characters"
        return True, "Search Query is valid"

    def validate_fine_amount(self, amount: float) -> Tuple[bool, str]:
        if amount < 0:
            return False, "Fine amount can not be negative"
        if amount > 5000:
            return False, "Fine amount limit is $5000.00"
        return True, "Fine amount is valid"
    def can_charge_fines(self, user: User, amount: float) -> Tuple[bool, str]:
        valid, msg = self.validate_fine_amount(amount)
        if not valid:
            return False, msg
        if user.status != UserStatus.ACTIVE.value:
            return False, "User is not active"
        current_fines = user.get_outstanding_fines()
        if current_fines + amount > 10000:
            return False, f"Adding this fine would exceedd limit"
        return True, "Fine can be charged"


    def validate_import_data(self, data: dict) -> Tuple[bool, List[str]]:
        errors = []
        if 'users' in data:
            for i, user in enumerate(data['users']):
                valid, _ = self.validate_user_data(user, is_new=False)
                if not valid:
                    errors.append(f"User {i}: {_}")
        if 'resources' in data:
            for i, resource in enumerate(data['resources']):
                valid, _ = self.validate_resource_data(resource)
                if not valid:
                    errors.append(f"Resource {i}: {_}")
        if 'copies' in data:
            for i, copy in enumerate(data['copies']):
                valid, _ = self.validate_copy_data(copy)
                if not valid:
                    errors.append(f"Copy {i}: {_}")
        return len(errors) == 0, errors
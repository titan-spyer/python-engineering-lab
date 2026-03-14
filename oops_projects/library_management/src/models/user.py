from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Set
import hashlib
import secrets
import re


# Enum for user types and status
class UserRole(Enum):
    STUDENT = 1
    FACULTY = 2
    LIBRARIAN = 3
    ADMIN = 4

    @classmethod
    def get_name(cls, value: int) -> str:
        for item in cls:
            if item.value == value:
                return item.name
        return "Unknown"

    @classmethod
    def get_permission_level(cls, value: int) -> int:
        permissions = {
            1: 10,  # Student
            2: 20,  # Teacher
            3: 80,  # Librarian
            4: 100  # Admin
        }
        return permissions.get(value, 0)


class UserStatus(Enum):
    ACTIVE = 1
    INACTIVE = 2
    SUSPENDED = 3
    BLACKLISTED = 4
    PENDING_ACTIVATION = 5
    DEACTIVATED = 6

    @classmethod
    def get_name(cls, value: int) -> str:
        for item in cls:
            if item.value == value:
                return item.name
        return "Unknown"


class AccountStatus(Enum):
    GOOD_STANDING = 1
    OVERDUE = 2
    FINE_PENDING = 3
    BORROWING_LIMIT_REACHED = 4
    RESTRICTED = 5


# Fine & Borrow limit configuration.
class BorrowLimits:
    LIMITS = {
        UserRole.STUDENT: {
            'max_books': 5,
            'max_days': 14,
            'max_renewals': 1,
            'max_fines_allowed': 50.0,
            'max_value_total': 1000.0,
            'restricted_categories': ['rare', 'reference'],
            'digital_access': True,
            'journal_access': True,
            'research_paper_access': True
        },
        UserRole.FACULTY: {
            'max_books': 10,
            'max_days': 30,
            'max_renewals': 3,
            'max_fines_allowed': 200.0,
            'max_value_total': 2000.0,
            'restricted_categories': ['rare'],
            'digital_access': True,
            'journal_access': True,
            'research_paper_access': True,
            'can_request_purchases': True
        },
        UserRole.LIBRARIAN: {
            'max_books': 15,
            'max_days': 45,
            'max_renewals': 5,
            'max_fines_allowed': 500.0,
            'max_value_total': 5000.0,
            'restricted_categories': [],
            'digital_access': True,
            'journal_access': True,
            'research_paper_access': True,
            'can_override_policies': False,
            'can_manage_users': True,
            'can_process_fines': True
        },
        UserRole.ADMIN: {
            'max_books': 20,
            'max_days': 60,
            'max_renewals': 10,
            'max_fines_allowed': float('inf'),
            'max_value_total': float('inf'),
            'restricted_categories': [],
            'digital_access': True,
            'journal_access': True,
            'research_paper_access': True,
            'can_manage_all_users': True,
            'can_override_policies': True,
            'can_manage_system': True,
            'can_override_fines': True,
            'can_process_fines': True
        }
    }


    @classmethod
    def get_limits(cls, role: UserRole) -> Dict[str, Any]:
        return cls.LIMITS.get(role, cls.LIMITS[UserRole.STUDENT])


# Borrowing Record class to track borrowings.
class BorrowingRecord:
    def __init__(
            self,
            user_id: str,
            record_id: str,
            resource_id: int,
            copy_id: str,
            borrow_date: str,
            due_date: str,
            return_date: Optional[str] = None,
            renewal_count: int = 0,
            fine_amount: float = 0.0,
            fine_paid: bool = False,
            status: str = "active"
    ):
        self.user_id = user_id
        self.record_id = record_id
        self.resource_id = resource_id
        self.copy_id = copy_id
        self.borrow_date = borrow_date
        self.due_date = due_date
        self.return_date = return_date
        self.renewal_count = renewal_count
        self.fine_amount = fine_amount
        self.fine_paid = fine_paid
        self.status = status
        self.renewal_history: List[str] = []
    
    def calculate_fines(self, daily_rate: float = 1.0) -> float:
        if self.return_date:
            return self.fine_amount
        
        due = datetime.strptime(self.due_date, "%Y-%m-%d")
        today = datetime.now()

        if today > due:
            overdue_days = (today - due).days
            self.fine_amount = overdue_days * daily_rate
        
        return self.fine_amount
    
    def renew(self) -> bool:
        if self.renewal_count < 3:
            self.renewal_count += 1
            new_due = datetime.strptime(self.due_date, "%Y-%m-%d") + timedelta(days=14)
            self.due_date = new_due.strftime("%Y-%m-%d")
            self.renewal_history.append(f"Renewed on {datetime.now().strftime('%Y-%m-%d')}")
            return True
        return False

    def return_item(self) -> float:
        self.return_date = datetime.now().strftime("%Y-%m-%d")
        self.status = "returned"
        self.calculate_fines()
        return self.fine_amount

    def to_dict(self) -> Dict[str, Any]:
        return {
            'record_id': self.record_id,
            'user_id': self.user_id,
            'resource_id': self.resource_id,
            'copy_id': self.copy_id,
            'borrow_date': self.borrow_date,
            'due_date': self.due_date,
            'return_date': self.return_date,
            'renewal_count': self.renewal_count,
            'fine_amount': self.fine_amount,
            'fine_paid': self.fine_paid,
            'status': self.status
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BorrowingRecord':
        return cls(**data)


#  Fine Record class to track fines.
class FineRecord:
    def __init__(
            self,
            fine_id: str,
            user_id: str,
            record_id: str,
            amount: float,
            reason: str,
            issued_date: str,
            due_date: str,
            paid_date: Optional[str] = None,
            waived_by: Optional[str] = None,
            status: str = "pending"
    ):
        self.fine_id = fine_id
        self.user_id = user_id
        self.record_id = record_id
        self.amount = amount
        self.reason = reason
        self.issued_date = issued_date
        self.due_date = due_date
        self.paid_date = paid_date
        self.waived_by = waived_by
        self.status = status

    def pay(self) -> bool:
        self.paid_date = datetime.now().strftime("%Y-%m-%d")
        self.status = "paid"
        return True

    def waive(self, admin_id: str) -> bool:
        self.waived_by = admin_id
        self.status = "waived"
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'fine_id': self.fine_id,
            'user_id': self.user_id,
            'record_id': self.record_id,
            'amount': self.amount,
            'reason': self.reason,
            'issued_date': self.issued_date,
            'due_date': self.due_date,
            'paid_date': self.paid_date,
            'waived_by': self.waived_by,
            'status': self.status
        }


# Notification class
class Notification:
    def __init__(
            self,
            notification_id: str,
            user_id: str,
            type: str,
            message: str,
            created_date: str,
            read: bool = False,
            priority: str = "normal"
    ):
        self.notification_id = notification_id
        self.user_id = user_id
        self.type = type
        self.message = message
        self.created_date = created_date
        self.read = read
        self.read_date: Optional[str] = None
        self.priority = priority

    def mark_as_read(self) -> None:
        self.read = True
        self.read_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict[str, Any]:
        return {
            'notification_id': self.notification_id,
            'user_id': self.user_id,
            'type': self.type,
            'message': self.message,
            'created_date': self.created_date,
            'read': self.read,
            'read_date': self.read_date,
            'priority': self.priority
        }


# Abstract User class
class User(ABC):
    def __init__(
            self,
            user_id: str,
            username: str,
            password_hash: str,
            email: str,
            full_name: str,
            role: int,
            status: int = UserStatus.PENDING_ACTIVATION.value,
            department: str = "",
            phone: str = "",
            address: str = "",
            registration_date: Optional[str] = None,
            last_login: Optional[str] = None,
            notes: str = ""
    ):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.full_name = full_name
        self.role = role
        self.status = status
        self.department = department
        self.phone = phone
        self.address = address
        self.registration_date = registration_date or datetime.now().strftime("%Y-%m-%d")
        self.last_login = last_login
        self.notes = notes
        self.notifications: List[Notification] = []
        self.current_borrowings: List[BorrowingRecord] = []
        self.borrowing_history: List[BorrowingRecord] = []
        self.fines: List[FineRecord] = []
        self.total_books_borrowed: int = 0
        self.total_fines_paid: float = 0.0
        self.times_blacklisted: int = 0
        self.activation_date: Optional[str] = None
        self.deactivation_date: Optional[str] = None
        self.deactivation_reason: str = ""

    @abstractmethod
    def get_role_name(self) -> str:
        pass

    @abstractmethod
    def get_borrowing_limits(self) -> Dict[str, Any]:
        pass

    def verify_password(self, password: str) -> bool:
        hash_obj = hashlib.sha256(password.encode())
        return hash_obj.hexdigest() == self.password_hash

    def update_last_login(self) -> None:
        self.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def can_borrow(self, resource_type: int, category: str="") -> tuple[bool, str]:
        if self.status != UserStatus.ACTIVE.value:
            return False, f"User status is {UserStatus.get_name(self.status)}, cannot borrow."
        limits = self.get_borrowing_limits()

        # Check BorrowLimits
        if len(self.current_borrowings) >= limits['max_books']:
            return False, f"Borrowing limit reached: {limits['max_books']} books."

        # Check Restrictions.
        if category in limits.get('restricted_categories', []):
            return False, f"Cannot borrow items from category: {category}."

        # Check fines.
        total_fines = sum(f.amount for f in self.fines if f.status == "pending")
        if total_fines > limits.get('max_fines_allowed', 50):
            return False, f"Outstanding fines exceed limit: ${limits['max_fines_allowed']}."

        # Check if blacklisted.
        if self.status == UserStatus.BLACKLISTED.value:
            return False, "User is blacklisted and cannot borrow."
        return True, "User can borrow."

    def add_borrowing(self, record: BorrowingRecord) -> bool:
        can_borrow, message = self.can_borrow(record.resource_id, "")
        if not can_borrow:
            print(f"Cannot add borrowing: {message}")
            return False
        self.current_borrowings.append(record)
        self.borrowing_history.append(record)
        self.total_books_borrowed += 1
        return True

    def return_item(self, copy_id: str) -> Optional[float]:
        for record in self.current_borrowings:
            if record.copy_id == copy_id:
                fine = record.return_item()
                self.current_borrowings.remove(record)

                if fine > 0:
                    fine_record = FineRecord(
                        fine_id=f"FINE-{self.user_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        user_id=self.user_id,
                        record_id=record.record_id,
                        amount=fine,
                        reason="overdue",
                        issued_date=datetime.now().strftime("%Y-%m-%d"),
                        due_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                    )
                    self.fines.append(fine_record)
                    self.add_notification(
                        "Fine Issued",
                        f"You have been issued a fine of ${fine:.2f} for overdue item: {record.copy_id}."
                        "high"
                    )
                return fine
        return None

    def add_fine(self, fine: FineRecord) -> None:
        self.fines.append(fine)

        total_fines = sum(f.amount for f in self.fines if f.status == "pending")
        limits = self.get_borrowing_limits()

        if total_fines > limits.get('max_fines_allowed', 50):
            self.add_notification(
                "Fine Limit Exceeded",
                f"Your total outstanding fines of ${total_fines:.2f} exceed the allowed limit of ${limits.get('max_fines_allowed', 50)}. "
                "Please pay your fines to continue borrowing.",
                "High"
            )

    def pay_fine(self, fine_id: str) -> bool:
        for fine in self.fines:
            if fine.fine_id == fine_id and fine.status == "pending":
                fine.pay()
                self.total_fines_paid += fine.amount
                return True
        return False

    def add_notification(self, type: str, message: str, priority: str = "normal") -> str:
        notification_id = f"NOTIFY-{self.user_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        notification = Notification(
            notification_id=notification_id,
            user_id=self.user_id,
            type=type,
            message=message,
            created_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            priority=priority
        )
        self.notifications.append(notification)
        return notification_id

    def get_unread_notifications(self) -> list[Notification]:
        return [n for n in self.notifications if not n.read]

    def get_outstanding_fines(self) -> float:
        return sum(f.amount for f in self.fines if f.status == "pending")

    def get_current_borrowings_count(self) -> int:
        return len(self.current_borrowings)

    def activate(self, activated_by: str) -> bool:
        if self.status == UserStatus.PENDING_ACTIVATION.value:
            self.status = UserStatus.ACTIVE.value
            self.activation_date = datetime.now().strftime("%Y-%m-%d")
            self.add_notification(
                "account",
                f"Your account has been activated by {activated_by}",
                "normal"
            )
            return True
        return False

    def deactivate(self, deactivate_by: str, reason: str = "") -> bool:
        if self.status != UserStatus.DEACTIVATED.value:
            self.status = UserStatus.DEACTIVATED.value
            self.deactivation_date = datetime.now().strftime("%Y-%m-%d")
            self.deactivation_reason = reason
            self.add_notification(
                "account",
                f"Your account has been deactivate for {reason} by {deactivate_by}",
                "high"
            )
            return True
        return False

    def blacklist(self, blacklisted_by: str, reason: str) -> bool:
        self.status = UserStatus.BLACKLISTED.value
        self.times_blacklisted += 1
        self.notes += f"\nBlacklisted  on {datetime.now().strftime("%Y-%m-%d")} by {blacklisted_by}: {reason}"
        self.add_notification(
            "warning",
            f"Your account has been blacklisted for {reason} by {blacklisted_by}. Please contact library staff for more information.",
            "urgent"
        )
        return True

    def remove_from_blacklist(self, removed_by: str) -> bool:
        if self.status == UserStatus.BLACKLISTED.value:
            self.status = UserStatus.ACTIVE.value
            self.notes += f"\nRemoved from blacklist on {datetime.now().strftime('%Y-%m-%d')} by {removed_by}"
            self.add_notification(
                "account",
                "your account has been restored to active status.",
                "high"
            )
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'password_hash': self.password_hash,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'status': self.status,
            'department': self.department,
            'phone': self.phone,
            'address': self.address,
            'registration_date': self.registration_date,
            'last_login': self.last_login,
            'total_books_borrowed': self.total_books_borrowed,
            'total_fines_paid': self.total_fines_paid,
            'times_blacklisted': self.times_blacklisted,
            'activation_date': self.activation_date,
            'deactivation_date': self.deactivation_date,
            'deactivation_reason': self.deactivation_reason,
            'notes': self.notes
        }

    @abstractmethod
    def __str__(self):
        pass


# class for students
class Student(User):
    def __init__(self, **kwargs):
        if 'department' not in kwargs:
            kwargs['department'] = 'Undergraduate'
        super().__init__(**kwargs)
        self.student_id = kwargs.get('student_id', self.user_id)
        self.year_of_study = kwargs.get('year_of_study', 1)
        self.major = kwargs.get('major', 'Undeclared')

    def get_role_name(self) -> str:
        return "Student"

    def get_borrowing_limits(self) -> Dict[str, Any]:
        return BorrowLimits.get_limits(UserRole.STUDENT)

    def can_borrow(self, resource_type: int, category: str="") -> tuple[bool, str]:
        can_borrow, message = super().can_borrow(resource_type, category)
        if not can_borrow:
            return can_borrow, message
        return True, "Approved"

    def __str__(self) -> str:
        status_text = UserStatus.get_name(self.status)
        return (
            f"\n{'='*60}\n"
            f"👨‍🎓 STUDENT: {self.full_name}\n"
            f"{'='*60}\n"
            f"ID: {self.user_id} | Student ID: {self.student_id}\n"
            f"Username: {self.username} | Email: {self.email}\n"
            f"Department: {self.department} | Major: {self.major}\n"
            f"Year: {self.year_of_study} | Status: {status_text}\n"
            f"Borrowed: {len(self.current_borrowings)}/{self.get_borrowing_limits()['max_books']}\n"
            f"Outstanding Fines: ${self.get_outstanding_fines():.2f}\n"
            f"Registered: {self.registration_date} | Last Login: {self.last_login or 'Never'}\n"
            f"{'='*60}"
        )


# Class for Faculty.
class Faculty(User):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.employee_id = kwargs.get('employee_id', self.user_id)
        self.designation = kwargs.get('designation', 'Professor')
        self.qualification = kwargs.get('qualification', '')
        self.courses_teaching: List[str] = kwargs.get('courses_teaching', [])
        self.can_request_purchase = True

    def get_role_name(self):
        return "Faculty"

    def get_borrowing_limits(self):
        return BorrowLimits.get_limits(UserRole.FACULTY)

    def request_purchase(self, book_title: str, author: str, isbn: str = "") -> str:
        request_id = f"REQ-{self.user_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.add_notification(
            "request",
            f"Purchase request submitted for '{book_title}' by {author}. Request ID: {request_id}",
            "normal"
        )
        return request_id

    def __str__(self):
        status_text = UserStatus.get_name(self.status)
        return (
            f"\n{'='*60}\n"
            f"👩‍🏫 FACULTY: {self.full_name}\n"
            f"{'='*60}\n"
            f"ID: {self.user_id} | Employee ID: {self.employee_id}\n"
            f"Username: {self.username} | Email: {self.email}\n"
            f"Department: {self.department} | Designation: {self.designation}\n"
            f"Qualification: {self.qualification} | Status: {status_text}\n"
            f"Borrowed: {len(self.current_borrowings)}/{self.get_borrowing_limits()['max_books']}\n"
            f"Outstanding Fines: ${self.get_outstanding_fines():.2f}\n"
            f"Courses Teaching: {', '.join(self.courses_teaching)}\n"
            f"Registered: {self.registration_date} | Last Login: {self.last_login or 'Never'}\n"
            f"{'='*60}"
        )

# Class for Librarian
class Librarian(User):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.employee_id = kwargs.get('employee_id', self.user_id)
        self.staff_id = kwargs.get('staff_id', '')
        self.section = kwargs.get('section', 'General')
        self.shift = kwargs.get('shift', 'Day')

    def get_role_name(self) -> str:
        return "Librarian"

    def get_borrowing_limits(self) -> Dict[str, Any]:
        return BorrowLimits.get_limits(UserRole.LIBRARIAN)

    def manage_user(self, user: User, action: str, **kwargs) -> bool:
        if user.role > UserRole.LIBRARIAN.value:
            print("Cannot manage users with admin users")
            return False

        if action == "activate":
            return user.activate(self.user_id)
        elif action == "deactivate":
            reason = kwargs.get('reason', 'No reason provided')
            return user.deactivate(self.user_id, reason)
        elif action == "add_note":
            user.notes += f"\n{kwargs.get('note', '')} (by {self.user_id})"
            return True

        return False

    def process_fine(self, fine: FineRecord, action: str) -> bool:
        if action == "mark_paid":
            return fine.pay()
        return False

    def __str__(self) -> str:
        status_text = UserStatus.get_name(self.status)
        return (
            f"\n{'='*60}\n"
            f"📚 LIBRARIAN: {self.full_name}\n"
            f"{'='*60}\n"
            f"ID: {self.user_id} | Staff ID: {self.staff_id}\n"
            f"Username: {self.username} | Email: {self.email}\n"
            f"Section: {self.section} | Shift: {self.shift}\n"
            f"Status: {status_text} | Department: {self.department}\n"
            f"Borrowed: {len(self.current_borrowings)}/{self.get_borrowing_limits()['max_books']}\n"
            f"Registered: {self.registration_date} | Last Login: {self.last_login or 'Never'}\n"
            f"{'='*60}"
        )

# Class for Admin
class Admin(User):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.admin_id = kwargs.get('admin_id', self.user_id)
        self.access_level = kwargs.get('access_level', 'Full')
        self.permissions: Set[str] = {
            'manage_users',
            'manage_books',
            'manage_fines',
            'override_policies',
            'system_config',
            'view_reports',
            'manage_librarians',
            'manage_admins'
        }

    def get_role_name(self) -> str:
        return "Administrator"

    def get_borrowing_limits(self) -> Dict[str, Any]:
        return BorrowLimits.get_limits(UserRole.ADMIN)

    def override_policy(self, policy_name: str, new_value: Any) -> bool:
        self.add_notification(
            "system",
            f"Policy '{policy_name}' has been overridden to '{new_value}' by {self.full_name}.",
            "high"
        )
        return True

    def waive_fine(self, fine: FineRecord) -> bool:
        fine.waive(self.user_id)
        return True

    def manage_librarian(self, librarian: Librarian, action: str) -> bool:
        if action == "promote":
            librarian.notes += f"\nPromoted on {datetime.now().strftime('%Y-%m-%d')} by {self.user_id}"
            return True
        elif action == "demote":
            librarian.notes += f"\nDemoted on {datetime.now().strftime('%Y-%m-%d')} by {self.user_id}"
            return True
        return False

    def configure_system(self, settings: Dict[str, Any]) -> bool:
        self.add_notification(
            "system",
            f"system configuration updated: {len(settings)} changes",
            "normal"
        )
        return True

    def __str__(self) -> str:
        status_text = UserStatus.get_name(self.status)
        return (
            f"\n{'='*60}\n"
            f"👑 ADMIN: {self.full_name}\n"
            f"{'='*60}\n"
            f"ID: {self.user_id} | Admin ID: {self.admin_id}\n"
            f"Username: {self.username} | Email: {self.email}\n"
            f"Access Level: {self.access_level} | Status: {status_text}\n"
            f"Permissions: {len(self.permissions)} granted\n"
            f"Borrowed: {len(self.current_borrowings)} (unlimited)\n"
            f"Registered: {self.registration_date} | Last Login: {self.last_login or 'Never'}\n"
            f"{'='*60}"
        )

# Class for user factory to create users based on role.
class UserFactory:
    @staticmethod
    def create_user(role: int, **kwargs) -> User:
        if 'user_id' not in kwargs:
            prefix = {
                1: 'STU',
                2: 'FAC',
                3: 'LIB',
                4: 'ADM'
            }.get(role, 'USR')
            kwargs['user_id'] = f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%S')}"

        if 'password' in kwargs and 'password_hash' not in kwargs:
            hash_obj = hashlib.sha256(kwargs['password'].encode())
            kwargs['password_hash'] = hash_obj.hexdigest()
            del kwargs['password']

        if role == UserRole.STUDENT.value:
            return Student(**kwargs)
        elif role == UserRole.FACULTY.value:
            return Faculty(**kwargs)
        elif role == UserRole.LIBRARIAN.value:
            return Librarian(**kwargs)
        elif role == UserRole.ADMIN.value:
            return Admin(**kwargs)
        else:
            raise ValueError(f"Invalid role value: {role}")

    @staticmethod
    def create_from_csv_row(row: Dict[str, str]) -> User:
        data = {
            'user_id': row['user_id'],
            'username': row['username'],
            'password_hash': row['password_hash'],
            'email': row['email'],
            'full_name': row['full_name'],
            'role': int(row['role']),
            'status': int(row.get('status', UserStatus.PENDING_ACTIVATION.value)),
            'department': row.get('department', ''),
            'phone': row.get('phone', ''),
            'address': row.get('address', ''),
            'registration_date': row.get('registration_date', ''),
            'last_login': row.get('last_login', ''),
            'total_books_borrowed': int(row.get('total_books_borrowed') or 0),
            'total_fines_paid': float(row.get('total_fines_paid', 0.0)),
            'times_blacklisted': int(row.get('times_blacklisted', 0)),
            'activation_date': row.get('activation_date', ''),
            'deactivation_date': row.get('deactivation_date', ''),
            'deactivation_reason': row.get('deactivation_reason', ''),
            'notes': row.get('notes', '')
        }
        role = data['role']
        if role == UserRole.STUDENT.value:
            data['student_id'] = row.get('student_id', data['user_id'])
            data['year_of_study'] = int(row.get('year_of_study', 1))
            data['major'] = row.get('major', 'Undeclared')
        elif role == UserRole.FACULTY.value:
            data['employee_id'] = row.get('employee_id', data['user_id'])
            data['designation'] = row.get('designation', 'Professor')
            data['qualification'] = row.get('qualification', '')
        elif role == UserRole.LIBRARIAN.value:
            data['employee_id'] = row.get('employee_id', data['user_id'])
            data['staff_id'] = row.get('staff_id', '')
            data['section'] = row.get('section', 'General')
            data['shift'] = row.get('shift', 'Day')
        elif role == UserRole.ADMIN.value:
            data['admin_id'] = row.get('admin_id', data['user_id'])
            data['access_level'] = row.get('access_level', 'Full')
        return UserFactory.create_user(role, **data)
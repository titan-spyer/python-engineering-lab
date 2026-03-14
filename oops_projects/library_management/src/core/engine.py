from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.user import User, UserFactory, UserRole, UserStatus, BorrowingRecord, FineRecord
from src.models.book import Resource, Book, ResourceFactory, PhysicalCopy, StatusType, ConditionType
from src.repository.storage import Storage
from src.core.validator import Validator
from src.utils.logger import Logger
from src.utils.auth_tools import AuthTools


class LibraryEngine:
    def __init__(self, data_path: str = "data"):
        self.storage = Storage(data_path)
        self.logger = Logger("library_engine")
        self.validator = Validator()
        self._user_cache: Dict[str, User] = {}
        self._book_cache: Dict[int, Resource] = {}
        self.logger.info("LibraryEngine initialized with data path: %s", data_path)

    def load_user(self, user_id: str) -> Optional[User]:
        if user_id in self._user_cache:
            return self._user_cache[user_id]
        user_data = self.storage.find_user_by_id(user_id)
        if user_data:
            user = UserFactory.create_from_csv_row(user_data)
            self._load_user_borrowing_history(user)
            self._load_user_fines(user)
            self._user_cache[user_id] = user
            return user
        self.logger.warning(f"User not found: {user_id}")
        return None

    def load_book(self, book_id: int) -> Optional[Resource]:
        if book_id in self._book_cache:
            return self._book_cache[book_id]
        book_data = self.storage.find_resource_by_id(book_id)
        if book_data:
            book = ResourceFactory.create_from_csv_row(book_data)
            self._load_book_copies(book)
            self._book_cache[book_id] = book
            return book
        self.logger.warning(f"Book not found: {book_id}")
        return None

    def save_user(self, user: User) -> bool:
        try:
            success = self.storage.save_user(user.to_dict())
            if success:
                self._user_cache[user.user_id] = user
                self._save_user_borrowing_history(user)
                self._save_user_fines(user)
                self.logger.info(f"User saved: {user.user_id}")
            return success
        except Exception as e:
            self.logger.error(f"Error saving user {user.user_id}: {e}")
            return False

    def save_book(self, book: Resource) -> bool:
        try:
            success = self.storage.save_resource(book.to_dict())
            if success:
                self._book_cache[book.id] = book
                self._save_book_copies(book)
                self.logger.info(f"Book saved: {book.id}")
            return success
        except Exception as e:
            self.logger.error(f"Error saving book {book.id}: {e}")
            return False

    def _load_user_borrowing_history(self, user: User) -> None:
        records_data = self.storage.find_borrowing_records_by_user(user.user_id)
        for record_data in records_data:
            record = BorrowingRecord.from_dict(record_data)
            if record.status == "active":
                user.current_borrowings.append(record)
            else:
                user.borrowing_history.append(record)

    def _save_user_borrowing_history(self, user: User) -> None:
        all_records = user.current_borrowings + user.borrowing_history
        for record in all_records:
            self.storage.save_borrowing_record(record.to_dict())

    def _load_user_fines(self, user: User) -> None:
        fines_data = self.storage.find_fines_by_user(user.user_id)
        for fine_data in fines_data:
            user.fines.append(FineRecord.from_dict(fine_data))

    def _save_user_fines(self, user: User) -> None:
        for fine in user.fines:
            self.storage.save_fine_record(fine.to_dict())

    def _load_book_copies(self, book: Resource) -> None:
        if book.format == 0:
            copies_data = self.storage.find_copies_by_resource(book.id)
            for copy_data in copies_data:
                book.physical_copies.append(PhysicalCopy.from_dict(copy_data))

    def _save_book_copies(self, book: Resource) -> None:
        for copy in book.physical_copies:
            self.storage.save_copy(copy.to_dict())

    def issue_book_to_user(self, user_id: str, book_id: int) -> Dict[str, Any]:
        user = self.load_user(user_id)
        if not user:
            return {"success": False,
                    "message": f"User with ID {user_id} not found"
            }
        book = self.load_book(book_id)
        if not book:
            return {"success": False,
                    "message": f"Book with ID {book_id} not found"
            }
        can_borrow, validation_message = self.validator.can_user_borrow(user, book)
        if not can_borrow:
            self.logger.warning(f"Borrowing denied for user {user_id}: {validation_message}")
            return {
                "success": False,
                "message": validation_message
            }
        if book.copies <= 0:
            return {
                "success": False,
                "message": f"No available copies of book {book.title}"
            }
        available_copy = None
        if book.format == 0:
            available_copy = book.get_available_copies()
            if not available_copy:
                return {
                    "success": False,
                    "message": f"No available physical copies of book {book.title}"
                }
            available_copy = available_copy[0]
            copy_id = available_copy.copy_id
        else:
            copy_id = f"digital-{book.id}"
        limits = user.get_borrowing_limits()
        due_date = (datetime.now() + timedelta(days=limits['max_days'])).strftime("%Y-%m-%d")
        record_id = f"BR-{user_id}-{book_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        borrowing_record = BorrowingRecord(
            record_id=record_id,
            user_id=user_id,
            resource_id=book_id,
            copy_id=copy_id,
            borrow_date=datetime.now().strftime("%Y-%m-%d"),
            due_date=due_date,
            renewal_count=0,
            fine_amount=0.0,
            status="active"
        )
        user.add_borrowing(borrowing_record)
        if book.format == 0: #physical copy
            available_copy.check_out(user_id, due_date)
            book.copies -= 1
            if book.copies == 0:
                book.status = 1
        else:
            book.copies -= 1

        self.save_user(user)
        self.save_book(book)

        self.logger.info(f"Book {book_id} issued to user {user_id}, copy {copy_id}, due {due_date}")
        self.storage.log_transaction({
            'transaction_id': f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'type': 'issue',
            'user_id': user_id,
            'resource_id': book_id,
            'copy_id': copy_id,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'due_date': due_date
        })
        return {
            "success": True,
            "message": f"Book {book.title} issued successfully, due on {due_date}",
            "due_date": due_date,
            "record_id": record_id,
            "copy_id": copy_id
        }

    def return_book(self, user_id: str, book_id: int, copy_id: str) -> Dict[str, Any]:
        user = self.load_user(user_id)
        if not user:
            return {"success": False,
                    "message": f"User with ID {user_id} not found"
            }
        book = self.load_book(book_id)
        if not book:
            return {"success": False,
                    "message": f"Book with ID {book_id} not found"
            }
        active_record = None
        for record in user.current_borrowings:
            if record.copy_id == copy_id:
                active_record = record
                break
        if not active_record:
            return {
                "success": False,
                "message": f"No active borrowing record found for copy {copy_id}"
            }
        book_id = active_record.resource_id
        book = self.load_book(book_id)
        fine_amount = active_record.return_item()
        if book:
            if book.format == 0:
                for copy in book.physical_copies:
                    if copy.copy_id == copy_id:
                        copy.check_in()
                        break
            book.copies += 1
            book.status = 0
            self.save_book(book)
        if fine_amount > 0:
            fine_record = FineRecord(
                fine_id=f"FINE-{user_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                user_id=user_id,
                record_id=active_record.record_id,
                amount=fine_amount,
                reason="overdue",
                issued_date=datetime.now().strftime("%Y-%m-%d"),
                due_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            )
            user.add_fine(fine_record)
        self.save_user(user)
        self.logger.info(f"Copy {copy_id} returned by user {user_id}, fine: ₹{fine_amount:.2f}")
        self.storage.log_transaction({
            'transaction_id': f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'type': 'return',
            'user_id': user_id,
            'copy_id': copy_id,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'fine_amount': fine_amount
        })
        if fine_amount > 0:
            user.add_notification(
                "fine",
                f"Your return of copy {copy_id} incurred a fine of ₹{fine_amount:.2f}. Please pay by {fine_record.due_date} to avoid further penalties.",
                "high"
            )
        return {
            "success": True,
            "message": f"Book returned successfully.",
            "fine_amount": fine_amount,
            "fine_waived": False
        }

    def renew_book(self, user_id: str, copy_id: str) -> Dict[str, Any]:
        user = self.load_user(user_id)
        if not user:
            return {
                "success": False,
                "message": f"User with ID {user_id} not found"
            }
        active_record = None
        for record in user.current_borrowings:
            if record.copy_id == copy_id:
                active_record = record
                break
        if not active_record:
            return {
                "success": False,
                "message": f"No active borrowing record found for copy {copy_id}"
            }
        for record in user.current_borrowings:
            due = datetime.strptime(record.due_date, "%Y-%m-%d")
            if datetime.now() > due:
                return {
                    "success": False,
                    "message": f"Cannot renew. You have overdue items."
                }
        limits = user.get_borrowing_limits()
        if active_record.renewal_count >= limits['max_renewals']:
            return {
                "success": False,
                "message": f"Renewal limit reached for copy {copy_id}"
            }
        active_record.renew()
        self.save_user(user)
        self.logger.info(f"copy {copy_id} renewed by user {user_id}, new due date: {active_record.due_date}")
        self.storage.log_transaction({
            'transaction_id': f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'type': 'renew',
            'user_id': user_id,
            'copy_id': copy_id,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'new_due_date': active_record.due_date
        })
        user.add_notification(
            "renewal",
            f"Your renewal for copy {copy_id} was successful. New due date is {active_record.due_date}.",
            "normal"
        )
        return {
            "success": True,
            "message": "Book renewed successfully.",
            "new_due_date": active_record.due_date,
            "renewal_count": active_record.renewal_count
        }

    def register_user(self, role: int, **kwargs) -> Dict[str, Any]:
        self.logger.info(f"Registering new user with role {role}")

        required_fields = ['username', 'email', 'full_name', 'password']
        for field in  required_fields:
            if field not in kwargs:
                return {
                    "success": False,
                    "message": f"Missing required field: {field}"
                }

        existing_user = self.find_user_by_username(kwargs['username'])
        if existing_user:
            return {
                "success": False,
                "message": f"Username {kwargs['username']} is already taken"
            }
        if not self.validator.validate_email(kwargs['email']):
            return {
                "success": False,
                "message": f"Invalid email format: {kwargs['email']}"
            }

        if not self.validator.validate_password_strength(kwargs['password']):
            return {
                "success": False,
                "message": "Password does not meet strength requirements"
            }

        try:
            kwargs['password_hash'] = AuthTools.hash_password(kwargs['password'])
            del kwargs['password']
            user = UserFactory.create_user(role, **kwargs)
            if self.save_user(user):
                self.logger.info(f"User registered successfully: {user.user_id}")
                return {
                    "success": True,
                    "message": f"User registered successfully",
                    "user_id": user.user_id,
                    "status": "pending_activation"
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to saver user to storage"
                }
        except Exception as e:
            self.logger.error(f"Error registering user: {e}")
            return {
                "success": False,
                "message": f"Error registering user: {str(e)}"
            }

    def activate_user(self, admin_id: str, user_id: str) -> Dict[str, Any]:
        admin = self.load_user(admin_id)
        if not admin or admin.role < UserRole.LIBRARIAN.value:
            return {
                "success": False,
                "message": "Unauthorized: only librarians and admins can active users"
            }
        user = self.load_user(user_id)
        if not user:
            return {
                "success": False,
                "message": f"User {user_id} not found"
            }
        if user.activate(admin.full_name):
            self.save_user(user)
            self.logger.info(f"User {user_id} activated by {admin.full_name}")
            return {
                "success": True,
                "message": f"User {user_id} activated successfully"
            }
        else:
            return {
                "success": False,
                "message": f"User {user_id} cannot be activated (current status: {UserStatus.get_name(user.status)})"
            }

    def deactivate_user(self, admin_id: str, user_id: str, reason: str="") -> Dict[str, Any]:
        admin = self.load_user(admin_id)
        if not admin or admin.role < UserRole.LIBRARIAN.value:
            return {
                "success": False,
                "message": "Unauthorized: only librarians and admins can deactivate users"
            }
        user = self.load_user(user_id)
        if not user:
            return {
                "success": False,
                "message": f"User {user_id} not found"
            }
        if user.current_borrowings:
            return {
                "success": False,
                "message": f"User {user_id} has active borrowings and cannot be deactivated"
            }
        if user.deactivate(admin.full_name, reason):
            self.save_user(user)
            self.logger.info(f"User {user_id} deactivated by {admin.full_name}")
            return {
                "success": True,
                "message": f"User {user_id} deactivated successfully"
            }
        else:
            return {
                "success": False,
                "message": f"User {user_id} cannot be deactivated"
            }

    def blacklist_user(self, admin_id: str, user_id: str, reason: str) -> Dict[str, Any]:
        admin = self.load_user(admin_id)
        if not admin or admin.role < UserRole.LIBRARIAN.value:
            return {
                "success": False,
                "message": "Unauthorized: only admins can blacklist a user"
            }
        user = self.load_user(user_id)
        if not user:
            return {
                "success": False,
                "message": f"User {user_id} not found"
            }
        if user.blacklist(admin.full_name, reason):
            self.save_user(user)
            self.logger.warning(f"User {user_id} blacklisted by {admin.full_name}: {reason}")
            return {
                "success": True,
                "message": f"User {user.full_name} balcklisted successfully"
            }
        else:
            return {
                "success": False,
                "message": f"User {user_id} cannot be blacklisted"
            }

    def remove_from_blacklist(self, admin_id: str, user_id: str) -> Dict[str, Any]:
        admin = self.load_user(admin_id)
        if not admin or admin.role < UserRole.LIBRARIAN.value:
            return {
                "success": False,
                "message": "Unauthorized: only admins can remove a user from blacklist"
            }
        user = self.load_user(user_id)
        if not user:
            return {
                "success": False,
                "message": f"User {user_id} not found"
            }
        if user.remove_from_blacklist(admin.full_name):
            self.save_user(user)
            self.logger.info(f"User {user_id} removed from blacklist by {admin.full_name}")
            return {
                "success": True,
                "message": f"User {user.full_name} removed from blacklist successfully"
            }
        else:
            return {
                "success": False,
                "message": f"User {user_id} cannot be removed from blacklist"
            }

    def waive_user_fine(self, admin_id: str, fine_id: str) -> Dict[str, Any]:
        admin = self.load_user(admin_id)
        if not admin or admin.role < UserRole.LIBRARIAN.value:
            return {
                "success": False,
                "message": "Unauthorized: only librarians and admins can waive fines"
            }
        all_users = self.get_all_users()
        for user in all_users:
            for fine in user.fines:
                if fine.fine_id == fine_id and fine.status == "pending":
                    fine.waive(admin.full_name)
                    self.save_user(user)
                    self.logger.info(f"Fine {fine_id} waived by {admin.full_name}")
                    user.add_notification(
                        "fine",
                        f"Your fine of ₹{fine.amount:.2f} for record {fine.record_id} has been waived by {admin.full_name}.",
                        "high"
                    )
                    return {
                        "success": True,
                        "message": f"Fine {fine_id} waived successfully",
                        "user_id": user.user_id,
                        "amount": fine.amount
                    }
        return {
            "success": False,
            "message": f"Fine {fine_id} not found or already processed"
        }

    def pay_fine(self, user_id: str, fine_id: str) -> Dict[str, Any]:
        user = self.load_user(user_id)
        if not user:
            return {
                "success": False,
                "message": f"User {user_id} not found"
            }
        if user.pay_fine(fine_id):
            self.save_user(user)
            self.logger.info(f"User {user_id} paid fine {fine_id}")
            return {
                "success": True,
                "message": f"Fine {fine_id} paid successfully"
            }
        return {
            "success": False,
            "message": f"Fine {fine_id} not found or already paid"
        }

    def search_books_by_title(self, title: str) -> List[Resource]:
        results = self.storage.search_resources_by_title(title)
        books = []
        for data in results:
            book = ResourceFactory.create_from_csv_row(data)
            self._load_book_copies(book)
            books.append(book)
        return books

    def search_books_by_author(self, author: str) -> List[Resource]:
        results = self.storage.search_resources_by_author(author)
        books = []
        for data in results:
            book = ResourceFactory.create_from_csv_row(data)
            self._load_book_copies(book)
            books.append(book)
        return books

    def search_books_by_genre(self, genre: str) -> List[Resource]:
        results = self.storage.search_resources_by_genre(genre)
        books = []
        for data in results:
            book = ResourceFactory.create_from_csv_row(data)
            self._load_book_copies(book)
            books.append(book)
        return books

    def search_books_by_isbn(self, isbn: str) -> Optional[Resource]:
        data = self.storage.find_resource_by_isbn(isbn)
        if data:
            book = ResourceFactory.create_from_csv_row(data)
            self._load_book_copies(book)
            return book
        return None

    def find_user_by_username(self, username: str) -> Optional[User]:
        user_data = self.storage.find_user_by_username(username)
        if user_data:
            user = UserFactory.create_from_csv_row(user_data)
            self._load_user_borrowing_history(user)
            self._load_user_fines(user)
            return user
        return None

    def find_user_by_email(self, email: str) -> Optional[User]:
        user_data = self.storage.find_user_by_email(email)
        if user_data:
            user = UserFactory.create_from_csv_row(user_data)
            self._load_user_borrowing_history(user)
            self._load_user_fines(user)
            return user
        return None

    def get_all_users(self) -> List[User]:
        user_data = self.storage.get_all_users()
        users = []
        for data in user_data:
            user = UserFactory.create_from_csv_row(data)
            self._load_user_borrowing_history(user)
            self._load_user_fines(user)
            users.append(user)
        return users

    def get_all_books(self) -> List[Resource]:
        resource_data = self.storage.get_all_resources()
        resources = []
        for data in resource_data:
            resource = ResourceFactory.create_from_csv_row(data)
            self._load_book_copies(resource)
            resources.append(resource)
        return resources

    def get_borrowing_report(self, user_id: str) -> Dict[str, Any]:
        user = self.load_user(user_id)
        if not user:
            return {"error": "user not found"}
        total_borrowed = len(user.borrowing_history)
        active_borrowings = len(user.current_borrowings)
        overdue_count = 0

        for record in user.current_borrowings:
            due = datetime.strptime(record.due_date, "%Y-%m-%d")
            if datetime.now() > due:
                overdue_count += 1

        current_books = []
        for record in user.current_borrowings:
            book = self.load_book(record.resource_id)
            current_books.append({
                'copy_id': record.copy_id,
                'title': book.title if book else 'unknown',
                'borrow_date': record.borrow_date,
                'due_date': record.due_date,
                'days_remaining': (datetime.strptime(record.due_date, "%Y-%m-%d") - datetime.now()).days,
                'renewals': record.renewal_count
            })
        return {
            'user_id': user_id,
            'user_name': user.full_name,
            'total_books_borrowed': total_borrowed,
            'active_borrowings': active_borrowings,
            'overdue_count': overdue_count,
            'current_books': current_books,
            'borrowing_limit': user.get_borrowing_limits()['max_books'],
            'remaining_borrows': user.get_borrowing_limits()['max_books'] - active_borrowings
        }

    def get_fines_report(self, user_id: str) -> Dict[str, Any]:
        user = self.load_user(user_id)
        if not user:
            return {"error": "user not found"}
        pending_fines = [f for f in user.fines if f.status == "pending"]
        paid_fines = [f for f in user.fines if f.status == "paid"]
        waived_fines = [f for f in user.fines if f.status == "waived"]

        total_pending = sum(f.amount for f in pending_fines)
        total_paid = sum(f.amount  for f in paid_fines)
        total_waived = sum(f.amount for f in waived_fines)

        fine_details = []
        for fine in user.fines:
            fine_details.append({
                'fine_id': fine.fine_id,
                'amount': fine.amount,
                'reason': fine.reason,
                'issued_date': fine.issued_date,
                'paid_date': fine.paid_date,
                'status': fine.status
            })

        return {
            'user_id': user_id,
            'user_name': user.full_name,
            'total_pending': total_pending,
            'total_paid': total_paid,
            'total_waived': total_waived,
            'pending_count': len(pending_fines),
            'paid_count': len(paid_fines),
            'waived_count': len(waived_fines),
            'fines': fine_details
        }

    def get_system_report(self) -> Dict[str, Any]:
        users = self.get_all_users()
        books = self.get_all_books()
        total_users = len(users)
        active_users = sum(1 for u in users if u.status == UserStatus.ACTIVE.value)
        blacklisted_users = sum(1 for u in users if u.status == UserStatus.BLACKLISTED.value)

        users_by_role = {
            'student': sum(1 for u in users if u.role == UserRole.STUDENT.value),
            'faculty': sum(1 for u in users if u.role == UserRole.FACULTY.value),
            'librarians': sum(1 for u in users if u.role == UserRole.LIBRARIAN.value),
            'admins': sum(1 for u in users if u.role == UserRole.ADMIN.value)
        }

        total_books = len(books)
        available_books = sum(1 for b in books if b.copies > 0)
        checked_out = sum(1 for b in books if b.status == 1)

        books_by_type = {}
        for book in books:
            type_name = book.type_of_resource()
            books_by_type[type_name] = books_by_type.get(type_name, 0) + 1

        active_borrowings = sum(len(u.current_borrowings) for u in users)
        total_fines_pending = sum(sum(f.amount for f in u.fines if f.status == "pending") for u in users)

        return {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'users': {
                'total': total_users,
                'active': active_users,
                'blacklisted': blacklisted_users,
                'by_role': users_by_role
            },
            'resources': {
                'total': total_books,
                'available': available_books,
                'checked_out': checked_out,
                'by_type': books_by_type
            },
            'transactions': {
                'active_borrowings': active_borrowings,
                'total_fines_pending': total_fines_pending
            }
        }

    def override_borrowing_limits(self, admin_id: str, user_id: str, new_limit: int) -> Dict[str, Any]:
        admin = self.load_user(admin_id)
        if not admin or admin.role < UserRole.ADMIN.value:
            return {
                "success": False,
                "message": "Unauthorized: only admins can override borrowing limits"
            }
        user = self.load_user(user_id)
        if not user:
            return {
                "success": False,
                "message": f"User {user_id} not found"
            }
        user.notes += f"\nBorrowing limit overridden to {new_limit} by {admin.full_name} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self.save_user(user)
        self.logger.info(f"Borrowing limit for user {user_id} overridden to {new_limit} by admin {admin.full_name}")
        return {
            "success": True,
            "message": f"Borrowing limit for user {user.full_name} overridden to {new_limit}"
        }
    def clear_user_fines(self, admin_id: str, user_id: str) -> Dict[str, Any]:
        admin = self.load_user(admin_id)
        if not admin or admin.role < UserRole.ADMIN.value:
            return {
                "success": False,
                "message": "Unauthorized: only admins can clear user fines"
            }
        user = self.load_user(user_id)
        if not user:
            return {
                "success": False,
                "message": f"User {user_id} not found"
            }
        cleared_count = 0
        cleared_amount = 0.0
        for fine in user.fines:
            if fine.status == "pending":
                fine.waive(admin.full_name)
                cleared_count += 1
                cleared_amount += fine.amount
        
        if cleared_count > 0:
            self.save_user(user)
            user.add_notification(
                "fine",
                f"Your pending fines totaling ₹{cleared_amount:.2f} have been cleared by {admin.full_name}.",
                "high"
            )
            self.logger.info(f"Admin {admin_id}  cleared {cleared_count} fines for user {user_id}, total amount: ₹{cleared_amount:.2f}")
            return {
                "success": True,
                "message": f"Cleared {cleared_count} fines for user {user.full_name}, total amount: ₹{cleared_amount:.2f}"
            }
        else:
            return {
                "success": False,
                "message": f"No pending fines to clear for user {user.full_name}"
            }
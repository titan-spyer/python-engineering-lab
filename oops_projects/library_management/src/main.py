import os
import sys
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import getpass
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.engine import LibraryEngine
from src.models.user import User, UserRole, UserStatus, Student, Faculty, Librarian, Admin
from src.models.book import Resource, Book, Journal, ResearchPaper, ResourceType
from src.utils.logger import get_logger
from src.utils.auth_tools import AuthTools

class LibraryCLI:
    COLORS = {
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
        'RED': '\033[91m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'PURPLE': '\033[95m',
        'CYAN': '\033[96m',
        'WHITE': '\033[97m',
        'BG_RED': '\033[41m',
        'BG_GREEN': '\033[42m',
        'BG_YELLOW': '\033[43m',
        'BG_BLUE': '\033[44m'
    }

    def __init__(self):
        self.engine = LibraryEngine(data_path="data")
        self.logger = get_logger("cli")
        self.current_user: Optional[User] = None
        self.session_start = datetime.now()

    def _clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def _print_color(self, text: str, color: str = 'WHITE', bold: bool = False):
        if bold:
            print(f"{self.COLORS['BOLD']}{self.COLORS[color]}{text}{self.COLORS['RESET']}")
        else:
            print(f"{self.COLORS[color]}{text}{self.COLORS['RESET']}")

    def  _print_header(self, title: str):
        self._clear_screen()
        width = 80
        self._print_color("=" * width, 'CYAN', bold=True)
        self._print_color(f"{title:^{width}}", 'CYAN', bold=True)
        self._print_color("=" * width, 'CYAN', bold=True)
        print()

    def _print_success(self, message: str):
        self._print_color(f"✅ {message}", 'GREEN')

    def _print_error(self, message: str):
        self._print_color(f"❌ {message}", 'RED')

    def _print_warning(self, message: str):
        self._print_color(f"⚠️ {message}", 'YELLOW')

    def _print_info(self, message: str):
        self._print_color(f"ℹ️ {message}", 'BLUE')

    def _print_table(self, headers: List[str], rows: List[List[Any]], max_width: int = 80):
        if not rows:
            self._print_warning("No data to display.")
            return
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        total_width = sum(col_widths) + 3 * (len(headers) - 1) + 4
        if total_width > max_width:
            scale = max_width / total_width
            col_widths = [max(5, int(w * scale)) for w in col_widths]
        header_line = "| " + " | ".join(h.ljust(col_widths[i]) for  i, h in enumerate(headers)) + " |"
        self._print_color("┌" + "─" * (len(header_line) - 2) + "┐", 'CYAN')
        self._print_color(header_line, 'CYAN', bold=True)
        self._print_color("├" + "─" * (len(header_line) - 2) + "┤", 'CYAN')
        for row in rows:
            line = "│ " + " │ ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)) + " │"
            self._print_color(line, 'WHITE')
        self._print_color("└" + "─" * (len(header_line) - 2) + "┘", 'CYAN')

    def _get_input(self, prompt: str, required: bool = True, password: bool = False) -> str:
        while True:
            if password:
                value = getpass.getpass(prompt)
            else:
                value = input(prompt).strip()
            if not value and required:
                self._print_error("This field is required")
                continue
            return value

    def _get_choice(self, prompt: str, options: List[str], allow_back: bool = True) -> str:
        print()
        for i, option in enumerate(options, 1):
            self._print_color(f" {i}. {option}", 'WHITE')
        if allow_back:
            self._print_color(f" 0. Back", 'YELLOW')
        print()
        while True:
            try:
                choice = self._get_input(prompt)
                if choice == '0' and allow_back:
                    return '0'
                idx = int(choice)
                if 1 <= idx <= len(options):
                    return str(idx)
                else:
                    self._print_error(f"Please enter a number between 1 and {len(options)}")
            except ValueError:
                self._print_error("Please enter a valid number")
    def _pause(self):
        print()
        self._get_input("Press Enter to continue...", required=False)

    def _login(self) -> bool:
        self._print_header("🔐 USER LOGIN")
        username = self._get_input("Username: ")
        password = self._get_input("password: ", password=True)
        user = self.engine.find_user_by_username(username)
        if not user:
            self._print_error("Invalid username or passowrd")
            self._pause()
            return False
        if not user.verify_password(password):
            self._print_error("Invalid username or password")
            self.logger.log_user_login(username, username, False)
            self._pause()
            return False
        if user.status != UserStatus.ACTIVE.value:
            status_name = UserStatus.get_name(user.status)
            self._print_error(f"Account is {status_name}. Please contact administrator")
            self._pause()
            return False
        user.update_last_login()
        self.engine.save_user(user)
        self.current_user = user
        self.logger.log_user_login(user.user_id, user.username, True)
        self.logger.info(f"User {user.username} logged in successfully")
        self._print_success(f"Welcom back, {user.full_name}!")
        time.sleep(1)
        return True
    def _logout(self):
        if self.current_user:
            self.logger.log_user_logout(self.current_user.user_id, self.current_user.username)
            self.logger.info(f"User {self.current_user.username} logged out")
            self.current_user = None
            self._print_success("Logged out successfully")
            time.sleep(1)

    def run(self):
        self.logger.log_system_startup()
        while True:
            if not self.current_user:
                if not self.show_auth_menu():
                    break
            else:
                self._show_main_menu()
    def _show_auth_menu(self):
        self._print_header("📚 LIBRARY MANAGEMENT SYSTEM")
        print("Welcome to the Library Management System!\n")
        options = ["Login", "Register", "Exit"]
        choice = self._get_choice("Select option: ", options, allow_back=False)
        if choice == '1':
            if self._login():
                return True
            return True
        if choice == '2':
            self._register()
            return True
        if choice == '3':
            self._exit_system()
            return False
        return True
    def _register(self):
        self._print_header("📝 USER REGISTRATION")
        print("Create a new Account\n")
        username = self._get_input("Username (min 6 charcters): ")
        email = self._get_input("Email: ")
        full_name = self._get_input("Full Name: ")
        phone = self._get_input("Phone (optional): ", required=False)
        department = self._get_input("Department (optional): ", required=False)
        print("\nSelect role:")
        role_options = ["Student", "Faculty", "Librarian", "Admin (requires approval)"]
        role_choice = self._get_choice("Choose role: ", role_options, allow_back=True)
        if role_choice == '0':
            return
        role_map = {'1': 1, '2': 2, '3': 3, '4': 4}
        role = role_map[role_choice]
        #Passowrd
        print("\nPassowrd requirements:")
        print("• At least 8 characters")
        print("• At least one uppercase letter")
        print("• At least one lowercase letter")
        print("• At least one number")
        print("• At least one special character")
        print()
        password = self._get_input("Passowrd: ", password=True)
        confirm = self._get_input("Confirm Passowrd: ", password=True)
        if password != confirm:
            self._print_error("Password do not match")
            self._pause()
            return
        result = self.engine.register_user(
            role=role,
            username=username,
            email=email,
            full_name=full_name,
            password=password,
            phone=phone,
            department=department
        )
        if result['success']:
            self._print_success(result['message'])
            self._print_info(f"Your user ID is: {result['user_id']}")
            self._print_warning("Your account is pending activation. Please wait for librarian/admin approval.")
            self.logger.log_user_registration(result['user_id'], username, role)
        else:
            self._print_error(result['message'])
        self._pause()

    def _show_main_menu(self):
        if not self.current_user:
            return
        role_name = self.current_user.get_role_name()
        self._print_header(f"🏠 MAIN MENU - {role_name}: {self.current_user.full_name}")
        self._print_info(f"User: {self.current_user.username} | Status: {UserStatus.get_name(self.current_user.status)}")
        unread = len(self.current_user.get_unread_notifications())
        if unread > 0:
            self._print_warning(f"You have {unread} unread notification(s)")
        overdue = 0
        for record in self.current_user.current_borrowings:
            due = datetime.strptime(record.due_date, "%Y-%m-%d")
            if datetime.now() > due:
                overdue += 1
        if overdue > 0:
            self._print_error(f"You have {overdue} overdue item(s)")
            print()
        options = [
            "📖 Browse/Search Books",
            "📋 My Borrowings",
            "💰 My Fines",
            "🔔 Notifications",
            "👤 My Profile"
        ]
        if self.current_user.role == UserRole.STUDENT.value:
            options.extend(["📚 Request Purchase (Faculty only)", "⬅️ "])
        elif self.current_user.role == UserRole.FACULTY.value:
            options.extend(["📚 Request Purchase", "⬅️ "])
        elif self.current_user.role == UserRole.LIBRARIAN.value:
            options.extend([
                "👥 Manage Users",
                "📚 Manage Resources",
                "📊 View Reports",
                "💰 Manage Fines"
            ])
        elif self.current_user.role == UserRole.ADMIN.value:
            options.extend([
                "👥 Manage Users",
                "📚 Manage Resources",
                "📊 View Reports",
                "💰 Manage Fines",
                "⚙️ System Settings",
                "💾 Backup/Restore"
            ])
        options.append("🚪 Logout")
        choice = self._get_choice("select option: ", options)
        if choice == '0':
            return
        handlers = {
            '1': self._browse_books,
            '2': self._view_borrowings,
            '3': self._view_fines,
            '4': self._view_notifications,
            '5': self._view_profile
        }
        offset = 5
        if self.current_user.role in [UserRole.STUDENT.value, UserRole.FACULTY.value]:
            if choice == '6':
                if self.current_user.role == UserRole.FACULTY.value:
                    self._request_purchase()
            elif choice == str(len(options) - 1):
                self._logout()
        elif self.current_user.role == UserRole.LIBRARIAN.value:
            if choice == '6':
                self._manage_users()
            elif choice == '7':
                self._manage_resources()
            elif choice == '8':
                self._view_reports()
            elif choice == '9':
                self._logout()
            elif choice == str(len(options) - 1):
                self._logout()
        elif self.current_user.role == UserRole.ADMIN.value:
            if choice == '6':
                self._manage_users()
            elif choice == '7':
                self._manage_resources()
            elif choice == '8':
                self._view_reports()
            elif choice == '9':
                self._manage_fines()
            elif choice == '10':
                self._system_settings()
            elif choice == '11':
                self._backup_restore()
            elif choice == str(len(options) - 1):
                self._logout()
        if choice == str(len(options) - 1):
            self._logout()


    def _browse_books(self):
        self._print_header("📖 BROWSE BOOKS")
        while True:
            print("\nSearch options: ")
            options = [
                "Search by Title",
                "Search by Author",
                "Search by Genre",
                "Search by ISBN",
                "View All Books",
                "View Available Books",
                "Back to Main Menu"
            ]
            choice = self._get_choice("Select search option: ", options, allow_back=False)
            if choice == '7':
                break
            results = []
            if choice == '1':
                title = self._get_input("Enter title: ")
                results = self.engine.search_books_by_title(title)
            elif choice == '2':
                author = self._get_input("Enter author: ")
                results = self.engine.search_books_by_author(author)
            elif choice == '3':
                genre = self._get_input("Enter genre: ")
                results = self.engine.search_books_by_genre(genre)
            elif choice == '4':
                isbn = self._get_input("Enter ISBN: ")
                book = self.engine.search_books_by_isbn(isbn)
                results = [book] if book else []
            elif choice == '5':
                results = self.engine.get_all_books()
            elif choice == '6':
                results = [b for b in self.engine.get_all_books() if b.copies > 0]
            if not results:
                self._print_warning("No books found")
                self._pause()
                continue
            self._display_book_results(results)

    def _display_book_results(self, books: List[Resource]):
        while True:
            self._print_header("📚 SEARCH RESULTS")
            headers = ["ID", "Title", "Author", "Type", "Avaiable"]
            rows = []
            for book in books[:20]:
                rows.append([
                    book.id,
                    book.title[:30] + "..." if len(book.title) > 30 else book.title,
                    book.author[:20] + "..." if len(book.author) > 20 else book.author,
                    book.type_of_resource(),
                    f"{book.copies}/{book.total_copies}"
                ])
            self._print_table(headers, rows)
            if len(books) > 20:
                self._print_info(f"Showing 20 of {len(books)} results")
            
            print("\nOptions:")
            print("  B <ID> - Borrow a book")
            print("  V <ID> - View details")
            print("  N      - Next page")
            print("  P      - Previous page")
            print("  Q      - Back to search")

            cmd = self._get_input("\nCommand: ", required=False).strip().upper()

            if cmd == 'Q':
                break
            elif cmd.startswith('V '):
                try:
                    book_id = int(cmd[2:])
                    self._view_book_details(book_id)
                except:
                    self._print_error("Invalid book ID")
            elif cmd.startswith('B '):
                try:
                    book_id = int(cmd[2:])
                    self._borrow_book(book_id)
                except:
                    self._print_error("Invalid book ID")
    def _view_book_details(self, book_id: int):
        book = self.engine.load_book(book_id)
        if not book:
            self._print_error("Book not found")
            self._pause()
            return
        self._print_header(f"📖 BOOK DETAILS: {book.title}")
        print(str(book))
        if book.format == 0:
            print("\n 📦 Physical Copies:")
            for copy in book.physical_copies:
                status = "✅ Available" if copy.status == 0 else "📤 Checked Out"
                condition = copy.condition.name
                print(f" • {copy.copy_id} - {status} - {condition} - {copy.location}")
                self._pause()

    def _borrow_book(self, book_id: int):
        if not self.current_user:
            self._print_error("Please Login first")
            self._pause()
            return
        result = self.engine.issue_book_to_user(self.current_user.user_id, book_id)
        if result['success']:
            self._print_success(result['message'])
            self._print_info(f"Due date: {result['due_date']}")
            self._print_info(f"Copy ID: {result['copy_id']}")
            self.current_user = self.engine.load_user(self.current_user.user_id)
        else:
            self._print_error(result['message'])
        self._pause()

    def _view_borrowings(self):
        if not self.current_user:
            return
        report = self.engine.get_borrowing_report(self.current_user.user_id)
        self._print_header(f"📋 BORROWINGS - {self.current_user.full_name}")
        print(f"Total books borrowed: {report['total_books_borrowed']}")
        print(f"Active borrowings: {report['active_borrowings']}")
        print(f"Overdue items: {report['overdue_count']}")
        print(f"Remaining borrows: {report['remaining_borrows']}")
        print()
        if report['fines']:
            headers = ["Fine ID", "Amount", "Reason", "Issued", "Status"]
            rows = []
            for fine in report['fines']:
                rows.append([
                    fine['fine_id'][:10] + "...",
                    f"${fine['amount']:.2f}",
                    fine['reason'],
                    fine['issued_date'],
                    fine['status']
                ])
            self._print_table(headers, rows)
            if report['pending_count'] > 0:
                print("\nOptions:")
                print("  P <FineID> - Pay fine")
                print("  Q          - Back")
                cmd = self._get_input("\nCommand: ", required=False).strip().upper()
                if cmd.startswith('P '):
                    fine_id = cmd[2:]
                    self._pay_fine(fine_id)
        else:
            self._print_info("No fines found")
            self._pause()

    def _pay_fine(self, fine_id: str):
        result = self.engine.pay_fine(self.current_user.user_id, fine_id)
        if result['success']:
            self._print_success(result['message'])
            self.current_user = self.engine.load_user(self.current_user.user_id)
        else:
            self._print_error(result['message'])
        self._pause()

    def _view_notifications(self):
        if not self.current_user:
            return
        self._print_header(f"🔔 NOTIFICATIONS - {self.current_user.full_name}")
        notifications = self.current_user.notifications
        unread = [n for n in notifications if not n.read]
        if not notifications:
            self._print_info("No notifications")
        else:
            for i, noti in enumerate(notifications[-10:], 1):
                status = "📫" if not noti.read else "📭"
                priority_icon = {
                    "low": "ℹ️",
                    "normal": "📌",
                    "high": "⚠️",
                    "urgent": "🚨"
                }.get(noti.priority, "📌")
                print(f"{i}. {status} {priority_icon} [{noti.type}] {noti.message}")
                print(f"    {noti.created_date}")
                print()
            if unread:
                print("\nOptions:")
                print("  M <#>- Mark as read")
                print("  A    - Mark all as read")
                print("  Q    - Back")
                cmd = self._get_input("\nCommand: ", required=False).strip().upper()
                if cmd == 'A':
                    for noti in unread:
                        noti.mark_as_read()
                    self.engine.save_user(self.current_user)
                    self._print_success("All notifications marked as read")
                    self._pause()
                elif cmd.startswith('M '):
                    try:
                        idx = int(cmd[2:]) - 1
                        if 0 <= idx < len(notifications):
                            notifications[-(idx+1)].mark_as_read()
                            self.engine.save_user(self.current_user)
                            self._print_success("Notifications marked as read")
                        else:
                            self._print_error("Invalid notification number")
                    except:
                        self._print_error("Invalid command")
                    self._pause()
        self._pause()

    def _view_profile(self):
        if not self.current_user:
            return
        self._print_header(f"👤 USER PROFILE")
        print(f"User ID: {self.current_user.user_id}")
        print(f"Username: {self.current_user.username}")
        print(f"Full Name: {self.current_user.full_name}")
        print(f"Email: {self.current_user.email}")
        print(f"Role: {self.current_user.get_role_name()}")
        print(f"Status: {UserStatus.get_name(self.current_user.status)}")
        print(f"Department: {self.current_user.department or 'N/A'}")
        print(f"Phone: {self.current_user.phone or 'N/A'}")
        print(f"Registered: {self.current_user.registration_date}")
        print(f"Last Login: {self.current_user.last_login or 'Never'}")

        if isinstance(self.current_user, Student):
            print(f"Student ID: {self.current_user.student_id}")
            print(f"Year of Study: {self.current_user.year_of_study}")
            print(f"Major: {self.current_user.major}")
        elif isinstance(self.current_user, Faculty):
            print(f"Employee ID: {self.current_user.employee_id}")
            print(f"Designation: {self.current_user.designation}")
            print(f"Qualification: {self.current_user.qualification or 'N/A'}")
        elif isinstance(self.current_user, Librarian):
            print(f"Staff ID: {self.current_user.staff_id}")
            print(f"Section: {self.current_user.section}")
            print(f"Shift: {self.current_user.shift}")
        elif isinstance(self.current_user, Admin):
            print(f"Admin ID: {self.current_user.admin_id}")
            print(f"Access Level: {self.current_user.access_level}")

        print("\nOptions:")
        print("  1. Change Password")
        print("  2. Update Contact Info")
        print("  3. Back")

        choice = self._get_choice("Select option: ", ["Change Password", "Update Contact Info", "Back"], allow_back=False)

        if choice == '1':
            self._change_password()
        elif choice == '2':
            self._update_contact_info()

    def _change_password(self):
        self._print_header("🔐 CHANGE PASSWORD")
        current = self._get_input("Current Password: ", password=True)
        if not self.current_user.verify_password(current):
            self._print_error("Incorrect Password")
            self._pause()
            return
        new = self._get_input("New Password: ", password=True)
        confirm = self._get_input("Confirm New Password: ", password=True)
        if new != confirm:
            self._print_error("Password do not match")
            self._pause()
            return
        valid, message = self.engine.validator.validate_password_strength(new)
        if not valid:
            self._print_error(message)
            self._pause()
            return
        self.current_user.password_hash = AuthTools.hash_password(new)
        self.engine.save_user(self.current_user)
        self._print_success("password changed successfully")
        self._pause()

    def _update_contact_info(self):
        self._print_header("📧 UPDATE CONTACT INFO")
        print("Leave blank to keep current value")
        email = self._get_input(f"Email [{self.current_user.email}]: ", required=False)
        if email:
            valid, message = self.engine.validator.validate_email(email)
            if not valid:
                self._print_error(message)
                self._pause()
                return
            self.current_user.email = email
        
        phone = self._get_input(f"Phone [{self.current_user.phone or ''}]: ", required=False)
        if phone:
            valid, message = self.engine.validator.validate_phone(phone)
            if not valid:
                self._print_error(message)
                self._pause()
                return
            self.current_user.phone = phone
        
        address = self._get_input(f"Address [{self.current_user.address or ''}]: ", required=False)
        if address:
            self.current_user.address = address
        self.engine.save_user(self.current_user)
        self._print_success("Contact information updated")
        self._pause()

    def _request_purchase(self):
        self._print_header("📚 REQUEST PURCHASE")
        if not isinstance(self.current_user, Faculty):
            self._print_error("Only faculty can request purchases")
            self._pause()
            return
        title = self._get_input("Book Title: ")
        author = self._get_input("Author: ")
        isbn = self._get_input("ISBN (optional): ", required=False)
        reason = self._get_input("Reason for request: ")
        request_id = self.current_user.request_purchase(title, author, isbn)
        self._print_success(f"Purchase request submitted")
        self._print_info(f"Request ID: {request_id}")
        self._pause()

    def _manage_users(self):
        self._print_header("👥 USER MANAGEMENT")
        while True:
            options = [
                "View All Users",
                "Search Users",
                "Activate User",
                "Deactivate User",
                "Blacklist User",
                "Remove from Blacklist",
                "Back"
            ]
            choice = self._get_choice("Select option: ", options)
            
            if choice == '0' or choice == '7':
                break
            elif choice == '1':
                self._view_all_users()
            elif choice == '2':
                self._search_users()
            elif choice == '3':
                self._activate_user()
            elif choice == '4':
                self._deactivate_user()
            elif choice == '5':
                self._blacklist_user()
            elif choice == '6':
                self._remove_from_blacklist()

    def _view_all_users(self):
        users = self.engine.get_all_users()
        self._print_header("📋 ALL USERS")
        headers = ["ID", "Username", "Name", "Role", "Status", "Borrowed"]
        rows = []
        for user in users[:30]:
            rows.append([
                user.user_id[:8] + "...",
                user.username,
                user.full_name[:15] + "..." if len(user.full_name) > 15 else user.full_name,
                user.get_role_name(),
                UserStatus.get_name(user.status),
                f"{len(user.current_borrowings)}/{user.get_borrowing_limits()['max_books']}"
            ])
        self._print_table(headers, rows)
        if len(user) > 30:
            self._print_info(f"Showing 30 of {len(users)} users")
        self._pause()

    def _search_user(self):
        search_term = self._get_input("Enter username, email, or name to search: ")
        users = self.engine.get_all_users()
        results = [
            u for u in users
            if search_term.lower() in u.username.lower()
            or search_term.lower() in u.email.lower()
            or search_term.lower() in u.full_name.lower()
        ]

        self._print_header(f"🔍 SEARCH RESULTS: {len(results)} users found")
        if results:
            headers = ["ID", "Username", "Name", "Role", "Status"]
            rows = []
            for user in results[:20]:
                rows.append([
                    user.user_id[:8] + "...",
                    user.username,
                    user.full_name[:15] + "..." if len(user.full_name) > 15 else user.full_name,
                    user.get_role_name(),
                    UserStatus.get_name(user.status)
                ])
            self._print_table(headers, rows)
        self._pause()

    def  _activate_user(self):
        self._print_header("✅ ACTIVE USER")
        user_id = self._get_input("Enter User ID to active: ")
        result = self.engine.activate_user(self.current_user.user_id, user_id)
        if result['success']:
            self._print_success(result['message'])
        else:
            self._print_error(result['message'])
        self._pause()

    def _deactive_user(self):
        self._print_header("❌ DEACTIVATE USER")
        user_id = self._get_input("Enter User ID to deactivate: ")
        reason = self._get_input("Reason for deactivation: ")
        result = self.engine.deactivate_user(self.current_user.user_id, user_id, reason)
        if result['success']:
            self._print_success(result['message'])
        else:
            self._print_error(result['message'])
        self._pause()

    def _blacklist_user(self):
        self._print_header("⛔ BLACKLIST USER")
        
        user_id = self._get_input("Enter User ID to blacklist: ")
        reason = self._get_input("Reason for blacklisting: ")
        
        result = self.engine.blacklist_user(self.current_user.user_id, user_id, reason)
        
        if result['success']:
            self._print_success(result['message'])
        else:
            self._print_error(result['message'])
        
        self._pause()

    def _remove_from_blacklist(self):
        self._print_header("✅ REMOVE FROM BLACKLIST")
        
        user_id = self._get_input("Enter User ID to restore: ")
        
        result = self.engine.remove_from_blacklist(self.current_user.user_id, user_id)
        
        if result['success']:
            self._print_success(result['message'])
        else:
            self._print_error(result['message'])
        
        self._pause()

    def _manage_resources(self):
        self._print_header("📚 RESOURCE MANAGEMENT")
        while True:
            options = [
                "Add New Resource",
                "Edit Resource",
                "Delete/Archive Resource",
                "Add Copy",
                "Remove Copy",
                "Update Location",
                "Update Condition",
                "View All Resources",
                "Back"
            ]
            
            choice = self._get_choice("Select option: ", options)
            
            if choice == '0' or choice == '9':
                break
            elif choice == '1':
                self._add_resource()
            elif choice == '2':
                self._edit_resource()
            elif choice == '3':
                self._delete_resource()
            elif choice == '4':
                self._add_copy()
            elif choice == '5':
                self._remove_copy()
            elif choice == '6':
                self._update_location()
            elif choice == '7':
                self._update_condition()
            elif choice == '8':
                self._view_all_resources()

    def _add_resource(self):
        self._print_header("➕ ADD NEW RESOURCE")
        
        print("Select resource type:")
        type_options = ["Book", "Journal", "Research Paper", "Magazine", "DVD", "Comic"]
        type_choice = self._get_choice("Choose type: ", type_options)
        
        type_map = {'1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6}
        resource_type = type_map[type_choice]
        
        # Common fields
        title = self._get_input("Title: ")
        author = self._get_input("Author(s): ")
        isbn = self._get_input("ISBN (optional): ", required=False)
        genre = self._get_input("Genre: ")
        category = self._get_input("Category (optional): ", required=False)
        try:
            pages = int(self._get_input("Pages: "))
        except:
            pages = 0
        
        publisher = self._get_input("Publisher: ")
        language = self._get_input("Language [English]: ", required=False) or "English"
        edition = self._get_input("Edition [1st]: ", required=False) or "1st"
        pub_date = self._get_input("Publication Date (YYYY-MM-DD): ")
        
        print("\nFormat:")
        format_options = ["Physical", "Digital", "Audio", "Video"]
        format_choice = self._get_choice("Choose format: ", format_options)
        format_map = {'1': 0, '2': 1, '3': 2, '4': 3}
        resource_format = format_map[format_choice]
        
        location = ""
        if resource_format == 0:  # Physical
            location = self._get_input("Shelf Location (e.g., A1-2-3): ")
        try:
            copies = int(self._get_input("Number of copies [1]: ", required=False) or "1")
        except:
            copies = 1
        
        description = self._get_input("Description (optional): ", required=False)
        
        # Get next ID
        existing = self.engine.get_all_books()
        new_id = max([b.id for b in existing], default=0) + 1
        resource_data = {
            'id': new_id,
            'title': title,
            'author': author,
            'isbn': isbn,
            'genre': genre,
            'category': category,
            'pages': pages,
            'publisher': publisher,
            'language': language,
            'edition': edition,
            'publication_date': pub_date,
            'type': resource_type,
            'format': resource_format,
            'condition': 1,  # New
            'location': location,
            'status': 0,  # Available
            'copies': copies,
            'total_copies': copies,
            'description': description,
            'date_added': datetime.now().strftime("%Y-%m-%d"),
            'last_updated': datetime.now().strftime("%Y-%m-%d")
        }
        from src.models.book import ResourceFactory
        resource = ResourceFactory.create_from_csv_row(resource_data)
        
        if self.engine.save_book(resource):
            self._print_success(f"Resource added successfully with ID: {new_id}")
            self.logger.log_resource_creation(self.current_user.user_id, new_id, title)
        else:
            self._print_error("Failed to add resource")
        
        self._pause()

    def _edit_resource(self):
        self._print_header("✏️ EDIT RESOURCE")
        try:
            book_id = int(self._get_input("Enter Resource ID to edit: "))
        except:
            self._print_error("Invalid ID")
            self._pause()
            return
        
        book = self.engine.load_book(book_id)
        if not book:
            self._print_error("Resource not found")
            self._pause()
            return
        
        print(f"\nEditing: {book.title}")
        print("Leave blank to keep current value\n")
        
        updates = {}
        title = self._get_input(f"Title [{book.title}]: ", required=False)
        if title:
            updates['title'] = title
        
        author = self._get_input(f"Author [{book.author}]: ", required=False)
        if author:
            updates['author'] = author
        
        genre = self._get_input(f"Genre [{book.genre}]: ", required=False)
        if genre:
            updates['genre'] = genre
        if updates:
            book.update_details(**updates)
            if self.engine.save_book(book):
                self._print_success("Resource updated successfully")
                self.logger.log_resource_update(self.current_user.user_id, book_id, updates)
            else:
                self._print_error("Failed to save updates")
        else:
            self._print_info("No changes made")
        
        self._pause()

    def _delete_resource(self):
        self._print_header("🗑️ DELETE/ARCHIVE RESOURCE")
        
        try:
            book_id = int(self._get_input("Enter Resource ID to delete: "))
        except:
            self._print_error("Invalid ID")
            self._pause()
            return
        
        book = self.engine.load_book(book_id)
        if not book:
            self._print_error("Resource not found")
            self._pause()
            return
        
        print(f"\nResource: {book.title}")
        print("\nOptions:")
        print("  1. Archive (soft delete)")
        print("  2. Permanently delete")
        print("  3. Cancel")
        choice = self._get_choice("Choose option: ", ["Archive", "Permanently delete", "Cancel"])
        
        if choice == '3':
            return
        elif choice == '1':
            book.archive()
            self.engine.save_book(book)
            self._print_success("Resource archived")
            self.logger.log_resource_deletion(self.current_user.user_id, book_id, book.title)
        elif choice == '2':
            confirm = self._get_input("Type 'DELETE' to confirm permanent deletion: ")
            if confirm == 'DELETE':
                # Implement permanent deletion in storage
                self._print_success("Resource permanently deleted")
                self.logger.log_resource_deletion(self.current_user.user_id, book_id, book.title)
            else:
                self._print_info("Deletion cancelled")
        
        self._pause()

    def _add_copy(self):
        self._print_header("➕ ADD COPY")
        try:
            book_id = int(self._get_input("Enter Resource ID: "))
        except:
            self._print_error("Invalid ID")
            self._pause()
            return
        
        book = self.engine.load_book(book_id)
        if not book:
            self._print_error("Resource not found")
            self._pause()
            return
        
        if book.format != 0:
            self._print_error("Cannot add physical copies to digital resources")
            self._pause()
            return
        copy_id = book.add_copy()
        if copy_id:
            self.engine.save_book(book)
            self._print_success(f"Copy added: {copy_id}")
        else:
            self._print_error("Failed to add copy")
        
        self._pause()

    def _remove_copy(self):
        self._print_header("➖ REMOVE COPY")
        
        copy_id = self._get_input("Enter Copy ID to remove: ")
        
        # Find which resource this copy belongs to
        books = self.engine.get_all_books()
        target_book = None
        for book in books:
            for copy in book.physical_copies:
                if copy.copy_id == copy_id:
                    target_book = book
                    break
            if target_book:
                break
        
        if not target_book:
            self._print_error("Copy not found")
            self._pause()
            return
        if target_book.remove_copy(copy_id):
            self.engine.save_book(target_book)
            self._print_success("Copy removed")
        else:
            self._print_error("Failed to remove copy")
        
        self._pause()

    def _updatea_location(self):
        self._print_header("📍 UPDATE LOCATION")
        
        try:
            book_id = int(self._get_input("Enter Resource ID: "))
        except:
            self._print_error("Invalid ID")
            self._pause()
            return
        
        book = self.engine.load_book(book_id)
        if not book:
            self._print_error("Resource not found")
            self._pause()
            return
        
        print(f"\nCurrent location: {book.get_location()}")
        new_location = self._get_input("New location: ")
        book.set_location(new_location)
        self.engine.save_book(book)
        self._print_success("Location updated")
        self._pause()

    def _update_condition(self):
        self._print_header("🔧 UPDATE CONDITION")
        print("Update condition for:")
        print("  1. Entire resource")
        print("  2. Specific copy")
        
        choice = self._get_choice("Choose option: ", ["Entire resource", "Specific copy"])
        
        condition_map = {
            '1': "New (1)",
            '2': "Good (2)",
            '3': "Damaged (3)",
            '4': "Lost (4)",
            '5': "Repair (5)"
        }
        
        print("\nSelect new condition:")
        for key, value in condition_map.items():
            print(f"  {key}. {value}")
        
        try:
            condition = int(self._get_input("Condition (1-5): "))
            if condition not in [1, 2, 3, 4, 5]:
                self._print_error("Invalid condition")
                self._pause()
                return
        except:
            self._print_error("Invalid input")
            self._pause()
            return
        
        if choice == '1':
            try:
                book_id = int(self._get_input("Enter Resource ID: "))
                book = self.engine.load_book(book_id)
                if book:
                    book.update_condition(new_condition=condition)
                    self.engine.save_book(book)
                    self._print_success("Condition updated")
                else:
                    self._print_error("Resource not found")
            except:
                self._print_error("Invalid ID")
        else:
            copy_id = self._get_input("Enter Copy ID: ")
            books = self.engine.get_all_books()
            updated = False
            for book in books:
                for copy in book.physical_copies:
                    if copy.copy_id == copy_id:
                        book.update_condition(copy_id=copy_id, new_condition=condition)
                        self.engine.save_book(book)
                        updated = True
                        break
                if updated:
                    break
            
            if updated:
                self._print_success("Copy condition updated")
            else:
                self._print_error("Copy not found")
        self._pause()

    def _view_all_resources(self):
        resources = self.engine.get_all_books()
        self._print_header("📚 ALL RESOURCES")
        
        headers = ["ID", "Title", "Author", "Type", "Format", "Available"]
        rows = []
        for resource in resources[:30]:
            rows.append([
                resource.id,
                resource.title[:25] + "..." if len(resource.title) > 25 else resource.title,
                resource.author[:15] + "..." if len(resource.author) > 15 else resource.author,
                resource.type_of_resource(),
                resource.format_of_resource(),
                f"{resource.copies}/{resource.total_copies}"
            ])
        self._print_table(headers, rows)
        if len(resource) > 30:
            self._print_info(f"Showing 30 of {len(resources)} resources")
        self._pause()

    def _manage_fines(self):
        self._print_header("💰 FINE MANAGEMENT")
        while True:
            options = [
                "View All Pending Fines",
                "View User Fines",
                "Waive Fine",
                "Clear User Fines",
                "Back"
            ]
            choice = self._get_choice("Select option: ", options)
            if choice == '0' or choice == '5':
                break
            elif choice == '1':
                self._view_pending_fines()
            elif choice == '2':
                self._view_user_fines()
            elif choice == '3':
                self._waive_fine()
            elif choice == '4':
                self._clear_user_fines()

    def _view_pending_fines(self):
        pending = self.engine.storage.get_all_pending_fines()
        self._print_header("⏳ PENDING FINES")
        if pending:
            headers = ["Fine ID", "User ID", "Amount", "Reason", "Issued", "Due"]
            rows = []
            for fine in pending[:30]:
                rows.append([
                    fine['fine_id'][:8] + "...",
                    fine['user_id'][:8] + "...",
                    f"${float(fine['amount']):.2f}",
                    fine['reason'],
                    fine['issued_date'],
                    fine['due_date']
                ])
            self._print_table(headers, rows)
        else:
            self._print_info("No pending fines")
        self._pause()

    def _view_user_fines(self):
        user_id = self._get_input("Enter User ID: ")
        report = self.engine.get_fines_report(user_id)
        if 'error' in report:
            self._print_error(report['error'])
        else:
            self._print_header(f"💰 FINES - {report['user_name']}")
            print(f"Total pending: ${report['total_pending']:.2f}")
            print(f"Total paid: ${report['total_paid']:.2f}")
            print(f"Total waived: ${report['total_waived']:.2f}")
            print()
        if report['fines']:
                headers = ["Fine ID", "Amount", "Reason", "Issued", "Status"]
                rows = []
                for fine in report['fines']:
                    rows.append([
                        fine['fine_id'][:8] + "...",
                        f"${fine['amount']:.2f}",
                        fine['reason'],
                        fine['issued_date'],
                        fine['status']
                    ])
                self._print_table(headers, rows)
        self._pause()

    def _waive_fine(self):
        self._print_header("💸 WAIVE FINE")
        fine_id = self._get_input("Enter Fine ID to waive: ")
        result = self.engine.waive_user_fine(self.current_user.user_id, fine_id)
        if result['success']:
            self._print_success(result['message'])
        else:
            self._print_error(result['message'])
        self._pause()

    def _clear_user_fines(self):
        self._print_header("🧹 CLEAR USER FINES")
        user_id = self._get_input("Enter User ID: ")
        result = self.engine.clear_user_fines(self.current_user.user_id, user_id)
        if result['success']:
            self._print_success(result['message'])
        else:
            self._print_error(result["message"])
        self._pause()

    def _view_reports(self):
        self._print_header("📊 SYSTEM REPORTS")
        report = self.engine.get_system_report()
        print(f"Report generated: {report['timestamp']}\n")
        print("👥 USER STATISTICS")
        print(f"  Total Users: {report['users']['total']}")
        print(f"  Active Users: {report['users']['active']}")
        print(f"  Blacklisted: {report['users']['blacklisted']}")
        print(f"  By Role:")
        for role, count in report['users']['by_role'].items():
            print(f"    • {role.title()}: {count}")
        print()
        print("📚 RESOURCE STATISTICS")
        print(f"  Total Resources: {report['resources']['total']}")
        print(f"  Available: {report['resources']['available']}")
        print(f"  Checked Out: {report['resources']['checked_out']}")
        print(f"  By Type:")
        for type_name, count in report['resources']['by_type'].items():
            print(f"    • {type_name}: {count}")
        print()
        print("💳 TRANSACTION STATISTICS")
        print(f"  Active Borrowings: {report['transactions']['active_borrowings']}")
        print(f"  Total Fines Pending: ${report['transactions']['total_fines_pending']:.2f}")
        self._pause()

    def _system_settings(self):
        self._print_header("⚙️ SYSTEM SETTINGS")
        print("It will availabe soon")
        self._pause()

    def _backup_restore(self):
        self._print_header("💾 BACKUP & RESTORE")
        while True:
            options = [
                "Create Backup",
                "Restore from Backup",
                "View Backup History",
                "Back"
            ]
            choice = self._get_choice("Select option: ", options)
            if choice == '0' or choice == '4':
                break
            elif choice == '1':
                self._create_backup()
            elif choice == '2':
                self._restore_backup()
            elif choice == '3':
                self._view_backups()
    def _create_backup(self):
        self._print_header("💾 CREATE BACKUP")
        backup_path = self.engine.storage.backup_data()
        if backup_path:
            stats = self.engine.storage.get_statistics()
            self._print_success(f"Backup created successfully")
            self._print_info(f"Location: {backup_path}")
            self._print_info(f"Backed up: {stats['users']} users, {stats['resources']} resources")
            self.logger.log_backup(self.current_user.user_id, backup_path, 0)
        else:
            self._print_error("Backup failed")
        self._pause()

    def _restore_backup(self):
        self._print_header("↩️ RESTORE BACKUP")
        backup_dir = os.path.join("data", "backups")
        if not os.path.exists(backup_dir):
            self._print_error("No backups found")
            self._pause()
            return
        backups = sorted(os.listdir(backup_dir), reverse=True)
        if not backups:
            self._print_error("No backups found")
            self._pause()
            return
        print("Available backups:")
        for i, backup in enumerate(backups[:10], 1):
            backup_path = os.path.join(backup_dir, backup)
            created = datetime.fromtimestamp(os.path.getctime(backup_path))
            print(f"  {i}. {backup} ({created.strftime('%Y-%m-%d %H:%M:%S')})")
        try:
            choice = int(self._get_input("\nSelect backup to restore (0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(backups[:10]):
                backup_name = backups[choice-1]
                backup_path = os.path.join(backup_dir, backup_name)
                
                confirm = self._get_input(f"Restore from {backup_name}? This will overwrite current data. Type 'RESTORE' to confirm: ")
                if confirm == 'RESTORE':
                    if self.engine.storage.restore_from_backup(backup_path):
                        self._print_success("System restored successfully")
                        self.logger.log_restore(self.current_user.user_id, backup_path)
                    else:
                        self._print_error("Restore failed")
                else:
                    self._print_info("Restore cancelled")
        except:
            self._print_error("Invalid choice")
        self._pause()

    def _view_backups(self):
        self._print_header("📋 BACKUP HISTORY")
        backup_dir = os.path.join("data", "backups")
        if not os.path.exists(backup_dir):
            self._print_info("No backups found")
            self._pause()
            return
        backups = sorted(os.listdir(backup_dir), reverse=True)
        if backups:
            headers = ["Backup", "Date", "Time", "Size"]
            rows = []
            for backup in backups[:20]:
                backup_path = os.path.join(backup_dir, backup)
                created = datetime.fromtimestamp(os.path.getctime(backup_path))
                size = sum(os.path.getsize(os.path.join(backup_path, f)) 
                          for f in os.listdir(backup_path) 
                          if os.path.isfile(os.path.join(backup_path, f)))
                size_str = f"{size/1024:.1f} KB" if size < 1024*1024 else f"{size/(1024*1024):.1f} MB"
                rows.append([
                    backup[:15] + "..." if len(backup) > 15 else backup,
                    created.strftime("%Y-%m-%d"),
                    created.strftime("%H:%M:%S"),
                    size_str
                ])
            self._print_table(headers, rows)
        else:
            self._print_info("No backups found")

        self._pause()

    def _exit_system(self):
        self._print_header("👋 GOODBYE!")
        session_duration = datetime.now() - self.session_start
        hours, remainder = divmod(session_duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 30)
        self._print_info(f"Session duration: {hours}h {minutes}m {seconds}s")
        self._print_info("Thank you for using the APP!")
        self.logger.log_system_shutdown()
        print("\n")
        self._get_input("Press Enter to exit...", required=False)
        sys.exit(0)


def main():
    try:
        cli = LibraryCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n👋 GoodBye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
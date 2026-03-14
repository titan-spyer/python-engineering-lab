"""
Test cases for the Validator class.
Tests all validation rules and business logic.
"""

import pytest
from datetime import datetime, timedelta
from src.models.user import UserRole, UserStatus, BorrowingRecord
from src.models.book import Resource, ResourceType, FormatType


class TestValidatorEmail:
    """Test email validation."""
    
    def test_valid_emails(self, validator):
        """Test valid email addresses."""
        valid_emails = [
            'user@example.com',
            'user.name@example.com',
            'user+label@example.com',
            'user@subdomain.example.com',
            'user@example.co.uk',
            '123@example.com'
        ]
        
        for email in valid_emails:
            is_valid, _ = validator.validate_email(email)
            assert is_valid is True, f"Email {email} should be valid"
    
    def test_invalid_emails(self, validator):
        """Test invalid email addresses."""
        invalid_emails = [
            'invalid',
            'user@',
            '@example.com',
            'user@.com',
            'user@example.',
            'user name@example.com',
            'user@exam ple.com',
            ''
        ]
        
        for email in invalid_emails:
            is_valid, _ = validator.validate_email(email)
            assert is_valid is False, f"Email {email} should be invalid"


class TestValidatorPassword:
    """Test password strength validation."""
    
    def test_strong_passwords(self, validator):
        """Test strong passwords."""
        strong_passwords = [
            'Test@1234',
            'Password1!',
            'Strong#Pass2023',
            'C0mpl3x!P@ss',
            'Aa1!Bb2@Cc3#'
        ]
        
        for password in strong_passwords:
            is_valid, _ = validator.validate_password_strength(password)
            assert is_valid is True, f"Password {password} should be strong"
    
    def test_weak_passwords(self, validator):
        """Test weak passwords."""
        weak_passwords = [
            'short',  # Too short
            'onlylowercase',  # No uppercase, no digits, no special
            'ONLYUPPERCASE',  # No lowercase, no digits, no special
            'NoDigits!',  # No digits
            'NoSpecial1',  # No special
            '12345678',  # Only digits
            ''  # Empty
        ]
        
        for password in weak_passwords:
            is_valid, message = validator.validate_password_strength(password)
            assert is_valid is False, f"Password {password} should be weak"
            assert message != "Password meets strength requirements"


class TestValidatorUsername:
    """Test username validation."""
    
    def test_valid_usernames(self, validator):
        """Test valid usernames."""
        valid_usernames = [
            'user123',
            'john_doe',
            'jane-doe',
            'User.Name',
            'a1b2c3',
            'test_user_123'
        ]
        
        for username in valid_usernames:
            is_valid, _ = validator.validate_username(username)
            assert is_valid is True, f"Username {username} should be valid"
    
    def test_invalid_usernames(self, validator):
        """Test invalid usernames."""
        invalid_usernames = [
            'ab',  # Too short
            'a' * 30,  # Too long
            '123start',  # Starts with number
            'user name',  # Contains space
            'user@name',  # Contains special
            ''  # Empty
        ]
        
        for username in invalid_usernames:
            is_valid, _ = validator.validate_username(username)
            assert is_valid is False, f"Username {username} should be invalid"


class TestValidatorPhone:
    """Test phone number validation."""
    
    def test_valid_phones(self, validator):
        """Test valid phone numbers."""
        valid_phones = [
            '1234567890',
            '9876543210',
            '555-123-4567',
            '(555) 123-4567',
            '+1-555-123-4567'
        ]
        
        for phone in valid_phones:
            is_valid, _ = validator.validate_phone(phone)
            assert is_valid is True, f"Phone {phone} should be valid"
    
    def test_invalid_phones(self, validator):
        """Test invalid phone numbers."""
        invalid_phones = [
            '12345',  # Too short
            '12345678901',  # Too long
            'abcdefghij',  # Not digits
            '123-abc-7890',  # Mixed
            ''  # Empty
        ]
        
        for phone in invalid_phones:
            is_valid, _ = validator.validate_phone(phone)
            assert is_valid is False, f"Phone {phone} should be invalid"


class TestValidatorBorrowing:
    """Test borrowing validation rules."""
    
    def test_can_user_borrow_active_user(self, validator, sample_student, sample_book):
        """Test that active user can borrow."""
        user, _ = sample_student
        can_borrow, message = validator.can_user_borrow(user, sample_book)
        
        assert can_borrow is True
        assert message == "Can borrow"
    
    def test_can_user_borrow_blacklisted(self, validator, sample_student, sample_book):
        """Test that blacklisted user cannot borrow."""
        user, _ = sample_student
        user.status = UserStatus.BLACKLISTED.value
        
        can_borrow, message = validator.can_user_borrow(user, sample_book)
        
        assert can_borrow is False
        assert 'blacklisted' in message.lower()
    
    def test_can_user_borrow_limit_reached(self, validator, sample_student, sample_book):
        """Test that user cannot borrow when limit is reached."""
        user, _ = sample_student
        limits = user.get_borrowing_limits()
        
        # Simulate reaching limit
        from src.models.user import BorrowingRecord
        for i in range(limits['max_books']):
            record = BorrowingRecord(
                user_id=user.user_id,
                record_id=f"test{i}",
                resource_id=100 + i,
                copy_id=f"copy{i}",
                borrow_date=datetime.now().strftime("%Y-%m-%d"),
                due_date=(datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
                status="active"
            )
            user.current_borrowings.append(record)
        
        can_borrow, message = validator.can_user_borrow(user, sample_book)
        
        assert can_borrow is False
        assert 'limit' in message.lower()
    
    def test_can_user_borrow_restricted_category(self, validator, sample_student, sample_book):
        """Test that user cannot borrow from restricted category."""
        user, _ = sample_student
        sample_book.category = 'rare'  # Restricted for students
        
        can_borrow, message = validator.can_user_borrow(user, sample_book)
        
        assert can_borrow is False
        assert 'restricted' in message.lower()
    
    def test_can_user_borrow_excessive_fines(self, validator, sample_student, sample_book):
        """Test that user cannot borrow with excessive fines."""
        user, _ = sample_student
        limits = user.get_borrowing_limits()
        
        # Add fines exceeding limit
        from src.models.user import FineRecord
        user.fines.append(
            FineRecord(
                fine_id="test1",
                user_id=user.user_id,
                record_id="record1",
                amount=limits['max_fines_allowed'] + 10,
                reason="overdue",
                issued_date=datetime.now().strftime("%Y-%m-%d"),
                due_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                status="pending"
            )
        )
        
        can_borrow, message = validator.can_user_borrow(user, sample_book)
        
        assert can_borrow is False
        assert 'fines' in message.lower()
    
    def test_can_user_borrow_unavailable_book(self, validator, sample_student, sample_book):
        """Test that user cannot borrow unavailable book."""
        user, _ = sample_student
        sample_book.copies = 0
        
        can_borrow, message = validator.can_user_borrow(user, sample_book)
        
        assert can_borrow is False
        assert 'available' in message.lower()
    
    def test_can_renew_record_success(self, validator, sample_student):
        """Test that active record can be renewed."""
        user, _ = sample_student
        
        record = BorrowingRecord(
            user_id=user.user_id,
            record_id="test1",
            resource_id=1,
            copy_id="copy1",
            borrow_date=datetime.now().strftime("%Y-%m-%d"),
            due_date=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            renewal_count=0,
            status="active"
        )
        
        can_renew, message = validator.can_renew_record(user, record)
        
        assert can_renew is True
        assert message == "Can renew"
    
    def test_can_renew_record_inactive_user(self, validator, sample_student):
        """Test that inactive user cannot renew."""
        user, _ = sample_student
        user.status = UserStatus.DEACTIVATED.value
        
        record = BorrowingRecord(
            user_id=user.user_id,
            record_id="test1",
            resource_id=1,
            copy_id="copy1",
            borrow_date=datetime.now().strftime("%Y-%m-%d"),
            due_date=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            renewal_count=0,
            status="active"
        )
        
        can_renew, message = validator.can_renew_record(user, record)
        
        assert can_renew is False
        assert 'not active' in message.lower()
    
    def test_can_renew_record_overdue(self, validator, sample_student):
        """Test that overdue record cannot be renewed."""
        user, _ = sample_student
        
        record = BorrowingRecord(
            user_id=user.user_id,
            record_id="test1",
            resource_id=1,
            copy_id="copy1",
            borrow_date=datetime.now().strftime("%Y-%m-%d"),
            due_date=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),  # Overdue
            renewal_count=0,
            status="active"
        )
        
        can_renew, message = validator.can_renew_record(user, record)
        
        assert can_renew is False
        assert 'overdue' in message.lower()
    
    def test_can_renew_record_max_reached(self, validator, sample_student):
        """Test that record cannot be renewed beyond max."""
        user, _ = sample_student
        max_renewals = user.get_borrowing_limits()['max_renewals']
        
        record = BorrowingRecord(
            user_id=user.user_id,
            record_id="test1",
            resource_id=1,
            copy_id="copy1",
            borrow_date=datetime.now().strftime("%Y-%m-%d"),
            due_date=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            renewal_count=max_renewals,  # Already at max
            status="active"
        )
        
        can_renew, message = validator.can_renew_record(user, record)
        
        assert can_renew is False
        assert 'maximum' in message.lower() or 'limit' in message.lower()
    
    def test_can_return_book_success(self, validator, sample_student):
        """Test that user can return a book they borrowed."""
        user, _ = sample_student
        
        record = BorrowingRecord(
            user_id=user.user_id,
            record_id="test1",
            resource_id=1,
            copy_id="copy1",
            borrow_date=datetime.now().strftime("%Y-%m-%d"),
            due_date=(datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
            status="active"
        )
        user.current_borrowings.append(record)
        
        can_return, message, found_record = validator.can_return_book(user, "copy1")
        
        assert can_return is True
        assert found_record is not None
        assert found_record.copy_id == "copy1"
    
    def test_can_return_book_not_found(self, validator, sample_student):
        """Test returning a book not borrowed."""
        user, _ = sample_student
        
        can_return, message, record = validator.can_return_book(user, "nonexistent")
        
        assert can_return is False
        assert record is None
        assert 'no active' in message.lower()


class TestValidatorResource:
    """Test resource validation."""
    
    def test_is_book_available(self, validator, sample_book):
        """Test book availability check."""
        # Available
        available, message = validator.is_book_available(sample_book, 1)
        assert available is True
        
        # Multiple copies
        available, message = validator.is_book_available(sample_book, 2)
        assert available is True
        
        # Not enough copies
        available, message = validator.is_book_available(sample_book, 4)
        assert available is False
    
    def test_validate_resource_data_valid(self, validator):
        """Test valid resource data."""
        data = {
            'title': 'Test Book',
            'author': 'Test Author',
            'pages': 200,
            'publication_date': '2023-01-01',
            'isbn': '978-1234567890'
        }
        
        is_valid, message = validator.validate_resource_data(data)
        assert is_valid is True
    
    def test_validate_resource_data_invalid(self, validator):
        """Test invalid resource data."""
        # Missing required field
        data = {
            'title': 'Test Book',
            'pages': 200
            # Missing author
        }
        is_valid, message = validator.validate_resource_data(data)
        assert is_valid is False
        assert 'missing' in message.lower()
        
        # Invalid pages
        data = {
            'title': 'Test Book',
            'author': 'Test Author',
            'pages': 'abc',
            'publication_date': '2023-01-01'
        }
        is_valid, message = validator.validate_resource_data(data)
        assert is_valid is False
        
        # Invalid ISBN
        data = {
            'title': 'Test Book',
            'author': 'Test Author',
            'pages': 200,
            'publication_date': '2023-01-01',
            'isbn': 'invalid-isbn'
        }
        is_valid, message = validator.validate_resource_data(data)
        assert is_valid is False
        assert 'isbn' in message.lower()
    
    def test_validate_copy_data_valid(self, validator):
        """Test valid copy data."""
        data = {
            'copy_id': '1-001',
            'resource_id': 1,
            'barcode': 'BAR-1-001',
            'condition': 1
        }
        
        is_valid, message = validator.validate_copy_data(data)
        assert is_valid is True
    
    def test_validate_copy_data_invalid(self, validator):
        """Test invalid copy data."""
        # Missing required field
        data = {
            'copy_id': '1-001'
            # Missing resource_id
        }
        is_valid, message = validator.validate_copy_data(data)
        assert is_valid is False
        assert 'missing' in message.lower()
        
        # Invalid condition
        data = {
            'copy_id': '1-001',
            'resource_id': 1,
            'barcode': 'BAR-1-001',
            'condition': 99  # Invalid
        }
        is_valid, message = validator.validate_copy_data(data)
        assert is_valid is False
        assert 'condition' in message.lower()


class TestValidatorPermissions:
    """Test permission checks."""
    
    def test_role_checks(self, validator):
        """Test role-based permission checks."""
        from src.models.user import User
        
        # Create users with different roles
        class MockUser(User):
            def get_role_name(self): return "Mock"
            def get_borrowing_limits(self): return {}
            def __str__(self): return ""
        
        student = MockUser(
            user_id="student",
            username="student",
            password_hash="hash",
            email="student@test.com",
            full_name="Student",
            role=UserRole.STUDENT.value
        )
        
        faculty = MockUser(
            user_id="faculty",
            username="faculty",
            password_hash="hash",
            email="faculty@test.com",
            full_name="Faculty",
            role=UserRole.FACULTY.value
        )
        
        librarian = MockUser(
            user_id="librarian",
            username="librarian",
            password_hash="hash",
            email="librarian@test.com",
            full_name="Librarian",
            role=UserRole.LIBRARIAN.value
        )
        
        admin = MockUser(
            user_id="admin",
            username="admin",
            password_hash="hash",
            email="admin@test.com",
            full_name="Admin",
            role=UserRole.ADMIN.value
        )
        
        # Test is_admin
        assert validator.is_admin(admin) is True
        assert validator.is_admin(librarian) is False
        assert validator.is_admin(faculty) is False
        assert validator.is_admin(student) is False
        
        # Test is_librarian
        assert validator.is_librarian(librarian) is True
        assert validator.is_librarian(admin) is False
        
        # Test is_librarian_or_admin
        assert validator.is_librarian_or_admin(librarian) is True
        assert validator.is_librarian_or_admin(admin) is True
        assert validator.is_librarian_or_admin(faculty) is False
        
        # Test can_waive_fines
        assert validator.can_waive_fines(librarian) is True
        assert validator.can_waive_fines(admin) is True
        assert validator.can_waive_fines(faculty) is False
        
        # Test can_override_policies
        assert validator.can_override_policies(admin) is True
        assert validator.can_override_policies(librarian) is False


class TestValidatorDates:
    """Test date validation."""
    
    def test_validate_date_format(self, validator):
        """Test date format validation."""
        # Valid dates
        assert validator.validate_date_format("2023-01-01")[0] is True
        assert validator.validate_date_format("2023-12-31")[0] is True
        
        # Invalid dates
        assert validator.validate_date_format("01-01-2023")[0] is False
        assert validator.validate_date_format("2023/01/01")[0] is False
        assert validator.validate_date_format("")[0] is False
    
    def test_validate_due_date(self, validator):
        """Test due date validation."""
        future_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        past_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        
        # Valid future date
        is_valid, _ = validator.validate_due_date(future_date)
        assert is_valid is True
        
        # Invalid past date
        is_valid, _ = validator.validate_due_date(past_date)
        assert is_valid is False
        
        # With borrow date
        borrow_date = datetime.now().strftime("%Y-%m-%d")
        is_valid, _ = validator.validate_due_date(future_date, borrow_date)
        assert is_valid is True
        
        # Due before borrow
        is_valid, _ = validator.validate_due_date(past_date, borrow_date)
        assert is_valid is False


class TestValidatorSearch:
    """Test search query validation."""
    
    def test_validate_search_query_valid(self, validator):
        """Test valid search queries."""
        valid_queries = [
            "python",
            "machine learning",
            "test-123",
            "a" * 50
        ]
        
        for query in valid_queries:
            is_valid, _ = validator.validate_search_query(query)
            assert is_valid is True
    
    def test_validate_search_query_invalid(self, validator):
        """Test invalid search queries."""
        invalid_queries = [
            "",  # Empty
            "a",  # Too short
            "SELECT * FROM users",  # SQL injection attempt
            "DROP TABLE books",  # SQL injection attempt
            "'; DELETE FROM users; --"  # SQL injection
        ]
        
        for query in invalid_queries:
            is_valid, _ = validator.validate_search_query(query)
            assert is_valid is False


class TestValidatorFines:
    """Test fine validation."""
    
    def test_validate_fine_amount(self, validator):
        """Test fine amount validation."""
        # Valid amounts
        assert validator.validate_fine_amount(0)[0] is True
        assert validator.validate_fine_amount(10.50)[0] is True
        assert validator.validate_fine_amount(5000)[0] is True
        
        # Invalid amounts
        assert validator.validate_fine_amount(-5)[0] is False
        assert validator.validate_fine_amount(5001)[0] is False
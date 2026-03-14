"""
Test cases for the LibraryEngine class.
Covers user registration, login, book operations, and transactions.
"""

import pytest
from datetime import datetime, timedelta
from src.models.user import UserRole, UserStatus
from src.models.book import StatusType


class TestEngineUserRegistration:
    """Test user registration functionality."""
    
    def test_user_registration_success(self, engine, sample_user_data):
        """Test successful user registration."""
        result = engine.register_user(
            role=UserRole.STUDENT.value,
            **sample_user_data
        )
        
        assert result['success'] is True
        assert 'user_id' in result
        assert result['status'] == 'pending_activation'
        
        # Verify user was saved
        user = engine.load_user(result['user_id'])
        assert user is not None
        assert user.username == sample_user_data['username']
        assert user.email == sample_user_data['email']
        assert user.role == UserRole.STUDENT.value
        assert user.status == UserStatus.PENDING_ACTIVATION.value
    
    def test_user_registration_duplicate_username(self, engine, sample_user_data):
        """Test registration with duplicate username."""
        # Register first user
        result1 = engine.register_user(
            role=UserRole.STUDENT.value,
            **sample_user_data
        )
        assert result1['success'] is True
        
        # Try to register with same username
        result2 = engine.register_user(
            role=UserRole.STUDENT.value,
            **sample_user_data
        )
        
        assert result2['success'] is False
        assert 'already taken' in result2['message'].lower()
    
    def test_user_registration_invalid_email(self, engine, sample_user_data):
        """Test registration with invalid email."""
        sample_user_data['email'] = 'invalid-email'
        
        result = engine.register_user(
            role=UserRole.STUDENT.value,
            **sample_user_data
        )
        
        assert result['success'] is False
        assert 'invalid email' in result['message'].lower()
    
    def test_user_registration_weak_password(self, engine, sample_user_data):
        """Test registration with weak password."""
        sample_user_data['password'] = 'weak'
        
        result = engine.register_user(
            role=UserRole.STUDENT.value,
            **sample_user_data
        )
        
        assert result['success'] is False
        assert 'password' in result['message'].lower()
    
    def test_user_registration_missing_fields(self, engine):
        """Test registration with missing required fields."""
        result = engine.register_user(
            role=UserRole.STUDENT.value,
            username='testuser'
            # Missing other fields
        )
        
        assert result['success'] is False
        assert 'missing required field' in result['message'].lower()


class TestEngineUserLogin:
    """Test user login functionality."""
    
    def test_user_login_success(self, engine, sample_student):
        """Test successful user login."""
        user, _ = sample_student
        last_login_before = user.last_login
        
        # Verify password
        assert user.verify_password('Test@1234') is True
        
        # Update last login
        user.update_last_login()
        engine.save_user(user)
        
        # Reload and verify
        reloaded = engine.load_user(user.user_id)
        assert reloaded.last_login != last_login_before
    
    def test_user_login_wrong_password(self, engine, sample_student):
        """Test login with wrong password."""
        user, _ = sample_student
        assert user.verify_password('wrongpassword') is False
    
    def test_user_login_inactive(self, engine, sample_user_data):
        """Test login with inactive account."""
        # Register but don't activate
        result = engine.register_user(
            role=UserRole.STUDENT.value,
            **sample_user_data
        )
        assert result['success'] is True
        
        user = engine.load_user(result['user_id'])
        assert user.status == UserStatus.PENDING_ACTIVATION.value
        assert user.verify_password(sample_user_data['password']) is True


class TestEngineBookOperations:
    """Test book borrowing, returning, and renewing."""
    
    def test_issue_book_success(self, engine, sample_student, sample_book):
        """Test successful book issuance."""
        user, admin = sample_student
        
        # Issue book
        result = engine.issue_book_to_user(user.user_id, sample_book.id)
        
        assert result['success'] is True
        assert 'copy_id' in result
        assert 'due_date' in result
        
        # Reload user and verify
        updated_user = engine.load_user(user.user_id)
        assert len(updated_user.current_borrowings) == 1
        
        # Reload book and verify
        updated_book = engine.load_book(sample_book.id)
        assert updated_book.copies == sample_book.copies - 1
    
    def test_issue_book_unavailable(self, engine, sample_student, sample_book):
        """Test issuing a book with no available copies."""
        user, admin = sample_student
        
        # Borrow all copies
        for _ in range(sample_book.copies):
            engine.issue_book_to_user(user.user_id, sample_book.id)
        
        # Try to borrow again
        result = engine.issue_book_to_user(user.user_id, sample_book.id)
        
        assert result['success'] is False
        assert 'no available copies' in result['message'].lower()
    
    def test_issue_book_exceed_limit(self, engine, sample_student, sample_book):
        """Test issuing beyond user's borrowing limit."""
        user, admin = sample_student
        limit = user.get_borrowing_limits()['max_books']
        
        # Create additional books
        from src.models.book import ResourceFactory
        for i in range(limit + 1):
            book_data = {
                'id': 100 + i,
                'title': f'Test Book {i}',
                'author': 'Test Author',
                'genre': 'fiction',
                'pages': 200,
                'publisher': 'Test Publisher',
                'type': 1,
                'format': 0,
                'status': 0,
                'copies': 1
            }
            book = ResourceFactory.create_from_csv_row(book_data)
            engine.save_book(book)
            
            if i < limit:
                # Should succeed
                result = engine.issue_book_to_user(user.user_id, book.id)
                assert result['success'] is True
            else:
                # Should fail (exceed limit)
                result = engine.issue_book_to_user(user.user_id, book.id)
                assert result['success'] is False
                assert 'limit' in result['message'].lower()
    
    def test_return_book_success(self, engine, sample_student, sample_book):
        """Test successful book return."""
        user, admin = sample_student
        
        # Issue book
        issue_result = engine.issue_book_to_user(user.user_id, sample_book.id)
        assert issue_result['success'] is True
        copy_id = issue_result['copy_id']
        
        # Return book
        return_result = engine.return_book(user.user_id, sample_book.id, copy_id)
        
        assert return_result['success'] is True
        assert return_result['fine_amount'] == 0.0
        
        # Reload user and verify
        updated_user = engine.load_user(user.user_id)
        assert len(updated_user.current_borrowings) == 0
        
        # Reload book and verify
        updated_book = engine.load_book(sample_book.id)
        assert updated_book.copies == sample_book.copies
    
    def test_return_book_with_fine(self, engine, sample_student, sample_book):
        """Test returning an overdue book with fine."""
        user, admin = sample_student
        
        # Issue book
        issue_result = engine.issue_book_to_user(user.user_id, sample_book.id)
        assert issue_result['success'] is True
        copy_id = issue_result['copy_id']
        
        # Manually set due date to past (bypassing normal flow for testing)
        record = user.current_borrowings[0]
        past_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        record.due_date = past_date
        engine.save_user(user)
        
        # Return book (should calculate fine)
        return_result = engine.return_book(user.user_id, sample_book.id, copy_id)
        
        assert return_result['success'] is True
        assert return_result['fine_amount'] > 0.0
        
        # Verify fine was created
        updated_user = engine.load_user(user.user_id)
        assert len(updated_user.fines) == 1
        assert updated_user.fines[0].amount > 0
        assert updated_user.fines[0].status == "pending"
    
    def test_return_nonexistent_borrowing(self, engine, sample_student, sample_book):
        """Test returning a book that wasn't borrowed."""
        user, admin = sample_student
        
        result = engine.return_book(user.user_id, sample_book.id, "invalid-copy")
        
        assert result['success'] is False
        assert 'no active borrowing' in result['message'].lower()
    
    def test_renew_book_success(self, engine, sample_student, sample_book):
        """Test successful book renewal."""
        user, admin = sample_student
        
        # Issue book
        issue_result = engine.issue_book_to_user(user.user_id, sample_book.id)
        assert issue_result['success'] is True
        copy_id = issue_result['copy_id']
        original_due = issue_result['due_date']
        
        # Renew book
        renew_result = engine.renew_book(user.user_id, copy_id)
        
        assert renew_result['success'] is True
        assert renew_result['new_due_date'] > original_due
        assert renew_result['renewal_count'] == 1
    
    def test_renew_book_max_renewals(self, engine, sample_student, sample_book):
        """Test renewing beyond maximum allowed renewals."""
        user, admin = sample_student
        max_renewals = user.get_borrowing_limits()['max_renewals']
        
        # Issue book
        issue_result = engine.issue_book_to_user(user.user_id, sample_book.id)
        assert issue_result['success'] is True
        copy_id = issue_result['copy_id']
        
        # Renew up to max
        for i in range(max_renewals):
            result = engine.renew_book(user.user_id, copy_id)
            assert result['success'] is True
            assert result['renewal_count'] == i + 1
        
        # Try to renew one more time
        result = engine.renew_book(user.user_id, copy_id)
        assert result['success'] is False
        assert 'renewal limit' in result['message'].lower()
    
    def test_renew_overdue_book(self, engine, sample_student, sample_book):
        """Test renewing an overdue book (should fail)."""
        user, admin = sample_student
        
        # Issue book
        issue_result = engine.issue_book_to_user(user.user_id, sample_book.id)
        assert issue_result['success'] is True
        copy_id = issue_result['copy_id']
        
        # Manually set due date to past
        record = user.current_borrowings[0]
        past_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        record.due_date = past_date
        engine.save_user(user)
        
        # Try to renew
        result = engine.renew_book(user.user_id, copy_id)
        assert result['success'] is False
        assert 'overdue' in result['message'].lower()
    
    def test_issue_digital_book(self, engine, sample_student, sample_digital_book):
        """Test issuing a digital book."""
        user, admin = sample_student
        
        result = engine.issue_book_to_user(user.user_id, sample_digital_book.id)
        
        assert result['success'] is True
        assert 'digital' in result['copy_id']
        
        # Digital books shouldn't decrement copies count
        updated_book = engine.load_book(sample_digital_book.id)
        assert updated_book.copies == sample_digital_book.copies


class TestEngineUserManagement:
    """Test user management operations."""
    
    def test_activate_user(self, engine, sample_user_data):
        """Test user activation."""
        # Register user
        result = engine.register_user(
            role=UserRole.STUDENT.value,
            **sample_user_data
        )
        user_id = result['user_id']
        
        # Create admin for activation
        admin_data = sample_user_data.copy()
        admin_data.update({
            'username': 'admin2',
            'email': 'admin2@library.com'
        })
        admin_result = engine.register_user(
            role=UserRole.ADMIN.value,
            **admin_data
        )
        admin_id = admin_result['user_id']
        admin = engine.load_user(admin_id)
        admin.activate('System')
        engine.save_user(admin)
        
        # Activate user
        activate_result = engine.activate_user(admin_id, user_id)
        
        assert activate_result['success'] is True
        
        # Verify activation
        user = engine.load_user(user_id)
        assert user.status == UserStatus.ACTIVE.value
        assert user.activation_date is not None
    
    def test_deactivate_user(self, engine, sample_student):
        """Test user deactivation."""
        user, admin = sample_student
        
        result = engine.deactivate_user(admin.user_id, user.user_id, "Testing")
        
        assert result['success'] is True
        
        # Verify deactivation
        updated_user = engine.load_user(user.user_id)
        assert updated_user.status == UserStatus.DEACTIVATED.value
        assert updated_user.deactivation_reason == "Testing"
    
    def test_deactivate_user_with_active_borrowings(self, engine, sample_student, sample_book):
        """Test deactivating user with active borrowings (should fail)."""
        user, admin = sample_student
        
        # Issue a book
        engine.issue_book_to_user(user.user_id, sample_book.id)
        
        # Try to deactivate
        result = engine.deactivate_user(admin.user_id, user.user_id, "Testing")
        
        assert result['success'] is False
        assert 'active borrowings' in result['message'].lower()
    
    def test_blacklist_user(self, engine, sample_student):
        """Test blacklisting a user."""
        user, admin = sample_student
        
        result = engine.blacklist_user(admin.user_id, user.user_id, "Violation of rules")
        
        assert result['success'] is True
        
        # Verify blacklist
        updated_user = engine.load_user(user.user_id)
        assert updated_user.status == UserStatus.BLACKLISTED.value
        assert updated_user.times_blacklisted == 1
    
    def test_remove_from_blacklist(self, engine, sample_student):
        """Test removing user from blacklist."""
        user, admin = sample_student
        
        # First blacklist
        engine.blacklist_user(admin.user_id, user.user_id, "Test")
        
        # Then remove
        result = engine.remove_from_blacklist(admin.user_id, user.user_id)
        
        assert result['success'] is True
        
        # Verify removal
        updated_user = engine.load_user(user.user_id)
        assert updated_user.status == UserStatus.ACTIVE.value


class TestEngineFineManagement:
    """Test fine management operations."""
    
    def test_pay_fine(self, engine, sample_student, sample_book):
        """Test paying a fine."""
        user, admin = sample_student
        
        # Create a fine by returning overdue book
        issue_result = engine.issue_book_to_user(user.user_id, sample_book.id)
        copy_id = issue_result['copy_id']
        
        # Set overdue
        record = user.current_borrowings[0]
        past_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        record.due_date = past_date
        engine.save_user(user)
        
        # Return to create fine
        engine.return_book(user.user_id, sample_book.id, copy_id)
        
        # Get the fine ID
        updated_user = engine.load_user(user.user_id)
        fine_id = updated_user.fines[0].fine_id
        
        # Pay the fine
        result = engine.pay_fine(user.user_id, fine_id)
        
        assert result['success'] is True
        
        # Verify fine is paid
        final_user = engine.load_user(user.user_id)
        assert final_user.fines[0].status == "paid"
        assert final_user.fines[0].paid_date is not None
    
    def test_waive_fine(self, engine, sample_student, sample_book):
        """Test waiving a fine (admin only)."""
        user, admin = sample_student
        
        # Create a fine
        issue_result = engine.issue_book_to_user(user.user_id, sample_book.id)
        copy_id = issue_result['copy_id']
        
        # Set overdue
        record = user.current_borrowings[0]
        past_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        record.due_date = past_date
        engine.save_user(user)
        
        # Return to create fine
        engine.return_book(user.user_id, sample_book.id, copy_id)
        
        # Get the fine ID
        updated_user = engine.load_user(user.user_id)
        fine_id = updated_user.fines[0].fine_id
        
        # Waive the fine
        result = engine.waive_user_fine(admin.user_id, fine_id)
        
        assert result['success'] is True
        
        # Verify fine is waived
        final_user = engine.load_user(user.user_id)
        assert final_user.fines[0].status == "waived"
        assert final_user.fines[0].waived_by == admin.full_name
    
    def test_clear_user_fines(self, engine, sample_student, sample_book):
        """Test clearing all fines for a user."""
        user, admin = sample_student
        
        # Create multiple fines
        for i in range(3):
            # Use different books
            book_data = {
                'id': 200 + i,
                'title': f'Test Book {i}',
                'author': 'Test Author',
                'genre': 'fiction',
                'pages': 200,
                'publisher': 'Test Publisher',
                'type': 1,
                'format': 0,
                'status': 0,
                'copies': 1
            }
            from src.models.book import ResourceFactory
            book = ResourceFactory.create_from_csv_row(book_data)
            engine.save_book(book)
            
            issue_result = engine.issue_book_to_user(user.user_id, book.id)
            copy_id = issue_result['copy_id']
            
            # Set overdue
            record = user.current_borrowings[0]
            past_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
            record.due_date = past_date
            engine.save_user(user)
            
            # Return to create fine
            engine.return_book(user.user_id, book.id, copy_id)
        
        # Clear all fines
        result = engine.clear_user_fines(admin.user_id, user.user_id)
        
        assert result['success'] is True
        assert 'cleared' in result['message'].lower()
        
        # Verify all fines are cleared
        final_user = engine.load_user(user.user_id)
        for fine in final_user.fines:
            assert fine.status == "waived"
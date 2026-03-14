"""
Integration tests for the entire Library Management System.
Tests complete workflows and system interactions.
"""

import pytest
from datetime import datetime, timedelta
from src.models.user import UserRole, UserStatus


class TestCompleteWorkflow:
    """Test complete library workflows."""
    
    def test_student_borrowing_workflow(self, engine, sample_user_data, sample_book_data):
        """Test complete student borrowing workflow."""
        from src.models.book import ResourceFactory
        
        # 1. Register student
        result = engine.register_user(
            role=UserRole.STUDENT.value,
            **sample_user_data
        )
        assert result['success'] is True
        student_id = result['user_id']
        
        # 2. Create admin and activate student
        admin_data = sample_user_data.copy()
        admin_data.update({
            'username': 'admin',
            'email': 'admin@library.com'
        })
        admin_result = engine.register_user(
            role=UserRole.ADMIN.value,
            **admin_data
        )
        admin_id = admin_result['user_id']
        admin = engine.load_user(admin_id)
        admin.activate('System')
        engine.save_user(admin)
        
        student = engine.load_user(student_id)
        student.activate(admin.full_name)
        engine.save_user(student)
        
        # 3. Add book
        book = ResourceFactory.create_from_csv_row(sample_book_data)
        engine.save_book(book)
        
        # 4. Student borrows book
        borrow_result = engine.issue_book_to_user(student_id, book.id)
        assert borrow_result['success'] is True
        copy_id = borrow_result['copy_id']
        
        # Verify borrowing
        updated_student = engine.load_user(student_id)
        assert len(updated_student.current_borrowings) == 1
        
        # 5. Student returns book
        return_result = engine.return_book(student_id, book.id, copy_id)
        assert return_result['success'] is True
        assert return_result['fine_amount'] == 0.0
        
        # Verify return
        final_student = engine.load_user(student_id)
        assert len(final_student.current_borrowings) == 0
        assert len(final_student.borrowing_history) == 1
    
    def test_overdue_fine_workflow(self, engine, sample_student, sample_book_data):
        """Test overdue book and fine workflow."""
        from src.models.book import ResourceFactory
        from datetime import datetime, timedelta
        
        user, admin = sample_student
        
        # Add book
        book = ResourceFactory.create_from_csv_row(sample_book_data)
        engine.save_book(book)
        
        # Borrow book
        borrow_result = engine.issue_book_to_user(user.user_id, book.id)
        assert borrow_result['success'] is True
        copy_id = borrow_result['copy_id']
        
        # Manually set due date to past
        user = engine.load_user(user.user_id)
        record = user.current_borrowings[0]
        past_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        record.due_date = past_date
        engine.save_user(user)
        
        # Return book (should generate fine)
        return_result = engine.return_book(user.user_id, book.id, copy_id)
        assert return_result['success'] is True
        assert return_result['fine_amount'] > 0
        
        # Verify fine created
        user_with_fine = engine.load_user(user.user_id)
        assert len(user_with_fine.fines) == 1
        assert user_with_fine.fines[0].status == "pending"
        assert user_with_fine.fines[0].amount == return_result['fine_amount']
        
        # Pay fine
        fine_id = user_with_fine.fines[0].fine_id
        pay_result = engine.pay_fine(user.user_id, fine_id)
        assert pay_result['success'] is True
        
        # Verify fine paid
        user_after_payment = engine.load_user(user.user_id)
        assert user_after_payment.fines[0].status == "paid"
    
    def test_renewal_workflow(self, engine, sample_student, sample_book_data):
        """Test book renewal workflow."""
        from src.models.book import ResourceFactory
        
        user, admin = sample_student
        
        # Add book
        book = ResourceFactory.create_from_csv_row(sample_book_data)
        engine.save_book(book)
        
        # Borrow book
        borrow_result = engine.issue_book_to_user(user.user_id, book.id)
        assert borrow_result['success'] is True
        copy_id = borrow_result['copy_id']
        original_due = borrow_result['due_date']
        
        # Renew book
        renew_result = engine.renew_book(user.user_id, copy_id)
        assert renew_result['success'] is True
        assert renew_result['new_due_date'] > original_due
        
        # Verify renewal
        updated_user = engine.load_user(user.user_id)
        assert updated_user.current_borrowings[0].renewal_count == 1
    
    def test_user_management_workflow(self, engine, sample_user_data):
        """Test user management workflow."""
        # Register user
        result = engine.register_user(
            role=UserRole.STUDENT.value,
            **sample_user_data
        )
        assert result['success'] is True
        user_id = result['user_id']
        
        # Create admin
        admin_data = sample_user_data.copy()
        admin_data.update({
            'username': 'admin',
            'email': 'admin@library.com'
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
        
        # Deactivate user
        deactivate_result = engine.deactivate_user(admin_id, user_id, "Testing")
        assert deactivate_result['success'] is True
        
        # Reactivate
        activate_result = engine.activate_user(admin_id, user_id)
        assert activate_result['success'] is True
        
        # Blacklist
        blacklist_result = engine.blacklist_user(admin_id, user_id, "Violation")
        assert blacklist_result['success'] is True
        
        # Remove from blacklist
        remove_result = engine.remove_from_blacklist(admin_id, user_id)
        assert remove_result['success'] is True
    
    def test_search_workflow(self, engine):
        """Test search functionality."""
        from src.models.book import ResourceFactory
        
        # Add multiple books
        books = [
            {"id": 1, "title": "Python Programming", "author": "John Doe", "genre": "tech"},
            {"id": 2, "title": "Data Science Basics", "author": "Jane Smith", "genre": "tech"},
            {"id": 3, "title": "Machine Learning", "author": "Bob Johnson", "genre": "tech"},
            {"id": 4, "title": "History of Rome", "author": "John Doe", "genre": "history"},
            {"id": 5, "title": "World War II", "author": "Jane Smith", "genre": "history"}
        ]
        
        for book_data in books:
            data = {
                'id': book_data['id'],
                'title': book_data['title'],
                'author': book_data['author'],
                'genre': book_data['genre'],
                'pages': 200,
                'publisher': 'Test Pub',
                'type': 1,
                'format': 0,
                'status': 0,
                'copies': 1
            }
            book = ResourceFactory.create_from_csv_row(data)
            engine.save_book(book)
        
        # Search by title
        results = engine.search_books_by_title("python")
        assert len(results) == 1
        assert results[0].title == "Python Programming"
        
        # Search by author
        results = engine.search_books_by_author("john doe")
        assert len(results) == 2  # Python Programming and History of Rome
        
        # Search by genre
        results = engine.search_books_by_genre("history")
        assert len(results) == 2
    
    def test_report_generation(self, engine, sample_student, sample_book_data):
        """Test report generation."""
        from src.models.book import ResourceFactory
        
        user, admin = sample_student
        
        # Add multiple books and create some activity
        books = []
        for i in range(3):
            data = sample_book_data.copy()
            data['id'] = i + 1
            book = ResourceFactory.create_from_csv_row(data)
            engine.save_book(book)
            books.append(book)
        
        # Borrow some books
        for book in books[:2]:
            engine.issue_book_to_user(user.user_id, book.id)
        
        # Get borrowing report
        borrow_report = engine.get_borrowing_report(user.user_id)
        assert borrow_report['active_borrowings'] == 2
        assert borrow_report['total_books_borrowed'] == 2
        
        # Get fines report
        fines_report = engine.get_fines_report(user.user_id)
        assert fines_report['total_pending'] == 0.0
        
        # Get system report
        system_report = engine.get_system_report()
        assert system_report['users']['total'] >= 2  # student + admin
        assert system_report['resources']['total'] >= 3
        assert system_report['transactions']['active_borrowings'] >= 2


class TestConcurrency:
    """Test concurrent operations and edge cases."""
    
    def test_borrow_same_copy_twice(self, engine, sample_student, sample_book):
        """Test trying to borrow the same copy twice."""
        user, admin = sample_student
        
        # First borrow
        result1 = engine.issue_book_to_user(user.user_id, sample_book.id)
        assert result1['success'] is True
        copy_id = result1['copy_id']
        
        # Try to borrow again (should fail)
        result2 = engine.issue_book_to_user(user.user_id, sample_book.id)
        assert result2['success'] is False
        assert 'available' in result2['message'].lower()
    
    def test_return_book_twice(self, engine, sample_student, sample_book):
        """Test trying to return the same book twice."""
        user, admin = sample_student
        
        # Borrow
        result = engine.issue_book_to_user(user.user_id, sample_book.id)
        copy_id = result['copy_id']
        
        # Return
        result1 = engine.return_book(user.user_id, sample_book.id, copy_id)
        assert result1['success'] is True
        
        # Try to return again (should fail)
        result2 = engine.return_book(user.user_id, sample_book.id, copy_id)
        assert result2['success'] is False
    
    def test_borrow_when_blacklisted(self, engine, sample_student, sample_book):
        """Test borrowing when user is blacklisted."""
        user, admin = sample_student
        
        # Blacklist user
        user.blacklist(admin.full_name, "Test")
        engine.save_user(user)
        
        # Try to borrow
        result = engine.issue_book_to_user(user.user_id, sample_book.id)
        assert result['success'] is False
        assert 'blacklisted' in result['message'].lower()
    
    def test_multiple_users_borrowing(self, engine, sample_user_data, sample_book_data):
        """Test multiple users borrowing the same book."""
        from src.models.book import ResourceFactory
        from src.models.user import UserFactory
        
        # Create a book with 2 copies
        book_data = sample_book_data.copy()
        book_data['copies'] = 2
        book_data['total_copies'] = 2
        book = ResourceFactory.create_from_csv_row(book_data)
        engine.save_book(book)
        
        # Create admin
        admin_data = sample_user_data.copy()
        admin_data.update({'username': 'admin'})
        admin = UserFactory.create_user(UserRole.ADMIN.value, **admin_data)
        admin.activate('System')
        engine.save_user(admin)
        
        # Create two students
        users = []
        for i in range(2):
            user_data = sample_user_data.copy()
            user_data.update({
                'username': f'student{i}',
                'email': f'student{i}@test.com'
            })
            result = engine.register_user(UserRole.STUDENT.value, **user_data)
            user = engine.load_user(result['user_id'])
            user.activate(admin.full_name)
            engine.save_user(user)
            users.append(user)
        
        # Both borrow successfully
        result1 = engine.issue_book_to_user(users[0].user_id, book.id)
        assert result1['success'] is True
        
        result2 = engine.issue_book_to_user(users[1].user_id, book.id)
        assert result2['success'] is True
        
        # Third user tries (should fail - no copies left)
        user_data = sample_user_data.copy()
        user_data.update({
            'username': 'student3',
            'email': 'student3@test.com'
        })
        result = engine.register_user(UserRole.STUDENT.value, **user_data)
        user3 = engine.load_user(result['user_id'])
        user3.activate(admin.full_name)
        engine.save_user(user3)
        
        result3 = engine.issue_book_to_user(user3.user_id, book.id)
        assert result3['success'] is False
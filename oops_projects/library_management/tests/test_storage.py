"""
Test cases for the Storage class.
Tests all CRUD operations and data persistence.
"""

import pytest
import os
import csv
from datetime import datetime


class TestStorageUserOperations:
    """Test user-related storage operations."""
    
    def test_save_user_new(self, storage, sample_user_data):
        """Test saving a new user."""
        from src.models.user import UserFactory
        
        # Create user
        user = UserFactory.create_user(
            role=1,
            **sample_user_data
        )
        user_dict = user.to_dict()
        
        # Save user
        result = storage.save_user(user_dict)
        assert result is True
        
        # Verify file exists
        assert os.path.exists(storage.users_file)
        
        # Read and verify
        saved = storage.find_user_by_id(user.user_id)
        assert saved is not None
        assert saved['username'] == sample_user_data['username']
        assert saved['email'] == sample_user_data['email']
    
    def test_save_user_update(self, storage, sample_user_data):
        """Test updating an existing user."""
        from src.models.user import UserFactory
        
        # Create and save user
        user = UserFactory.create_user(role=1, **sample_user_data)
        storage.save_user(user.to_dict())
        
        # Update user
        user.phone = "9876543210"
        user.department = "Updated Dept"
        result = storage.save_user(user.to_dict())
        assert result is True
        
        # Verify update
        saved = storage.find_user_by_id(user.user_id)
        assert saved['phone'] == "9876543210"
        assert saved['department'] == "Updated Dept"
    
    def test_find_user_by_id(self, storage, sample_user_data):
        """Test finding user by ID."""
        from src.models.user import UserFactory
        
        user = UserFactory.create_user(role=1, **sample_user_data)
        storage.save_user(user.to_dict())
        
        found = storage.find_user_by_id(user.user_id)
        assert found is not None
        assert found['user_id'] == user.user_id
        
        not_found = storage.find_user_by_id("nonexistent")
        assert not_found is None
    
    def test_find_user_by_username(self, storage, sample_user_data):
        """Test finding user by username."""
        from src.models.user import UserFactory
        
        user = UserFactory.create_user(role=1, **sample_user_data)
        storage.save_user(user.to_dict())
        
        found = storage.find_user_by_username(user.username)
        assert found is not None
        assert found['username'] == user.username
    
    def test_find_user_by_email(self, storage, sample_user_data):
        """Test finding user by email."""
        from src.models.user import UserFactory
        
        user = UserFactory.create_user(role=1, **sample_user_data)
        storage.save_user(user.to_dict())
        
        found = storage.find_user_by_email(user.email)
        assert found is not None
        assert found['email'] == user.email
    
    def test_get_all_users(self, storage):
        """Test getting all users."""
        from src.models.user import UserFactory
        
        # Create multiple users
        for i in range(5):
            user_data = {
                'username': f'user{i}',
                'email': f'user{i}@test.com',
                'full_name': f'User {i}',
                'password': 'Test@1234'
            }
            user = UserFactory.create_user(role=1, **user_data)
            storage.save_user(user.to_dict())
        
        users = storage.get_all_users()
        assert len(users) == 5


class TestStorageResourceOperations:
    """Test resource-related storage operations."""
    
    def test_save_resource_new(self, storage, sample_book_data):
        """Test saving a new resource."""
        from src.models.book import ResourceFactory
        
        resource = ResourceFactory.create_from_csv_row(sample_book_data)
        resource_dict = resource.to_dict()
        
        result = storage.save_resource(resource_dict)
        assert result is True
        
        assert os.path.exists(storage.resources_file)
        
        saved = storage.find_resource_by_id(resource.id)
        assert saved is not None
        assert saved['title'] == sample_book_data['title']
    
    def test_save_resource_update(self, storage, sample_book_data):
        """Test updating an existing resource."""
        from src.models.book import ResourceFactory
        
        resource = ResourceFactory.create_from_csv_row(sample_book_data)
        storage.save_resource(resource.to_dict())
        
        # Update
        resource.title = "Updated Title"
        resource.copies = 5
        result = storage.save_resource(resource.to_dict())
        assert result is True
        
        saved = storage.find_resource_by_id(resource.id)
        assert saved['title'] == "Updated Title"
        assert int(saved['copies']) == 5
    
    def test_find_resource_by_id(self, storage, sample_book_data):
        """Test finding resource by ID."""
        from src.models.book import ResourceFactory
        
        resource = ResourceFactory.create_from_csv_row(sample_book_data)
        storage.save_resource(resource.to_dict())
        
        found = storage.find_resource_by_id(resource.id)
        assert found is not None
        assert int(found['id']) == resource.id
    
    def test_find_resource_by_isbn(self, storage, sample_book_data):
        """Test finding resource by ISBN."""
        from src.models.book import ResourceFactory
        
        resource = ResourceFactory.create_from_csv_row(sample_book_data)
        storage.save_resource(resource.to_dict())
        
        found = storage.find_resource_by_isbn(resource.isbn)
        assert found is not None
        assert found['isbn'] == resource.isbn
    
    def test_get_all_resources(self, storage):
        """Test getting all resources."""
        from src.models.book import ResourceFactory
        
        for i in range(5):
            data = {
                'id': i + 1,
                'title': f'Book {i}',
                'author': 'Author',
                'genre': 'fiction',
                'pages': 200,
                'publisher': 'Publisher',
                'type': 1,
                'format': 0,
                'status': 0,
                'copies': 1
            }
            resource = ResourceFactory.create_from_csv_row(data)
            storage.save_resource(resource.to_dict())
        
        resources = storage.get_all_resources()
        assert len(resources) == 5
    
    def test_search_resources_by_title(self, storage):
        """Test searching resources by title."""
        from src.models.book import ResourceFactory
        
        titles = ["Python Programming", "Data Science", "Machine Learning", "Python Basics"]
        for i, title in enumerate(titles):
            data = {
                'id': i + 1,
                'title': title,
                'author': 'Author',
                'genre': 'tech',
                'pages': 200,
                'publisher': 'Publisher',
                'type': 1,
                'format': 0,
                'status': 0,
                'copies': 1
            }
            resource = ResourceFactory.create_from_csv_row(data)
            storage.save_resource(resource.to_dict())
        
        results = storage.search_resources_by_title("python")
        assert len(results) == 2  # "Python Programming" and "Python Basics"
    
    def test_search_resources_by_author(self, storage):
        """Test searching resources by author."""
        from src.models.book import ResourceFactory
        
        authors = ["John Doe", "Jane Smith", "Bob Johnson", "John Doe"]
        for i, author in enumerate(authors):
            data = {
                'id': i + 1,
                'title': f'Book {i}',
                'author': author,
                'genre': 'fiction',
                'pages': 200,
                'publisher': 'Publisher',
                'type': 1,
                'format': 0,
                'status': 0,
                'copies': 1
            }
            resource = ResourceFactory.create_from_csv_row(data)
            storage.save_resource(resource.to_dict())
        
        results = storage.search_resources_by_author("john")
        assert len(results) == 2  # Both John Doe entries
    
    def test_search_resources_by_genre(self, storage):
        """Test searching resources by genre."""
        from src.models.book import ResourceFactory
        
        genres = ["fiction", "nonfiction", "science", "fiction"]
        for i, genre in enumerate(genres):
            data = {
                'id': i + 1,
                'title': f'Book {i}',
                'author': 'Author',
                'genre': genre,
                'pages': 200,
                'publisher': 'Publisher',
                'type': 1,
                'format': 0,
                'status': 0,
                'copies': 1
            }
            resource = ResourceFactory.create_from_csv_row(data)
            storage.save_resource(resource.to_dict())
        
        results = storage.search_resources_by_genre("fiction")
        assert len(results) == 2


class TestStorageCopyOperations:
    """Test copy-related storage operations."""
    
    def test_save_copy_new(self, storage):
        """Test saving a new copy."""
        copy_data = {
            'copy_id': '1-001',
            'resource_id': 1,
            'barcode': 'BAR-1-001',
            'condition': 1,
            'location': 'A1-2-3',
            'status': 0,
            'purchase_date': '2024-01-01',
            'notes': 'Test copy',
            'checkout_count': 0,
            'last_checkout': None
        }
        
        result = storage.save_copy(copy_data)
        assert result is True
        
        assert os.path.exists(storage.copies_file)
        
        found = storage.find_copy_by_id('1-001')
        assert found is not None
        assert found['copy_id'] == '1-001'
    
    def test_find_copies_by_resource(self, storage):
        """Test finding copies by resource ID."""
        for i in range(3):
            copy_data = {
                'copy_id': f'1-00{i+1}',
                'resource_id': 1,
                'barcode': f'BAR-1-00{i+1}',
                'condition': 1,
                'location': 'A1-2-3',
                'status': 0,
                'purchase_date': '2024-01-01',
                'notes': '',
                'checkout_count': 0,
                'last_checkout': None
            }
            storage.save_copy(copy_data)
        
        copies = storage.find_copies_by_resource(1)
        assert len(copies) == 3


class TestStorageBorrowingOperations:
    """Test borrowing record storage operations."""
    
    def test_save_borrowing_record(self, storage):
        """Test saving a borrowing record."""
        record_data = {
            'record_id': 'BR-test-001',
            'user_id': 'user1',
            'resource_id': 1,
            'copy_id': '1-001',
            'borrow_date': '2024-01-01',
            'due_date': '2024-01-15',
            'return_date': None,
            'renewal_count': 0,
            'fine_amount': 0.0,
            'fine_paid': False,
            'status': 'active'
        }
        
        result = storage.save_borrowing_record(record_data)
        assert result is True
        
        assert os.path.exists(storage.borrowing_records_file)
        
        found = storage.find_borrowing_record_by_id('BR-test-001')
        assert found is not None
        assert found['user_id'] == 'user1'
    
    def test_find_borrowing_records_by_user(self, storage):
        """Test finding borrowing records by user."""
        for i in range(3):
            record_data = {
                'record_id': f'BR-user1-00{i}',
                'user_id': 'user1',
                'resource_id': 1,
                'copy_id': f'1-00{i}',
                'borrow_date': '2024-01-01',
                'due_date': '2024-01-15',
                'return_date': None,
                'renewal_count': 0,
                'fine_amount': 0.0,
                'fine_paid': False,
                'status': 'active'
            }
            storage.save_borrowing_record(record_data)
        
        records = storage.find_borrowing_records_by_user('user1')
        assert len(records) == 3
    
    def test_find_active_borrowing_by_copy(self, storage):
        """Test finding active borrowing by copy ID."""
        record_data = {
            'record_id': 'BR-test-001',
            'user_id': 'user1',
            'resource_id': 1,
            'copy_id': '1-001',
            'borrow_date': '2024-01-01',
            'due_date': '2024-01-15',
            'return_date': None,
            'renewal_count': 0,
            'fine_amount': 0.0,
            'fine_paid': False,
            'status': 'active'
        }
        storage.save_borrowing_record(record_data)
        
        record = storage.find_active_borrowing_by_copy('1-001')
        assert record is not None
        assert record['copy_id'] == '1-001'
        
        # Returned copy
        record_data['status'] = 'returned'
        record_data['return_date'] = '2024-01-10'
        storage.save_borrowing_record(record_data)
        
        record = storage.find_active_borrowing_by_copy('1-001')
        assert record is None
    
    def test_get_all_active_borrowings(self, storage):
        """Test getting all active borrowings."""
        for i in range(3):
            record_data = {
                'record_id': f'BR-00{i}',
                'user_id': f'user{i}',
                'resource_id': 1,
                'copy_id': f'1-00{i}',
                'borrow_date': '2024-01-01',
                'due_date': '2024-01-15',
                'return_date': None,
                'renewal_count': 0,
                'fine_amount': 0.0,
                'fine_paid': False,
                'status': 'active'
            }
            storage.save_borrowing_record(record_data)
        
        # Add one returned
        record_data['record_id'] = 'BR-003'
        record_data['status'] = 'returned'
        record_data['return_date'] = '2024-01-10'
        storage.save_borrowing_record(record_data)
        
        active = storage.get_all_active_borrowings()
        assert len(active) == 3


class TestStorageFineOperations:
    """Test fine record storage operations."""
    
    def test_save_fine_record(self, storage):
        """Test saving a fine record."""
        fine_data = {
            'fine_id': 'FINE-test-001',
            'user_id': 'user1',
            'record_id': 'BR-test-001',
            'amount': 10.50,
            'reason': 'overdue',
            'issued_date': '2024-01-01',
            'due_date': '2024-01-31',
            'paid_date': None,
            'waived_by': None,
            'status': 'pending'
        }
        
        result = storage.save_fine_record(fine_data)
        assert result is True
        
        assert os.path.exists(storage.fines_file)
        
        found = storage.find_fine_by_id('FINE-test-001')
        assert found is not None
        assert float(found['amount']) == 10.50
    
    def test_find_fines_by_user(self, storage):
        """Test finding fines by user."""
        for i in range(3):
            fine_data = {
                'fine_id': f'FINE-user1-00{i}',
                'user_id': 'user1',
                'record_id': f'BR-00{i}',
                'amount': 5.0 * i,
                'reason': 'overdue',
                'issued_date': '2024-01-01',
                'due_date': '2024-01-31',
                'paid_date': None,
                'waived_by': None,
                'status': 'pending' if i < 2 else 'paid'
            }
            storage.save_fine_record(fine_data)
        
        fines = storage.find_fines_by_user('user1')
        assert len(fines) == 3
        
        pending = storage.find_pending_fines_by_user('user1')
        assert len(pending) == 2
    
    def test_get_all_pending_fines(self, storage):
        """Test getting all pending fines."""
        for i in range(5):
            status = 'pending' if i < 3 else 'paid'
            fine_data = {
                'fine_id': f'FINE-00{i}',
                'user_id': f'user{i}',
                'record_id': f'BR-00{i}',
                'amount': 5.0,
                'reason': 'overdue',
                'issued_date': '2024-01-01',
                'due_date': '2024-01-31',
                'paid_date': None if status == 'pending' else '2024-01-15',
                'waived_by': None,
                'status': status
            }
            storage.save_fine_record(fine_data)
        
        pending = storage.get_all_pending_fines()
        assert len(pending) == 3


class TestStorageTransactionOperations:
    """Test transaction log storage operations."""
    
    def test_log_transaction(self, storage):
        """Test logging a transaction."""
        transaction_data = {
            'type': 'issue',
            'user_id': 'user1',
            'resource_id': 1,
            'copy_id': '1-001',
            'due_date': '2024-01-15'
        }
        
        result = storage.log_transaction(transaction_data)
        assert result is True
        
        assert os.path.exists(storage.transactions_file)
        
        transactions = storage.get_all_transactions()
        assert len(transactions) == 1
        assert transactions[0]['type'] == 'issue'
        assert 'transaction_id' in transactions[0]
    
    def test_find_transactions_by_user(self, storage):
        """Test finding transactions by user."""
        for i in range(3):
            transaction_data = {
                'type': 'issue',
                'user_id': 'user1',
                'resource_id': i + 1,
                'copy_id': f'1-00{i}',
                'due_date': '2024-01-15'
            }
            storage.log_transaction(transaction_data)
        
        transactions = storage.find_transactions_by_user('user1')
        assert len(transactions) == 3
    
    def test_find_transactions_by_date_range(self, storage):
        """Test finding transactions by date range."""
        from datetime import datetime, timedelta
        
        # Transactions on different dates
        dates = [
            (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
            (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
            datetime.now().strftime("%Y-%m-%d"),
            (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        ]
        
        for i, date in enumerate(dates):
            transaction_data = {
                'type': 'issue',
                'user_id': 'user1',
                'resource_id': i + 1,
                'copy_id': f'1-00{i}',
                'timestamp': f'{date} 10:00:00',
                'due_date': date
            }
            storage.log_transaction(transaction_data)
        
        # Find transactions in last week
        start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        end = datetime.now().strftime("%Y-%m-%d")
        
        found = storage.find_transactions_by_date_range(start, end)
        assert len(found) == 2  # 5 days ago and today


class TestStorageBackupRestore:
    """Test backup and restore functionality."""
    
    def test_backup_data(self, storage, sample_user_data, sample_book_data):
        """Test creating a backup."""
        from src.models.user import UserFactory
        from src.models.book import ResourceFactory
        
        # Add some data
        user = UserFactory.create_user(role=1, **sample_user_data)
        storage.save_user(user.to_dict())
        
        resource = ResourceFactory.create_from_csv_row(sample_book_data)
        storage.save_resource(resource.to_dict())
        
        # Create backup
        result = storage.backup_data()
        assert result is True
        
        # Check backup directory exists
        backup_dir = os.path.join(storage.data_path, 'backups')
        assert os.path.exists(backup_dir)
        
        # Check backup files exist
        backups = os.listdir(backup_dir)
        assert len(backups) > 0
        
        latest_backup = os.path.join(backup_dir, backups[0])
        assert os.path.exists(os.path.join(latest_backup, 'users.csv'))
        assert os.path.exists(os.path.join(latest_backup, 'resources.csv'))
    
    def test_restore_from_backup(self, storage):
        """Test restoring from a backup."""
        # Create backup first
        result = storage.backup_data()
        assert result is True
        
        backup_dir = os.path.join(storage.data_path, 'backups')
        backups = os.listdir(backup_dir)
        latest_backup = os.path.join(backup_dir, backups[0])
        
        # Restore
        result = storage.restore_from_backup(latest_backup)
        assert result is True


class TestStorageUtilities:
    """Test utility methods."""
    
    def test_get_statistics(self, storage, sample_user_data, sample_book_data):
        """Test getting statistics."""
        from src.models.user import UserFactory
        from src.models.book import ResourceFactory
        
        # Add some data
        for i in range(3):
            user_data = sample_user_data.copy()
            user_data['username'] = f'user{i}'
            user = UserFactory.create_user(role=1, **user_data)
            storage.save_user(user.to_dict())
        
        for i in range(2):
            book_data = sample_book_data.copy()
            book_data['id'] = i + 1
            book = ResourceFactory.create_from_csv_row(book_data)
            storage.save_resource(book.to_dict())
        
        stats = storage.get_statistics()
        assert stats['users'] == 3
        assert stats['resources'] == 2
        assert 'last_updated' in stats
    
    def test_clear_all_data(self, storage, sample_user_data):
        """Test clearing all data."""
        from src.models.user import UserFactory
        
        # Add some data
        user = UserFactory.create_user(role=1, **sample_user_data)
        storage.save_user(user.to_dict())
        
        assert len(storage.get_all_users()) == 1
        
        # Clear without confirm
        result = storage.clear_all_data(confirm=False)
        assert result is False
        assert len(storage.get_all_users()) == 1
        
        # Clear with confirm
        result = storage.clear_all_data(confirm=True)
        assert result is True
        assert len(storage.get_all_users()) == 0
    
    def test_import_from_dict(self, storage):
        """Test importing data from dictionary."""
        data = {
            'users': [
                {
                    'user_id': 'import1',
                    'username': 'importuser',
                    'password_hash': 'hash',
                    'email': 'import@test.com',
                    'full_name': 'Import User',
                    'role': 1,
                    'status': 1
                }
            ],
            'resources': [
                {
                    'id': 999,
                    'title': 'Import Book',
                    'author': 'Import Author',
                    'genre': 'fiction',
                    'pages': 200,
                    'publisher': 'Import Pub',
                    'type': 1,
                    'format': 0,
                    'status': 0,
                    'copies': 1
                }
            ],
            'copies': [
                {
                    'copy_id': '999-001',
                    'resource_id': 999,
                    'barcode': 'BAR-999-001',
                    'condition': 1,
                    'location': 'A1-2-3',
                    'status': 0,
                    'purchase_date': '2024-01-01',
                    'notes': ''
                }
            ]
        }
        
        result = storage.import_from_dict(data)
        assert result is True
        
        # Verify import
        assert storage.find_user_by_id('import1') is not None
        assert storage.find_resource_by_id(999) is not None
        assert storage.find_copy_by_id('999-001') is not None
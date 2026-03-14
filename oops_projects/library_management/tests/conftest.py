import pytest
import os
import shutil
import tempfile
from datetime import datetime, timedelta

from src.core.engine import LibraryEngine
from src.models.user import UserFactory, UserRole, UserStatus, Student, Faculty, Librarian, Admin
from src.models.book import ResourceFactory, Book, Journal, ResearchPaper, PhysicalCopy
from src.repository.storage import Storage
from src.core.validator import Validator
from src.utils.auth_tools import AuthTools


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def engine(temp_data_dir):
    """Create a LibraryEngine instance with temporary data directory."""
    return LibraryEngine(data_path=temp_data_dir)


@pytest.fixture
def storage(temp_data_dir):
    """Create a Storage instance with temporary data directory."""
    return Storage(data_path=temp_data_dir)


@pytest.fixture
def validator():
    """Create a Validator instance."""
    return Validator()


@pytest.fixture
def sample_user_data():
    """Provide sample user data for testing."""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'full_name': 'Test User',
        'password': 'Test@1234',
        'department': 'Computer Science',
        'phone': '1234567890'
    }


@pytest.fixture
def sample_book_data():
    """Provide sample book data for testing."""
    return {
        'id': 1,
        'title': 'Test Book',
        'author': 'Test Author',
        'isbn': '978-1234567890',
        'genre': 'fiction',
        'category': 'Literature',
        'pages': 200,
        'publisher': 'Test Publisher',
        'language': 'English',
        'edition': '1st',
        'publication_date': '2023-01-01',
        'type': 1,  # Book
        'format': 0,  # Physical
        'condition': 1,  # New
        'location': 'A1-2-3',
        'status': 0,  # Available
        'copies': 3,
        'total_copies': 3,
        'description': 'A test book for unit testing'
    }


@pytest.fixture
def sample_journal_data():
    """Provide sample journal data for testing."""
    return {
        'id': 2,
        'title': 'Test Journal',
        'author': 'Various',
        'isbn': '1557-1234',
        'genre': 'journal',
        'category': 'Science',
        'pages': 150,
        'publisher': 'Test Press',
        'language': 'English',
        'edition': 'Vol 1',
        'publication_date': '2023-06-01',
        'type': 2,  # Journal
        'format': 1,  # Digital
        'condition': 2,  # Good
        'location': 'Digital',
        'status': 0,
        'copies': 1,
        'total_copies': 1,
        'description': 'A test journal',
        'volume': '1',
        'issue': '1'
    }


@pytest.fixture
def sample_student(engine, sample_user_data):
    """Create a sample student for testing."""
    result = engine.register_user(
        role=UserRole.STUDENT.value,
        **sample_user_data
    )
    assert result['success']
    user = engine.load_user(result['user_id'])
    
    # Activate the user
    # Create admin first to activate
    admin_data = sample_user_data.copy()
    admin_data.update({
        'username': 'admin',
        'email': 'admin@library.com',
        'full_name': 'Admin User'
    })
    admin_result = engine.register_user(
        role=UserRole.ADMIN.value,
        **admin_data
    )
    admin = engine.load_user(admin_result['user_id'])
    admin.activate('System')
    engine.save_user(admin)
    
    # Activate student
    user.activate(admin.full_name)
    engine.save_user(user)
    
    return user, admin


@pytest.fixture
def sample_book(engine, sample_book_data):
    """Create a sample book for testing."""
    from src.models.book import ResourceFactory
    book = ResourceFactory.create_from_csv_row(sample_book_data)
    engine.save_book(book)
    return book


@pytest.fixture
def sample_digital_book(engine):
    """Create a sample digital book for testing."""
    book_data = {
        'id': 100,
        'title': 'Digital Test Book',
        'author': 'Digital Author',
        'isbn': '978-9999999999',
        'genre': 'nonfiction',
        'category': 'Technology',
        'pages': 300,
        'publisher': 'Digital Press',
        'language': 'English',
        'edition': '1st',
        'publication_date': '2023-01-01',
        'type': 1,
        'format': 1,  # Digital
        'condition': 1,
        'location': 'Digital',
        'status': 0,
        'copies': 999,  # Unlimited
        'total_copies': 999,
        'description': 'A digital test book'
    }
    from src.models.book import ResourceFactory
    book = ResourceFactory.create_from_csv_row(book_data)
    engine.save_book(book)
    return book
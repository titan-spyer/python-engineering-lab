from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any


# Enums for better type safety and readability
class ResourceType(Enum):
    BOOK = 1
    JOURNAL = 2
    RESEARCH_PAPER = 3
    MAGAZINE = 4
    DVD = 5
    COMIC = 6
    
    @classmethod
    def get_name(cls, value: int) -> str:
        for item in cls:
            if item.value == value:
                return item.name
        return "UNKNOWN"


class FormatType(Enum):
    PHYSICAL = 0
    DIGITAL = 1
    AUDIO = 2
    VIDEO = 3
    
    @classmethod
    def get_name(cls, value: int) -> str:
        for item in cls:
            if item.value == value:
                return item.name
        return "UNKNOWN"


class ConditionType(Enum):
    NEW = 1
    GOOD = 2
    DAMAGED = 3
    LOST = 4
    REPAIR = 5
    
    @classmethod
    def get_name(cls, value: int) -> str:
        for item in cls:
            if item.value == value:
                return item.name
        return "UNKNOWN"


class StatusType(Enum):
    AVAILABLE = 0
    CHECKED_OUT = 1
    ARCHIVED = -1
    RESERVED = 2
    LOST = 3
    
    @classmethod
    def get_name(cls, value: int) -> str:
        for item in cls:
            if item.value == value:
                return item.name
        return "UNKNOWN"


# Class to represent individual physical copies
class PhysicalCopy:
    def __init__(self, 
                 copy_id: str,
                 resource_id: int,
                 barcode: str,
                 condition: ConditionType = ConditionType.NEW,
                 location: str = "",
                 status: int = 0,
                 purchase_date: Optional[str] = None,
                 notes: str = ""):
        self.copy_id = copy_id
        self.resource_id = resource_id
        self.barcode = barcode
        self.condition = condition
        self.location = location
        self.status = status
        self.purchase_date = purchase_date or datetime.now().strftime("%Y-%m-%d")
        self.notes = notes
        self.checkout_count = 0
        self.last_checkout = None
        self.current_holder = None
        self.due_date = None
    
    def check_out(self, user_id: str, due_date: str) -> bool:
        if self.status == 0:
            self.status = 1
            self.current_holder = user_id
            self.due_date = due_date
            self.checkout_count += 1
            self.last_checkout = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return True
        return False
    
    def check_in(self) -> bool:
        if self.status == 1:
            self.status = 0
            self.current_holder = None
            self.due_date = None
            return True
        return False
    
    def update_condition(self, new_condition: ConditionType):
        self.condition = new_condition
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'copy_id': self.copy_id,
            'resource_id': self.resource_id,
            'barcode': self.barcode,
            'condition': self.condition.value,
            'location': self.location,
            'status': self.status,
            'purchase_date': self.purchase_date,
            'notes': self.notes,
            'checkout_count': self.checkout_count,
            'last_checkout': self.last_checkout
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhysicalCopy':
        copy = cls(
            copy_id=data['copy_id'],
            resource_id=data['resource_id'],
            barcode=data['barcode'],
            condition=ConditionType(data['condition']),
            location=data['location'],
            status=data['status'],
            purchase_date=data['purchase_date'],
            notes=data.get('notes', '')
        )
        copy.checkout_count = data.get('checkout_count', 0)
        copy.last_checkout = data.get('last_checkout')
        return copy
    
    def __str__(self):
        status = "Available" if self.status == 0 else "Checked Out"
        return f"Copy {self.copy_id} [Barcode: {self.barcode}] - {status} - {self.condition.name}"


# A parent class for all resources in the library management system.
class Resource(ABC):
    def __init__(
            self,
            id: int,
            title: str,
            author: str,
            genre: str,
            pages: int,
            publisher: str,
            type: int,
            format: int,
            status: int,
            copies: int,
            isbn: Optional[str] = None,
            category: str = "",
            language: str = "English",
            edition: str = "1st",
            publication_date: Optional[str] = None,
            condition: int = 1,
            location: str = "",
            total_copies: Optional[int] = None,
            description: str = "",
            date_added: Optional[str] = None,
            last_updated: Optional[str] = None
            ):
        self.id: int = id
        self.title: str = title
        self.author: str = author
        self.isbn: Optional[str] = isbn
        self.genre: str = genre
        self.category: str = category
        self.pages: int = pages
        self.publisher: str = publisher
        self.language: str = language
        self.edition: str = edition
        self.publication_date: Optional[str] = publication_date
        self.type: int = type
        self.format: int = format
        self.condition: int = condition
        self.location: str = location
        self.status: int = status
        self.copies: int = copies
        self.total_copies: int = total_copies or copies
        self.description: str = description
        self.date_added: str = date_added or datetime.now().strftime("%Y-%m-%d")
        self.last_updated: str = last_updated or self.date_added
        
        # For tracking individual copies
        self.physical_copies: List[PhysicalCopy] = []
        self._initialize_copies()

    def _initialize_copies(self):
        """Initialize physical copies based on total_copies"""
        if self.format == 0:  # Physical format
            for i in range(self.total_copies):
                copy_id = f"{self.id}-{i+1:03d}"
                barcode = f"BAR-{self.id}-{i+1:03d}"
                copy = PhysicalCopy(
                    copy_id=copy_id,
                    resource_id=self.id,
                    barcode=barcode,
                    condition=ConditionType(self.condition),
                    location=self.location,
                    status=0 if i < self.copies else 1  # Mark some as checked out if copies < total_copies
                )
                self.physical_copies.append(copy)

    @abstractmethod
    def check_out(self, user_id: Optional[str] = None):
        pass

    @abstractmethod
    def check_in(self, copy_id: Optional[str] = None):
        pass

    @abstractmethod
    def copies_available(self):
        pass

    @abstractmethod
    def __repr__(self):
        pass

    def __str__(self):
        status_text = StatusType.get_name(self.status)
        type_text = ResourceType.get_name(self.type)
        format_text = FormatType.get_name(self.format)
        condition_text = ConditionType.get_name(self.condition)
        
        return (
            f"\n{'='*60}\n"
            f"📚 {self.title}\n"
            f"{'='*60}\n"
            f"ID: {self.id} | Type: {type_text} | Format: {format_text}\n"
            f"Author(s): {self.author}\n"
            f"ISBN: {self.isbn or 'N/A'}\n"
            f"Genre: {self.genre} | Category: {self.category}\n"
            f"Publisher: {self.publisher} | Edition: {self.edition}\n"
            f"Language: {self.language} | Pages: {self.pages}\n"
            f"Publication Date: {self.publication_date or 'N/A'}\n"
            f"Condition: {condition_text} | Location: {self.location or 'Not set'}\n"
            f"Status: {status_text}\n"
            f"Copies: {self.copies}/{self.total_copies} available\n"
            f"Description: {self.description[:100]}...\n"
            f"Added: {self.date_added} | Updated: {self.last_updated}\n"
            f"{'='*60}"
        )

    def __eq__(self, other):
        if not isinstance(other, Resource):
            return False
        return self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.title < other.title

    def __le__(self, other):
        return self.title <= other.title

    def __gt__(self, other):
        return self.title > other.title

    def __ge__(self, other):
        return self.title >= other.title

    def type_of_resource(self) -> str:
        return ResourceType.get_name(self.type)

    def format_of_resource(self) -> str:
        return FormatType.get_name(self.format)
    
    def update_details(self, **kwargs) -> bool:
        """Edit resource details"""
        try:
            for key, value in kwargs.items():
                if hasattr(self, key) and key not in ['id', 'date_added']:
                    setattr(self, key, value)
            self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"✅ {self.title} details updated successfully.")
            return True
        except Exception as e:
            print(f"❌ Error updating details: {e}")
            return False
    
    def archive(self) -> bool:
        """Archive the resource (soft delete)"""
        self.status = -1
        self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"📦 {self.title} has been archived.")
        return True
    
    def add_copy(self) -> Optional[str]:
        """Add a new physical copy"""
        if self.format == 0:
            new_copy_num = len(self.physical_copies) + 1
            copy_id = f"{self.id}-{new_copy_num:03d}"
            barcode = f"BAR-{self.id}-{new_copy_num:03d}"
            
            new_copy = PhysicalCopy(
                copy_id=copy_id,
                resource_id=self.id,
                barcode=barcode,
                condition=ConditionType.NEW,
                location=self.location,
                status=0
            )
            
            self.physical_copies.append(new_copy)
            self.total_copies += 1
            self.copies += 1
            self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"✅ New copy added with ID: {copy_id}")
            return copy_id
        else:
            print("❌ Cannot add physical copies to digital resources.")
            return None
    
    def remove_copy(self, copy_id: str) -> bool:
        """Remove a specific copy (damaged/lost)"""
        for i, copy in enumerate(self.physical_copies):
            if copy.copy_id == copy_id:
                if copy.status == 0:  # Only remove if not checked out
                    removed = self.physical_copies.pop(i)
                    self.total_copies -= 1
                    if removed.status == 0:
                        self.copies -= 1
                    self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"✅ Copy {copy_id} removed.")
                    return True
                else:
                    print(f"❌ Cannot remove copy {copy_id} - it is currently checked out.")
                    return False
        print(f"❌ Copy {copy_id} not found.")
        return False
    
    def update_condition(self, copy_id: Optional[str] = None, new_condition: int = 1) -> bool:
        """Update condition of a specific copy or all copies"""
        condition = ConditionType(new_condition)
        
        if copy_id and self.format == 0:
            for copy in self.physical_copies:
                if copy.copy_id == copy_id:
                    old_condition = copy.condition
                    copy.update_condition(condition)
                    print(f"✅ Copy {copy_id} condition changed from {old_condition.name} to {condition.name}")
                    return True
            print(f"❌ Copy {copy_id} not found.")
            return False
        else:
            # Update all copies
            old_condition = ConditionType(self.condition)
            self.condition = new_condition
            if self.format == 0:
                for copy in self.physical_copies:
                    copy.update_condition(condition)
            print(f"✅ Resource condition changed from {old_condition.name} to {condition.name}")
            return True
    
    def get_location(self) -> str:
        """Get current shelf location"""
        if self.location:
            return self.location
        return "Location not set"
    
    def set_location(self, new_location: str) -> bool:
        """Set new shelf location for all copies"""
        old_location = self.location
        self.location = new_location
        if self.format == 0:
            for copy in self.physical_copies:
                copy.location = new_location
        self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"📍 Location updated from '{old_location}' to '{new_location}'")
        return True
    
    def get_available_copies(self) -> List[PhysicalCopy]:
        """Get list of available physical copies"""
        if self.format == 0:
            return [copy for copy in self.physical_copies if copy.status == 0]
        return []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert resource to dictionary for CSV storage"""
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'isbn': self.isbn or '',
            'genre': self.genre,
            'category': self.category,
            'pages': self.pages,
            'publisher': self.publisher,
            'language': self.language,
            'edition': self.edition,
            'publication_date': self.publication_date or '',
            'type': self.type,
            'format': self.format,
            'condition': self.condition,
            'location': self.location,
            'status': self.status,
            'copies': self.copies,
            'total_copies': self.total_copies,
            'description': self.description,
            'date_added': self.date_added,
            'last_updated': self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], resource_type: str) -> 'Resource':
        """Create resource from dictionary"""
        if resource_type == 'Book':
            return Book(**data)
        elif resource_type == 'Journal':
            return Journal(**data)
        elif resource_type == 'ResearchPaper':
            return ResearchPaper(**data)
        else:
            raise ValueError(f"Unknown resource type: {resource_type}")


# A child class for books, which inherits from the Resource class.
class Book(Resource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def check_out(self, user_id: Optional[str] = None):
        if self.format == 0:  # Physical
            available = self.get_available_copies()
            if available:
                copy = available[0]
                copy.check_out(user_id, "14_days")
                self.copies -= 1
                if self.copies == 0:
                    self.status = 1
                print(f"✅ '{self.title}' (Copy: {copy.copy_id}) has been checked out to {user_id or 'Unknown'}.")
                return copy.copy_id
            else:
                print(f"❌ No copies of '{self.title}' are currently available.")
                return None
        else:  # Digital
            print(f"📱 '{self.title}' is a digital resource. Access via download link.")
            return "digital_access"

    def check_in(self, copy_id: Optional[str] = None):
        if self.format == 0:  # Physical
            if not copy_id:
                print("❌ Please specify which copy you're returning.")
                return False
            
            for copy in self.physical_copies:
                if copy.copy_id == copy_id and copy.status == 1:
                    copy.check_in()
                    self.copies += 1
                    self.status = 0
                    print(f"✅ '{self.title}' (Copy: {copy_id}) has been checked in.")
                    return True
            
            print(f"❌ Copy {copy_id} not found or not checked out.")
            return False
        else:
            print(f"📱 Digital resources don't need to be checked in.")
            return True

    def copies_available(self):
        return self.copies
    
    def __repr__(self):
        return f"Book(id={self.id}, title='{self.title}', author='{self.author}', available={self.copies}/{self.total_copies})"
    

# A child class for journals, which inherits from the Resource class.
class Journal(Resource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.volume = kwargs.get('volume', '')
        self.issue = kwargs.get('issue', '')
    
    def check_out(self, user_id: Optional[str] = None):
        if self.format == 0 and self.copies > 0:
            self.copies -= 1
            if self.copies == 0:
                self.status = 1
            print(f"✅ '{self.title}' (Volume: {self.volume}) has been checked out.")
            return True
        elif self.format == 1:
            print(f"📱 '{self.title}' is a digital journal. Access via online portal.")
            return "digital_access"
        else:
            print(f"❌ '{self.title}' is not available for checkout.")
            return False

    def check_in(self, copy_id: Optional[str] = None):
        self.copies += 1
        self.status = 0
        print(f"✅ '{self.title}' has been checked in.")
        return True

    def copies_available(self):
        return self.copies
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'volume': self.volume,
            'issue': self.issue
        })
        return data

    def __repr__(self):
        return f"Journal(id={self.id}, title='{self.title}', volume='{self.volume}')"


# A child class for research papers, which inherits from the Resource class.
class ResearchPaper(Resource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.conference = kwargs.get('conference', '')
        self.doi = kwargs.get('doi', '')
    
    def check_out(self, user_id: Optional[str] = None):
        if self.format == 1:
            print(f"📄 '{self.title}' is available for download. DOI: {self.doi}")
            return "download_link"
        else:
            # Handle physical copies if any
            if self.copies > 0:
                self.copies -= 1
                print(f"✅ '{self.title}' has been checked out.")
                return True
            else:
                print(f"❌ No copies of '{self.title}' available.")
                return False

    def check_in(self, copy_id: Optional[str] = None):
        if self.format == 0:
            self.copies += 1
            print(f"✅ '{self.title}' has been checked in.")
        else:
            print(f"📄 Digital research papers don't need check-in.")
        return True

    def copies_available(self):
        return self.copies
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'conference': self.conference,
            'doi': self.doi
        })
        return data

    def __repr__(self):
        return f"ResearchPaper(id={self.id}, title='{self.title}', author='{self.author}')"


# Factory class to create resources from CSV data
class ResourceFactory:
    @staticmethod
    def create_from_csv_row(row: Dict[str, str]) -> Resource:
        """Create appropriate resource object from CSV row"""
        data = {
            'id': int(row['id']),
            'title': row['title'],
            'author': row['author'],
            'isbn': row.get('isbn', ''),
            'genre': row['genre'],
            'category': row.get('category', ''),
            'pages': int(row['pages']),
            'publisher': row['publisher'],
            'language': row.get('language', 'English'),
            'edition': row.get('edition', '1st'),
            'publication_date': row.get('publication_date', ''),
            'type': int(row['type']),
            'format': int(row['format']),
            'condition': int(row.get('condition', 1)),
            'location': row.get('location', ''),
            'status': int(row['status']),
            'copies': int(row['copies']),
            'total_copies': int(row.get('total_copies', row['copies'])),
            'description': row.get('description', ''),
            'date_added': row.get('date_added', ''),
            'last_updated': row.get('last_updated', '')
        }
        
        resource_type = int(row['type'])
        
        if resource_type == 1:
            return Book(**data)
        elif resource_type == 2:
            return Journal(**data)
        elif resource_type == 3:
            return ResearchPaper(**data)
        else:
            return Book(**data)
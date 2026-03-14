import csv
import os
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import shutil
from pathlib import Path


class Storage:
    def __init__(self, data_path: str = "data"):
        self.data_path = data_path
        self._ensure_data_directory()
        self.users_file = os.path.join(self.data_path, "users.csv")
        self.resources_file = os.path.join(self.data_path, "resources.csv")
        self.copies_file = os.path.join(self.data_path, "copies.csv")
        self.transactions_file = os.path.join(self.data_path, "transactions.csv")
        self.fines_file = os.path.join(self.data_path, "fines.csv")
        self.borrowing_records_file = os.path.join(self.data_path, "borrowing_records.csv")
        self._initialize_csv_files()

    def _ensure_data_directory(self):
        os.makedirs(self.data_path, exist_ok=True)

    def _initialize_csv_files(self):
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w', newline='', encoding='utf-8')as f:
                writer = csv.writer(f)
                writer.writerow([
                    'user_id', 'username', 'password_hash', 'email', 'full_name',
                    'role', 'status', 'department', 'phone', 'address',
                    'registration_date', 'last_login', 'total_books_borrowed',
                    'total_fines_paid', 'times_blacklisted', 'activation_date',
                    'deactivation_date', 'deactivation_reason', 'notes',
                    'student_id', 'year_of_study', 'major', 'employee_id',
                    'designation', 'qualification', 'staff_id', 'section',
                    'shift', 'admin_id', 'access_level'
                ])
        if not os.path.exists(self.resources_file):
            with open(self.resources_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'id', 'title', 'author', 'isbn', 'genre', 'category',
                    'pages', 'publisher', 'language', 'edition', 'publication_date',
                    'type', 'format', 'condition', 'location', 'status',
                    'copies', 'total_copies', 'description', 'date_added', 'last_updated'
                ])
        if not os.path.exists(self.copies_file):
            with open(self.copies_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'copy_id', 'resource_id', 'barcode', 'condition', 'location',
                    'status', 'purchase_date', 'notes', 'checkout_count', 'last_checkout'
                ])
        if not os.path.exists(self.transactions_file):
            with open(self.transactions_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'transaction_id', 'type', 'user_id', 'resource_id', 'copy_id',
                    'timestamp', 'due_date', 'return_date', 'fine_amount', 'notes'
                ])
        if not os.path.exists(self.fines_file):
            with open(self.fines_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'fine_id', 'user_id', 'record_id', 'amount', 'reason',
                    'issued_date', 'due_date', 'paid_date', 'waived_by', 'status'
                ])
        if not os.path.exists(self.borrowing_records_file):
            with open(self.borrowing_records_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'record_id', 'user_id', 'resource_id', 'copy_id', 'borrow_date',
                    'due_date', 'return_date', 'renewal_count', 'fine_amount',
                    'fine_paid', 'status', 'renewal_history'
                ])
    def _read_csv(self, file_path: str) -> List[Dict[str, str]]:
        data = []
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cleaned_row  = {k: (v if v != '' else None) for k, v in row.items()}
                    data.append(cleaned_row)
        except FileNotFoundError:
            pass
        return data
    def _write_csv(self, file_path: str, data: List[Dict[str, Any]], headers: List[str]):
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in data:
                writer.writerow({k: (v if v is not None else '') for k, v in row.items()})
    def _append_csv(self, file_path: str, row: Dict[str, Any], headers: List[str]):
        file_exists = os.path.exists(file_path)
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            if not file_exists:
                writer.writeheader()
            writer.writerow({k: (v if v is not None else '') for k, v in row.items()})
    def _update_csv(self, file_path: str, key_field: str, key_value: Union[str, int], updated_row: Dict[str, Any], headers: List[str]) -> bool:
        data = self._read_csv(file_path)
        updated = False
        for i, row in enumerate(data):
            if str(row.get(key_field)) == str(key_value):
                data[i] = updated_row
                updated = True
                break
        if updated:
            self._write_csv(file_path, data, headers)
        return updated
    def _delete_from_csv(self, file_path: str, key_field: str, key_value: Union[str, int]) -> bool:
        data = self._read_csv(file_path)
        original_length = len(data)
        data = [row for row in data if str(row.get(key_field)) != str(key_value)]
        if len(data) < original_length:
            headers = self._get_headers(file_path)
            self._write_csv(file_path, data, headers)
            return True
        return False
    def _get_headers(self, file_path: str) -> List[str]:
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f) 
                return next(reader)
        except (FileNotFoundError, StopIteration):
            return []


    def find_user_by_id(self, user_id: str) -> Optional[Dict[str, str]]:
        users = self._read_csv(self.users_file)
        for user in users:
            if user.get('user_id') == user_id:
                return user
        return None

    def find_user_by_username(self, username: str) -> Optional[Dict[str, str]]:
        users = self._read_csv(self.users_file)
        for user in users:
            if user.get('username') == username:
                return user
        return None

    def find_user_by_email(self, email: str) -> Optional[Dict[str, str]]:
        users = self._read_csv(self.users_file)
        for user in users:
            if user.get('email') == email:
                return user
        return None

    def get_all_users(self) -> List[Dict[str, str]]:
        return self._read_csv(self.users_file)

    def save_user(self, user_data: Dict[str, Any]) -> bool:
        headers = self._get_headers(self.users_file)
        existing = self.find_user_by_id(user_data.get('user_id', ''))
        if existing:
            return self._update_csv(
                self.users_file, 'user_id', user_data['user_id'], user_data, headers
            )
        else:
            self._append_csv(self.users_file, user_data, headers
            )
            return True

    def find_resource_by_id(self, resource_id: int) -> Optional[Dict[str, str]]:
        resources = self._read_csv(self.resources_file)
        for resource in resources:
            if resource.get('id') and int(resource['id']) == resource_id:
                return resource
        return None

    def find_resource_by_isbn(self, isbn: str) -> Optional[Dict[str, str]]:
        if not isbn:
            return None
        resources = self._read_csv(self.resources_file)
        for resource in resources:
            if resource.get('isbn') == isbn:
                return resource
        return None

    def get_all_resources(self) -> List[Dict[str, str]]:
        return self._read_csv(self.resources_file)

    def save_resource(self, resource_data: Dict[str, Any]) -> bool:
        headers = self._get_headers(self.resources_file)
        existing = self.find_resource_by_id(resource_data.get('id', 0))
        if existing:
            return self._update_csv(
                self.resources_file, 'id', resource_data['id'], resource_data, headers
            )
        else:
            self._append_csv(
                self.resources_file, resource_data, headers
            )
            return True

    def search_resources_by_author(self, author: str) -> List[Dict[str, str]]:
        resources = self._read_csv(self.resources_file)
        return [res for res in resources if res.get('author') and author.lower() in res['author'].lower()]

    def search_resources_by_genre(self, genre: str) -> List[Dict[str, str]]:
        resources = self._read_csv(self.resources_file)
        return [res for res in resources if res.get('genre') and genre.lower() in res['genre'].lower()]
    def search_resources_by_title(self, title: str) -> List[Dict[str, str]]:
        resources = self._read_csv(self.resources_file)
        return [res for res in resources if res.get('title') and title.lower() in res['title'].lower()]



    def find_copies_by_resource(self, resource_id: int) -> List[Dict[str, str]]:
        copies = self._read_csv(self.copies_file)
        return [
            copy for copy in copies if copy.get('resource_id') and int(copy['resource_id']) == resource_id
        ]
    def find_copy_by_id(self, copy_id: str) -> Optional[Dict[str, str]]:
        copies = self._read_csv(self.copies_file)
        for copy in copies:
            if copy.get('copy_id') == copy_id:
                return copy
        return None

    def save_copy(self, copy_data: Dict[str, Any]) -> bool:
        headers = self._get_headers(self.copies_file)
        existing = self.find_copy_by_id(copy_data.get('copy_id', ''))
        if existing:
            return self._update_csv(
                self.copies_file, 'copy_id', copy_data['copy_id'], copy_data, headers
            )
        else:
            self._append_csv(self.copies_file, copy_data, headers)
            return True


    def find_borrowing_records_by_user(self, user_id: str) -> List[Dict[str, str]]:
        records = self._read_csv(self.borrowing_records_file)
        return[r for r in records if r.get('user_id') == user_id]

    def find_borrowing_record_by_id(self, record_id: str) -> Optional[Dict[str, str]]:
        records = self._read_csv(self.borrowing_records_file)
        return next((r for r in records if r.get('record_id') == record_id), None)

    def find_active_borrowing_by_copy(self, copy_id: str)  -> Optional[Dict[str, str]]:
        records = self._read_csv(self.borrowing_records_file)
        return next((r for r in records if r.get('copy_id') == copy_id and r.get('status') == 'active'), None)

    def save_borrowing_record(self, record_data: Dict[str, Any]) -> bool:
        headers = self._get_headers(self.borrowing_records_file)
        existing = self.find_borrowing_record_by_id(record_data.get('record_id', ''))
        if existing:
            return self._update_csv(
                self.borrowing_records_file, 'record_id', record_data['record_id'], record_data, headers
            )
        else:
            self._append_csv(self.borrowing_records_file, record_data, headers)
            return True

    def get_all_active_borrowings(self) -> List[Dict[str, str]]:
        records = self._read_csv(self.borrowing_records_file)
        return [r for r in records if r.get('status') == 'active']


    def find_fines_by_user(self, user_id: str) -> List[Dict[str, str]]:
        fines = self._read_csv(self.fines_file)
        return [f for f in fines if f.get('user_id') == user_id]
    def find_fine_by_id(self, fine_id: str) -> Optional[Dict[str, str]]:
        fines = self._read_csv(self.fines_file)
        return next((f for f in fines if f.get('fine_id') == fine_id), None)
    def find_pending_fines_by_user(self, user_id: str) -> List[Dict[str, str]]:
        fines = self._read_csv(self.fines_file)
        return [f for f in fines if f.get('user_id') == user_id and f.get('status') == 'pending']
    def save_fine_record(self, fine_data: Dict[str, Any]) -> bool:
        headers = self._get_headers(self.fines_file)
        existing = self.find_fine_by_id(fine_data.get('fine_id', ''))
        if existing:
            return self._update_csv(
                self.fines_file, 'fine_id', fine_data['fine_id'], fine_data, headers
            )
        else:
            self._append_csv(self.fines_file, fine_data, headers)
            return True
    def get_all_pending_fines(self) -> List[Dict[str, str]]:
        fines = self._read_csv(self.fines_file)
        return[f for f in fines if f.get('status') == 'pending']


    def log_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        headers = self._get_headers(self.transactions_file)
        if 'transaction_id' not in transaction_data:
            transaction_data['transaction_id'] = f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if 'timestamp' not in transaction_data:
            transaction_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self._append_csv(self.transactions_file, transaction_data, headers)
        return True

    def find_transactions_by_user(self, user_id: str) -> List[Dict[str, str]]:
        transactions = self._read_csv(self.transactions_file)
        return [t for t in transactions if t.get('user_id') == user_id]

    def find_transactions_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, str]]:
        transactions = self._read_csv(self.transactions_file)
        result = []

        for trans in transactions:
            timestamp = trans.get('timestamp', '')
            if timestamp:
                date_part = timestamp.split()[0]
                if start_date <= date_part <= end_date:
                    result.append(trans)

        return result
    def get_all_transactions(self) -> List[Dict[str, str]]:
        return self._read_csv(self.transactions_file)

    def backup_data(self, backup_path: str=None) -> bool:
        if not backup_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(self.data_path, 'backups', timestamp)
        os.makedirs(backup_path, exist_ok=True)
        try:
            for file_name in ['users.csv', 'resources.csv', 'copies.csv', 'transactions.csv', 'fines.csv', 'borrowing_records.csv']:
                src = os.path.join(self.data_path, file_name)
                if os.path.exists(src):
                    dst = os.path.join(backup_path, file_name)
                    shutil.copy2(src, dst)
            return True
        except Exception as e:
            print(f"Error during backup: {e}")
            return False

    def restore_from_backup(self, backup_path: str) -> bool:
        if not os.path.exists(backup_path):
            print("Backup path does not exist.")
            return False
        try:
            for file_name in ['users.csv', 'resources.csv', 'copies.csv', 
                              'transactions.csv', 'fines.csv', 'borrowing_records.csv']:
                src = os.path.join(backup_path, file_name)
                if os.path.exists(src):
                    dst = os.path.join(self.data_path, file_name)
                    shutil.copy2(src, dst)
            return True
        except Exception as e:
            print(f"Error during restore: {e}")
            return False

    def get_statistics(self) -> Dict[str, int]:
        return {
            'users': len(self._read_csv(self.users_file)),
            'resources': len(self._read_csv(self.resources_file)),
            'copies': len(self._read_csv(self.copies_file)),
            'transactions': len(self._read_csv(self.transactions_file)),
            'fines': len(self._read_csv(self.fines_file)),
            'borrowing_records': len(self._read_csv(self.borrowing_records_file)),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def clear_all_data(self, confirm: bool = False) -> bool:
        if not confirm:
            return False
        self._initialize_csv_files()
        return True

    def import_from_dict(self, data: Dict[str, List[Dict[str, Any]]]) -> bool:
        try:
            if 'users' in data:
                for user in data['users']:
                    self.save_user(user)
            if 'resources' in data:
                for resource in data['resources']:
                    self.save_resource(resource)
            if 'copies' in data:
                for copy in data['copies']:
                    self.save_copy(copy)
            if 'transactions' in data:
                for transaction in data['transactions']:
                    self.log_transaction(transaction)
            if 'fines' in data:
                for fine in data['fines']:
                    self.save_fine_record(fine)
            if 'borrowing_records' in data:
                for record in data['borrowing_records']:
                    self.save_borrowing_record(record)
            return True
        except Exception as e:
            print(f"Error during import: {e}")
            return False
    

import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
import json
from logging.handlers import RotatingFileHandler
import traceback


class Logger:
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    COLORS = {
        'RESET': '\033[0m',
        'RED': '\033[91m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'PURPLE': '\033[95m',
        'CYAN': '\033[96m',
        'WHITE': '\033[97m'
    }
    def __init__(
            self,
            name: str = 'library_system',
            log_dir: str = 'logs',
            console_level: str = 'INFO',
            file_level: str = 'DEBUG',
            max_bytes: int = 10_485_760,
            backup_count: int = 5,
            use_colors: bool = True
    ):
        self.name = name
        self.log_dir = log_dir
        self.use_colors = use_colors
        os.makedirs(log_dir, exist_ok=True)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        self.logger.handlers.clear()
        self._setup_console_handler(console_level)
        self._setup_file_handler(file_level, max_bytes, backup_count)
        self.audit_file = os.path.join(log_dir, f"audit_{datetime.now().strftime('%Y%m%d')}.log")
        self.info(f"Logger '{name}' initialized. Log directory: {log_dir}")

    def _setup_console_handler(self, level: str):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.LOG_LEVELS.get(level, logging.INFO))

        if self.use_colors:
            formatter = logging.Formatter(
                f"{self.COLORS['CYAN']}%(asctime)s{self.COLORS['RESET']} | "
                f"%(color)s%(levelname)-8s{self.COLORS['RESET']} | "
                f"%(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        else:
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        if self.use_colors:
            old_factory = logging.getLogRecordFactory()
            def record_factory(*args, **kwargs):
                record = old_factory(*args, **kwargs)
                color_map = {
                    logging.DEBUG: self.COLORS['BLUE'],
                    logging.INFO: self.COLORS['GREEN'],
                    logging.WARNING: self.COLORS['YELLOW'],
                    logging.ERROR: self.COLORS['RED'],
                    logging.CRITICAL: self.COLORS['PURPLE']
                }
                record.color = color_map.get(record.levelno, '')
                return record
            logging.setLogRecordFactory(record_factory)

        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    def _setup_file_handler(self, level: str, max_bytes: int, backup_count: int):
        file_level = self.LOG_LEVELS.get(level, logging.DEBUG)
        error_handler = RotatingFileHandler(
            os.path.join(self.log_dir, f"{self.name}.log"),
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        error_handler.setLevel(file_level)
        error_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        self.logger.addHandler(error_handler)
        transaction_handler = RotatingFileHandler(
            os.path.join(self.log_dir, "transactions.log"),
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        transaction_handler.setLevel(logging.INFO)
        transaction_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        self.transaction_logger = logging.getLogger(f"{self.name}.trnsactions")
        self.transaction_logger.addHandler(transaction_handler)
        self.transaction_logger.setLevel(logging.INFO)
        self.transaction_logger.propagate = False

    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs):
        self.logger.critical(message, extra=kwargs)

    def exception(self, message: str, **kwargs):
        self.logger.exception(message, extra=kwargs)


    def log_transaction(self, transaction_type: str, user_id: str, details: Dict[str, Any]):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': transaction_type,
            'user_id': user_id,
            'details': details
        }
        self.transaction_logger.info(json.dumps(log_entry))
        self.info(f"Transaction: {transaction_type} - User: {user_id} - Details: {details}")

    def log_borrowing(self, user_id: str, book_id: str, copy_id: str, due_date: str):
        self.log_transaction(
            'ISSUE', user_id, {
                'book_id': book_id,
                'copy_id': copy_id,
                'due_date': due_date,
                'action': 'borrowed'
            }
        )
    def log_return(self, user_id: str, book_id: str, copy_id: str, fine_amount: float = 0.0):
        self.log_transaction('RETURN', user_id, {
            'copy_id': copy_id,
            'fine_amount': fine_amount,
            'action': 'returned'
        })
    def log_renewal(self, user_id: str, copy_id: str, new_due_date: str):
        self.log_transaction('RENEWAL', user_id, {
            'copy_id': copy_id,
            'new_due_date': new_due_date,
            'action': 'renewed'
        })
    def log_fine_payment(self, user_id: str, fine_id: str, amount: float):
        self.log_transaction('PAY_FINE', user_id, {
            'fine_id': fine_id,
            'amount': amount,
            'action': 'paid_fine'
        })
    def log_fine_waiver(self, admin_id: str, user_id: str, fine_id: str, amount: float):
        self.log_transaction('WAIVE_FINE', admin_id, {
            'target_user': user_id,
            'fine_id': fine_id,
            'amount': amount,
            'action': 'waived_fine'
        })


    def audit(self, action: str, user_id: str, details: Dict[str, Any], status: str = "SUCCESS"):
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'performed_by': user_id,
            'status': status,
            'details': details
        }
        try:
            with open(self.audit_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(audit_entry) + '\n')
        except Exception as e:
            self.error(f"Failed to write audit log: {e}")

        self.info(f"AUDIT: {action} - User: {user_id} - Status: {status}")

    def log_user_login(self, user_id: str, username: str, success: bool):
        if success:
            self.audit("LOGIN", user_id, {"username": username}, "SUCCESS")
            self.info(f"User login successful: {username} ({user_id})")
        else:
            self.audit("LOGIN", 'unknown', {"username": username}, "FAILURE")
            self.warning(f"Failed login attempt for user: {username}")

    def log_user_logout(self, user_id: str, username: str):
        self.info(f"User logout - ID: {user_id}, Username: {username}")
    def log_user_registration(self, user_id: str, username: str, role: int):
        self.info(f"New user registered - ID: {user_id}, Username: {username}, Role: {role}")
        self.audit("REGISTER_USER", user_id, {'username': username, 'role': role}, 'SUCCESS')
    def log_user_status_change(self, admin_id: str, user_id: str, old_status: int, new_status: int, reason: str = ""):
        self.info(
            f"User status changed - User: {user_id}, "
            f"Old: {old_status}, New: {new_status}, "
            f"By: {admin_id}, Reason: {reason}"
        )
        self.audit('CHANGE_USER_STATUS', admin_id, {
            'target_user': user_id,
            'old_status': old_status,
            'new_status': new_status,
            'reason': reason
        }, 'SUCCESS')

    def log_resource_creation(self, user_id: str, resource_id: int, title: str):
        self.info(f"New resource created - ID: {resource_id}, Title: {title}, By: {user_id}")
        self.audit('CREATE_RESOURCE', user_id, {
            'resource_id': resource_id,
            'title': title
        }, 'SUCCESS')

    def log_resource_update(self, user_id: str, resource_id: int, changes: Dict[str, Any]):
        self.info(f"Resource updated - ID: {resource_id}, By: {user_id}, Changes: {changes}")
        self.audit('UPDATE_RESOURCE', user_id, {
            'resource_id': resource_id,
            'changes': changes
        }, 'SUCCESS')

    def log_resource_deletion(self, user_id: str, resource_id: int, title: str):
        self.warning(f"Resource deleted - ID: {resource_id}, Title: {title}, By: {user_id}")
        self.audit('DELETE_RESOURCE', user_id,{
            'resource_id': resource_id,
            'title': title
        },'SUCCESS')

    def log_system_startup(self):
        self.info("=" * 60)
        self.info("LIBRARY MANAGEMENT SYSTEM STARTING UP")
        self.info("=" * 60)

    def log_system_shutdown(self):
        self.info("=" * 60)
        self.info("LIBRARY MANAGEMENT SYSTEM SHUTTING DOWN")
        self.info("=" * 60)

    def log_backup(self, user_id: str, backup_path: str, size: int):
        self.info(f"System backup created - Path: {backup_path}, Size: {size} bytes, By: {user_id}")
        self.audit('BACKUP', user_id, {
            'path': backup_path,
            'size': size
        }, 'SUCCESS')

    def log_restore(self, user_id: str, restore_path: str):
        self.warning(f"System restored from backup - Path: {restore_path}, By: {user_id}")
        self.audit('RESTORE', user_id, {'path': restore_path}, 'SUCCESS')


    def log_error_with_context(self, error: Exception, context: Dict[str, Any]):
        error_msg = f"Error: {str(error)}\nContext: {json.dumps(context, default=str)}"
        self.error(error_msg, exc_info=True)
        self.audit('SYSTEM_ERROR', 'system', {
            'error': str(error),
            'context': context,
            'traceback': traceback.format_exc()
        }, 'FAILURE')

    def get_recent_logs(self, level: str = "INFO", lines: int = 100) -> List[str]:
        log_file = os.path.join(self.log_dir, f"{self.name}.log")
        logs = []
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                logs = all_lines[-lines:]
        except FileNotFoundError:
            logs = ["No log file found"]
        except Exception as e:
            logs = [f"Error reading log file: {e}"]
        return logs
    def get_error_summary(self) -> Dict[str, Any]:
        error_file = os.path.join(self.log_dir, "errors.log")
        summary = {
            'total_errors': 0,
            'by_type': {},
            'recent_errors': []
        }
        try:
            with open(error_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'ERROR' in line:
                        summary['total_errors'] += 1
                        if ':' in line:
                            error_part = line.split('|')[-1].strip()
                            error_type = error_part.split(':')[0]
                            summary['by_type'][error_type] = summary['by_type'].get(error_type, 0) + 1
                            if len(summary['recent_errors']) < 10:
                                summary['recent_errors'].append(error_part)
        except FileNotFoundError:
            pass
        return summary
    
_logger_instance: Optional[Logger] = None

def get_logger(name: str = "library_system") -> Logger:
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger(name)
    return _logger_instance

def debug(msg: str, **kwargs):
    get_logger().debug(msg, **kwargs)

def info(msg: str, **kwargs):
    get_logger().info(msg, **kwargs)

def warning(msg: str, **kwargs):
    get_logger().warning(msg, **kwargs)

def error(msg: str, **kwargs):
    get_logger().error(msg, **kwargs)

def critical(msg: str, **kwargs):
    get_logger().critical(msg, **kwargs)

def exception(msg: str, **kwargs):
    get_logger().exception(msg, **kwargs)

def log_transaction(transaction_type: str, user_id: str, details: Dict[str, Any]):
    get_logger().log_transaction(transaction_type, user_id, details)

def audit(action: str, user_id: str, details: Dict[str, Any], status: str = "SUCCESS"):
    get_logger().audit(action, user_id, details, status)

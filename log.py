import os
import logging
from logging.handlers import RotatingFileHandler
import time

# Constants
LOG_DIR = "logs"
USER_LOG_DIR = os.path.join(LOG_DIR, "users")
TURN_ENGINE_LOG_FILE = os.path.join(LOG_DIR, "turn_engine.log")
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

# Ensure log directories exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(USER_LOG_DIR, exist_ok=True)

# Configure logging format
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def get_user_logger(username):
    """
    Get a logger for a specific user with file rotation.
    """
    logger = logging.getLogger(f"user_{username}")
    if not logger.handlers:
        log_file = os.path.join(USER_LOG_DIR, f"{username}.log")
        handler = RotatingFileHandler(log_file, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
        handler.setFormatter(log_format)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def get_turn_engine_logger():
    """
    Get the logger for the turn engine with file rotation.
    """
    logger = logging.getLogger("turn_engine")
    if not logger.handlers:
        handler = RotatingFileHandler(TURN_ENGINE_LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
        handler.setFormatter(log_format)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def log_user_action(username, action, details=None):
    """
    Log a user action.
    """
    logger = get_user_logger(username)
    log_message = f"Action: {action}"
    if details:
        log_message += f" - Details: {details}"
    logger.info(log_message)

def log_turn_engine_event(event, details=None):
    """
    Log a turn engine event.
    """
    logger = get_turn_engine_logger()
    log_message = f"Event: {event}"
    if details:
        log_message += f" - Details: {details}"
    logger.info(log_message)

# Example usage
if __name__ == "__main__":
    # Simulate some logs
    log_user_action("alice", "login")
    time.sleep(1)
    log_user_action("bob", "move", "x: 10, y: 15")
    time.sleep(1)
    log_turn_engine_event("turn_processed", "Turn 42")
    time.sleep(1)
    log_user_action("alice", "logout")

    print("Logging examples complete. Check the logs directory for output.")
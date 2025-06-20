import redis
import hashlib
import os
import json
import datetime
from datetime import UTC
import asyncio


def await_redis_result(result):
    """
    Helper function to handle awaiting Redis results if they are Awaitable objects.

    Args:
        result: The result from a Redis operation, which might be an Awaitable

    Returns:
        The actual result value
    """
    # Check if the result is an Awaitable (has 'done' method)
    if hasattr(result, 'done') and callable(getattr(result, 'done')):
        try:
            # If we're in an event loop, await the result
            if asyncio.get_event_loop().is_running():
                return asyncio.get_event_loop().run_until_complete(result)
            else:
                # Create a new event loop if needed
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(result)
                finally:
                    loop.close()
        except Exception as await_error:
            print(f"Error awaiting Redis result: {str(await_error)}")
            return None
    return result


# Redis connection parameters
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
REDIS_SSL = os.environ.get('REDIS_SSL', 'False').lower() == 'true'

# User-related keys
USER_PREFIX = "user:"
USER_AUTH_PREFIX = "auth:"
USER_DATA_PREFIX = "data:"


def get_redis_connection():
    """
    Establish a connection to Redis.

    Returns:
        redis.Redis: Redis connection object
    """
    try:
        # For local development
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            ssl=REDIS_SSL,
            decode_responses=True  # Automatically decode responses to strings
        )
        # Test connection
        ping_result = r.ping()
        if await_redis_result(ping_result) is not True:
            print(f"Warning: Redis ping did not return True")
        print(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        return r
    except redis.ConnectionError as e:
        print(f"Error connecting to Redis: {str(e)}")
        print("Make sure Redis is running and accessible.")
        return None
    except Exception as e:
        print(f"Unexpected error connecting to Redis: {str(e)}")
        return None


def hash_password(password):
    """
    Hash a password using SHA-256.
    Args:
        password (str): The password to hash
    Returns:
        str: The hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()


def user_exists(username):
    """
    Check if a user exists in Redis.
    Args:
        username (str): The username to check
    Returns:
        bool: True if the user exists, False otherwise
    """
    r = get_redis_connection()
    if not r:
        return False
    result = r.exists(f"{USER_AUTH_PREFIX}{username}")
    return await_redis_result(result)


def add_user(username, password):
    """
    Add a new user to Redis.
    Args:
        username (str): The username for the new user
        password (str): The password for the new user
    Returns:
        bool: True if the user was added successfully, False otherwise
    """
    r = get_redis_connection()
    if not r:
        return False
    # Check if user already exists
    if user_exists(username):
        print(f"User {username} already exists")
        return False
    try:
        # Hash the password
        hashed_password = hash_password(password)
        # Store the user credentials
        result1 = r.set(f"{USER_AUTH_PREFIX}{username}", hashed_password)
        await_redis_result(result1)
        # Store user data (creation timestamp)
        user_data = {
            "created": datetime.datetime.now(UTC).isoformat(),
            "last_login": None
        }
        result2 = r.set(f"{USER_DATA_PREFIX}{username}", json.dumps(user_data))
        await_redis_result(result2)
        print(f"User {username} added successfully")
        return True
    except Exception as e:
        print(f"Error adding user {username}: {str(e)}")
        return False


def authenticate_user(username, password):
    """
    Authenticate a user with username and password.
    Args:
        username (str): The username to authenticate
        password (str): The password to authenticate
    Returns:
        bool: True if authentication is successful, False otherwise
    """
    r = get_redis_connection()
    if not r:
        return False
    # Check if user exists
    if not user_exists(username):
        print(f"User {username} does not exist")
        return False
    # Get stored password hash
    stored_hash = await_redis_result(r.get(f"{USER_AUTH_PREFIX}{username}"))
    if stored_hash is None:
        return False

    # Hash the provided password
    input_hash = hash_password(password)
    # Compare hashes
    if stored_hash == input_hash:
        # Update last login timestamp
        try:
            # Get user data
            user_data_raw = await_redis_result(r.get(f"{USER_DATA_PREFIX}{username}"))

            # Parse the JSON data
            user_data = json.loads(user_data_raw or '{}')
            user_data["last_login"] = datetime.datetime.now(UTC).isoformat()
            result = r.set(f"{USER_DATA_PREFIX}{username}", json.dumps(user_data))
            await_redis_result(result)
        except Exception as e:
            print(f"Error updating last login for {username}: {str(e)}")
        return True
    else:
        return False


def register_user(username, password):
    """
    Register a new user (wrapper for add_user).
    
    Args:
        username (str): The username for the new user
        password (str): The password for the new user
    
    Returns:
        tuple: (bool, str) indicating success and a message
    """
    if user_exists(username):
        return False, f"User {username} already exists"
    
    success = add_user(username, password)
    if success:
        return True, f"User {username} registered successfully"
    else:
        return False, "Registration failed"


def get_user_data(username):
    """
    Get user data from Redis.

    Args:
        username (str): The username to get data for

    Returns:
        dict: User data dictionary or None if user doesn't exist
    """
    r = get_redis_connection()
    if not r:
        return None

    # Check if user exists
    if not user_exists(username):
        print(f"User {username} does not exist")
        return None

    # Get user data
    try:
        user_data = await_redis_result(r.get(f"{USER_DATA_PREFIX}{username}"))
        if user_data:
            return json.loads(user_data)
        return {}
    except Exception as e:
        print(f"Error getting data for user {username}: {str(e)}")
        return None

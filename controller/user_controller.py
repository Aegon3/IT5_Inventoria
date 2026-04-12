from model.database import DatabaseHandler


class UserController:
    """
    Dedicated controller for all user-related actions.
    Keeps authentication, user management, and password logic OUT of views.
    """

    def __init__(self, db_config: dict):
        self.db_config = db_config

    # -----------------------------------------------------------------------
    # AUTHENTICATION (extracted from view/login.py → authenticate())
    # -----------------------------------------------------------------------

    def authenticate(self, username: str, password: str):
        """
        Validate login credentials against the database.

        Args:
            username (str): The entered username.
            password (str): The entered password.

        Returns:
            tuple: (success: bool, user_data: dict | None, error_message: str)
                - On success: (True, {'username', 'full_name', 'role', 'password'}, "")
                - On failure: (False, None, "reason string")
        """
        # --- Validation (was inline in login.py) ---
        if not username.strip():
            return False, None, "Username cannot be empty."
        if not password.strip():
            return False, None, "Password cannot be empty."

        # --- Database check (was inline in login.py) ---
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return False, None, "Failed to connect to database."

        try:
            query = "SELECT * FROM users WHERE username = %s AND password = %s"
            db.cursor.execute(query, (username.strip(), password.strip()))
            user = db.cursor.fetchone()

            if user:
                user_data = {
                    'username': user['username'],
                    'full_name': user.get('full_name', ''),
                    'role': user.get('role', 'staff'),
                    'password': user.get('password', '')
                }
                return True, user_data, ""
            else:
                return False, None, "Invalid username or password."

        except Exception as e:
            return False, None, f"Authentication error: {str(e)}"
        finally:
            db.disconnect()

    # -----------------------------------------------------------------------
    # PASSWORD UPDATE (extracted from view/settings.py → save_password())
    # -----------------------------------------------------------------------

    def update_password(self, username: str, new_password: str):
        """
        Update the password for a given user.

        Args:
            username (str): The user whose password will be updated.
            new_password (str): The new password to set.

        Returns:
            tuple: (success: bool, message: str)
        """
        # --- Validation (was inline in settings.py) ---
        if not new_password.strip():
            return False, "Password cannot be empty."

        if len(new_password.strip()) < 4:
            return False, "Password must be at least 4 characters long."

        # --- Database update (was inline in settings.py) ---
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return False, "Failed to connect to database."

        try:
            query = "UPDATE users SET password = %s WHERE username = %s"
            db.cursor.execute(query, (new_password.strip(), username))
            db.conn.commit()

            if db.cursor.rowcount > 0:
                return True, "Password updated successfully."
            else:
                return False, f"User '{username}' not found."

        except Exception as e:
            return False, f"Failed to update password: {str(e)}"
        finally:
            db.disconnect()

    # -----------------------------------------------------------------------
    # CREATE USER (extracted from view/create_user_dialog.py → create_user())
    # -----------------------------------------------------------------------

    def create_user(self, username: str, fullname: str, password: str, confirm_password: str, role: str):
        """
        Validate and create a new user account (admin only action).

        Args:
            username (str): Desired username (must be unique, min 3 chars).
            fullname (str): Full name of the user.
            password (str): Password (min 4 chars).
            confirm_password (str): Must match password.
            role (str): Either 'admin' or 'staff'.

        Returns:
            tuple: (success: bool, message: str)
        """
        # --- Validation (was inline in create_user_dialog.py) ---
        username = username.strip()
        fullname = fullname.strip()

        if not username:
            return False, "Username cannot be empty."
        if len(username) < 3:
            return False, "Username must be at least 3 characters long."
        if not fullname:
            return False, "Full name cannot be empty."
        if not password:
            return False, "Password cannot be empty."
        if len(password) < 4:
            return False, "Password must be at least 4 characters long."
        if password != confirm_password:
            return False, "Passwords do not match."
        if role not in ('admin', 'staff'):
            return False, "Role must be 'admin' or 'staff'."

        # --- Database operations (was inline in create_user_dialog.py) ---
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return False, "Failed to connect to database."

        try:
            # Check for duplicate username
            db.cursor.execute(
                "SELECT COUNT(*) as count FROM users WHERE username = %s",
                (username,)
            )
            result = db.cursor.fetchone()
            count = result.get('count') if isinstance(result, dict) else result[0]

            if count > 0:
                return False, f"Username '{username}' already exists. Please choose a different username."

            # Insert the new user
            db.cursor.execute(
                "INSERT INTO users (username, password, full_name, role) VALUES (%s, %s, %s, %s)",
                (username, password, fullname, role)
            )
            db.conn.commit()

            print(f" New user created: {username} ({role})")
            return True, f"User '{username}' ({role.upper()}) created successfully."

        except Exception as e:
            return False, f"Failed to create user: {str(e)}"
        finally:
            db.disconnect()

    # -----------------------------------------------------------------------
    # DELETE USER (extracted from view/create_user_dialog.py → delete_user())
    # -----------------------------------------------------------------------

    def delete_user(self, user_id: int, username: str):
        """
        Delete a user account by ID (admin only action).
        Protected users ('admin', 'staff') cannot be deleted.

        Args:
            user_id (int): The database ID of the user to delete.
            username (str): The username (used to block protected accounts).

        Returns:
            tuple: (success: bool, message: str)
        """
        # --- Guard: never delete the default protected accounts ---
        if username in ('admin', 'staff'):
            return False, f"User '{username}' is protected and cannot be deleted."

        # --- Database delete (was inline in create_user_dialog.py) ---
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return False, "Failed to connect to database."

        try:
            db.cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            db.conn.commit()

            if db.cursor.rowcount > 0:
                print(f" User deleted: {username}")
                return True, f"User '{username}' deleted successfully."
            else:
                return False, f"User with ID {user_id} not found."

        except Exception as e:
            return False, f"Failed to delete user: {str(e)}"
        finally:
            db.disconnect()

    # -----------------------------------------------------------------------
    # GET ALL USERS (extracted from view/create_user_dialog.py → load_users())
    # -----------------------------------------------------------------------

    def get_all_users(self):
        """
        Retrieve all users from the database.

        Returns:
            list[dict]: List of user dicts with keys: id, username, full_name, role.
                        Returns empty list on error.
        """
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            print(" Cannot load users: Database not connected")
            return []

        try:
            db.cursor.execute("SELECT id, username, full_name, role FROM users ORDER BY id")
            users = db.cursor.fetchall()
            return users if users else []

        except Exception as e:
            print(f" Error loading users: {e}")
            return []
        finally:
            db.disconnect()
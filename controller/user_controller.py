"""
User Controller - Handles ALL user-related database operations.
NO QMessageBox imports.
"""

from model.database import DatabaseHandler


class UserController:

    def __init__(self, db_config: dict):
        self.db_config = db_config

    def authenticate(self, username: str, password: str):
        if not username.strip():
            return False, None, "Username cannot be empty."
        if not password.strip():
            return False, None, "Password cannot be empty."

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

    def update_password(self, username: str, new_password: str):
        if not new_password.strip():
            return False, "Password cannot be empty."

        if len(new_password.strip()) < 4:
            return False, "Password must be at least 4 characters long."

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

    def create_user(self, username: str, fullname: str, password: str, confirm_password: str, role: str):
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

        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return False, "Failed to connect to database."

        try:
            db.cursor.execute(
                "SELECT COUNT(*) as count FROM users WHERE username = %s",
                (username,)
            )
            result = db.cursor.fetchone()
            count = result.get('count') if isinstance(result, dict) else result[0]

            if count > 0:
                return False, f"Username '{username}' already exists. Please choose a different username."

            db.cursor.execute(
                "INSERT INTO users (username, password, full_name, role) VALUES (%s, %s, %s, %s)",
                (username, password, fullname, role)
            )
            db.conn.commit()
            return True, f"User '{username}' ({role.upper()}) created successfully."
        except Exception as e:
            return False, f"Failed to create user: {str(e)}"
        finally:
            db.disconnect()

    def delete_user(self, user_id: int, username: str):
        if username in ('admin', 'staff'):
            return False, f"User '{username}' is protected and cannot be deleted."

        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return False, "Failed to connect to database."

        try:
            db.cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            db.conn.commit()

            if db.cursor.rowcount > 0:
                return True, f"User '{username}' deleted successfully."
            else:
                return False, f"User with ID {user_id} not found."
        except Exception as e:
            return False, f"Failed to delete user: {str(e)}"
        finally:
            db.disconnect()

    def get_all_users(self):
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return []

        try:
            db.cursor.execute("SELECT id, username, full_name, role FROM users ORDER BY id")
            users = db.cursor.fetchall()
            return users if users else []
        except Exception as e:
            print(f"Error loading users: {e}")
            return []
        finally:
            db.disconnect()
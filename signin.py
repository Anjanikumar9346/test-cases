import unittest

# ---- Sample application login function (replace with your real function) ----
def login(username: str, password: str) -> str:
    """
    Simulates a login function.
    Replace this with your actual authentication logic.
    """
    valid_users = {
        "admin": "admin123",
        "user": "password123"
    }
    if username not in valid_users:
        raise ValueError("Invalid username or password")
    if valid_users[username] != password:
        raise ValueError("Invalid username or password")
    return "Login successful"


# ---- Unit Tests ----
class TestLoginInvalidCredentials(unittest.TestCase):

    def test_invalid_username_and_password(self):
        """Entering completely invalid username and password should fail"""
        with self.assertRaises(ValueError) as context:
            login("wrong_user", "wrong_pass")
        self.assertIn("Invalid username or password", str(context.exception))

    def test_invalid_username(self):
        """Invalid username with valid password should fail"""
        with self.assertRaises(ValueError) as context:
            login("fake_user", "admin123")
        self.assertIn("Invalid username or password", str(context.exception))

    def test_invalid_password(self):
        """Valid username with wrong password should fail"""
        with self.assertRaises(ValueError) as context:
            login("admin", "wrong_pass")
        self.assertIn("Invalid username or password", str(context.exception))


if __name__ == "__main__":
    unittest.main()

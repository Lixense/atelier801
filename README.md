# Atelier801 Python Library

A comprehensive Python library for automating Atelier 801 account operations including login, email management, certification, and account status checking.

![Python Version](https://img.shields.io/pypi/pyversions/atelier801)
![License](https://img.shields.io/pypi/l/atelier801)
![Version](https://img.shields.io/pypi/v/atelier801)

## Features

- 🔐 Account login with encrypted password
- 📧 Email change automation (uncertified accounts only)
- ✅ Certification request and code submission
- 🔍 Account status checking (certified, banned, etc.)
- 📬 MailTM integration for temporary emails
- 🛡️ Dynamic CSRF token handling
- 🔗 Save email associations with Atelier accounts

## Installation

```bash
pip install atelier801
```

Or install from source:

```bash
git clone https://github.com/yourusername/atelier801.git
cd atelier801
pip install -e .
```

## Quick Start

### Basic Login

```python
from atelier801 import Atelier801

client = Atelier801()
if client.login("Player#1234", "mypassword"):
    print("Logged in!")
```

### Check Account Status

```python
from atelier801 import Atelier801

client = Atelier801()
client.login("Player#1234", "mypassword")

status = client.get_account_status()
print(f"Email: {status['email']}")
print(f"Certified: {status['certified']}")
print(f"Banned: {status['is_banned']}")
```

### Full Certification Flow

**Important:** Email change only works for uncertified accounts. Certified accounts must use the game UI.

```python
from atelier801 import Atelier801
from mailtm import MailTM
import time

# Create temp email
mailtm = MailTM()
email, password = mailtm.create_account()

# Login to Atelier
client = Atelier801()
client.login("Player#1234", "mypassword")

# Check if account is certified (email change won't work if certified)
status = client.get_account_status()
if status['certified']:
    print("Account is already certified - use game UI to change email")
else:
    # Change email
    result = client.change_email(email)
    if result['success']:
        print(f"Email change requested: {result['message']}")
        
        # Wait for validation email
        mailtm.login(email, password)
        validation_link = mailtm.get_validation_link(timeout=60)
        
        if validation_link:
            # Validate email
            client.validate_email(validation_link)
            print("Email validated!")
            
            # Verify email changed (check if new email prefix appears)
            time.sleep(2)  # Wait for page update
            if client.check_email_changed(email[:3]):
                print("Email change confirmed!")
                
                # Save association
                mailtm.save_with_association(email, password, "Player#1234")
                print("Saved to em.txt")
            else:
                print("Email change may not have completed")
        else:
            print("No validation email received")
```

## API Reference

### Atelier801 Client

#### `Atelier801(session=None)`

Create a new Atelier801 client.

**Parameters:**
- `session` (requests.Session, optional): Custom session to use

**Example:**
```python
client = Atelier801()
# or with custom session
sess = requests.Session()
client = Atelier801(session=sess)
```

#### `login(username, password)`

Login to Atelier 801 account.

**Parameters:**
- `username` (str): Username with discriminator (e.g., "Player#1234")
- `password` (str): Account password

**Returns:** `bool` - True if login successful

**Example:**
```python
client = Atelier801()
client.login("Player#1234", "mypassword")
```

#### `get_account_status(force_refresh=False)`

Get comprehensive account status.

**Parameters:**
- `force_refresh` (bool): Force refresh cached data (default: False)

**Returns:** `dict` with keys:
- `username` (str): Full username
- `email` (str): Current email (masked)
- `email_validated` (bool): Email validation status
- `certified` (bool): Certification status
- `registration_date` (str): Registration date
- `is_banned` (bool): Ban status
- `ban_info` (dict): Ban details if banned

**Example:**
```python
status = client.get_account_status()
print(status['email'])       # "p***@g***.com"
print(status['certified'])   # True/False
print(status['is_banned'])   # True/False
```

#### `change_email(new_email)`

Change account email address.

**Note:** Only works for uncertified accounts.

**Parameters:**
- `new_email` (str): New email address

**Returns:** `dict` with keys:
- `success` (bool): Operation success
- `message` (str): Response message
- `validation_sent` (bool): Whether validation email sent

**Example:**
```python
result = client.change_email("newemail@example.com")
if result['success']:
    print("Email change requested!")
```

#### `check_email_changed(expected_email_prefix)`

Check if email has been changed successfully.

**Parameters:**
- `expected_email_prefix` (str): First few characters of expected new email

**Returns:** `bool` - True if email prefix matches

**Example:**
```python
if client.check_email_changed("abc"):
    print("Email changed successfully!")
```

#### `validate_email(validation_link)`

Visit validation link to confirm email.

**Parameters:**
- `validation_link` (str): Full validation URL from email

**Returns:** `bool` - True if validation successful

**Example:**
```python
link = mailtm.get_validation_link()
client.validate_email(link)
```

#### `request_certification()`

Request certification email.

**Returns:** `dict` with keys:
- `success` (bool): Request success
- `message` (str): Response message
- `token_name` (str): CSRF token name used
- `token_value` (str): CSRF token value used

**Example:**
```python
result = client.request_certification()
if result['success']:
    print("Certification email sent!")
```

#### `submit_certification_code(code)`

Submit certification code from email.

**Parameters:**
- `code` (str): Certification code

**Returns:** `dict` with keys:
- `success` (bool): Submission success
- `message` (str): Response message

**Example:**
```python
code = mailtm.get_certification_code()
result = client.submit_certification_code(code)
print(f"Certified: {result['success']}")
```

#### `is_logged_in()`

Check login status.

**Returns:** `bool` - Login status

**Example:**
```python
if client.is_logged_in():
    print("Logged in!")
```

#### `logout()`

Logout from current session.

**Returns:** `bool` - Logout success

**Example:**
```python
client.logout()
```

---

### MailTM Client

#### `MailTM(credentials_file="mailtm_accounts.txt")`

Create MailTM client.

**Parameters:**
- `credentials_file` (str): Path for credentials storage

**Example:**
```python
mailtm = MailTM()
# or custom file
mailtm = MailTM(credentials_file="my_accounts.txt")
```

#### `create_account(password=None, domain=None)`

Create new MailTM account.

**Parameters:**
- `password` (str, optional): Custom password
- `domain` (str, optional): Specific domain

**Returns:** `tuple` - (email, password)

**Example:**
```python
email, password = mailtm.create_account()
# or with custom password
email, password = mailtm.create_account(password="mypassword123")
```

#### `login(email, password)`

Login to MailTM.

**Parameters:**
- `email` (str): Email address
- `password` (str): Password

**Example:**
```python
mailtm.login("test@wshu.net", "password")
```

#### `get_inbox(limit=10)`

Get inbox messages.

**Parameters:**
- `limit` (int): Max messages to return

**Returns:** `list` - Message list

**Example:**
```python
inbox = mailtm.get_inbox()
for msg in inbox:
    print(msg['subject'])
```

#### `get_message(message_id)`

Get specific message.

**Parameters:**
- `message_id` (str): Message ID

**Returns:** `dict` - Full message data

**Example:**
```python
msg = mailtm.get_message("abc123")
print(msg['text'])  # Plain text
print(msg['html'])  # HTML content
```

#### `wait_for_email(sender_contains=None, subject_contains=None, timeout=60, interval=2)`

Wait for email matching criteria.

**Parameters:**
- `sender_contains` (str, optional): Sender filter
- `subject_contains` (str, optional): Subject filter
- `timeout` (int): Max wait seconds
- `interval` (int): Check interval seconds

**Returns:** `dict` - Full message or None

**Example:**
```python
msg = mailtm.wait_for_email(
    sender_contains="atelier801",
    subject_contains="validation",
    timeout=120
)
```

#### `get_validation_link(timeout=60)`

Get validation link from email.

**Parameters:**
- `timeout` (int): Max wait seconds

**Returns:** `str` - Validation URL or None

**Example:**
```python
link = mailtm.get_validation_link()
```

#### `get_certification_code(timeout=60)`

Get certification code from email.

**Parameters:**
- `timeout` (int): Max wait seconds

**Returns:** `str` - Certification code or None

**Example:**
```python
code = mailtm.get_certification_code()
```

#### `save_with_association(email, password, atelier_account, filename="em.txt")`

Save MailTM credentials with associated Atelier account.

**Parameters:**
- `email` (str): MailTM email
- `password` (str): MailTM password
- `atelier_account` (str): Atelier 801 account
- `filename` (str): File to save to

**Example:**
```python
mailtm.save_with_association("test@wshu.net", "pass123", "Player#1234")
```

#### `load_associations(filename="em.txt")`

Load all saved account associations.

**Parameters:**
- `filename` (str): File to load from

**Returns:** `list` - [(mailtm_email, mailtm_password, atelier_account), ...]

**Example:**
```python
assocs = MailTM.load_associations()
for email, pwd, account in assocs:
    print(f"{email} -> {account}")
```

#### `load_all_accounts()`

Load all saved accounts.

**Returns:** `list` - [(email, password), ...]

**Example:**
```python
accounts = MailTM.load_all_accounts()
for email, pwd in accounts:
    print(email)
```

## File Formats

### mailtm_accounts.txt
```
email:password
email:password
```

### em.txt (with associations)
```
email:password:account#
email:password:Account#1505
```

## Important Notes

- **Email change only works for uncertified accounts** - Certified accounts must use the game UI
- Always check if the account is certified before attempting email change
- Use `check_email_changed()` to verify email change success after validation
- Certification code submission may fail if the code is expired or already used

## Error Handling

```python
from atelier801 import Atelier801
from mailtm import MailTM

try:
    client = Atelier801()
    client.login("Player#1234", "mypassword")
    
    status = client.get_account_status()
    if status['is_banned']:
        print(f"Banned! Reason: {status['ban_info']['reason']}")
        
except Exception as e:
    print(f"Error: {e}")
```

## License

MIT License

## Support

For issues and feature requests, please open an issue on GitHub.
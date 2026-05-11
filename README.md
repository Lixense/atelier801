# Atelier801 Python Library

A comprehensive Python library for automating Atelier 801 account operations including login, email management, certification, and account status checking.

![Python Version](https://img.shields.io/pypi/pyversions/atelier801)
![License](https://img.shields.io/pypi/l/atelier801)
![Version](https://img.shields.io/pypi/v/atelier801)

## Features

- Account login with encrypted password
- Email change automation
- Certification request and code submission
- Account status checking (certified, banned, etc.)
- MailTM integration for temporary emails
- Dynamic CSRF token handling
- Save email associations with Atelier accounts

## Installation

```bash
pip install atelier801
```

Or install from source:

```bash
git clone https://github.com/Lixense/atelier801.git
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

### Change Email with MailTM

```python
from atelier801 import Atelier801
from mailtm import MailTM

# Create temp email
mailtm = MailTM()
email, password = mailtm.create_account()

# Login to Atelier
client = Atelier801()
client.login("Player#1234", "mypassword")

# Change email
result = client.change_email(email)
print(f"Email change: {result['message']}")

# Save association: email:password:account#
mailtm.save_with_association(email, password, "Player#1234")
```

### Full Certification Flow

```python
from atelier801 import Atelier801
from mailtm import MailTM

# Create temp email
mailtm = MailTM()
email, password = mailtm.create_account()

# Login to Atelier
client = Atelier801()
client.login("Player#1234", "mypassword")

# Change email
client.change_email(email)

# Validate email
validation_link = mailtm.get_validation_link()
client.validate_email(validation_link)

# Request certification
client.request_certification()

# Get code and submit
code = mailtm.get_certification_code()
result = client.submit_certification_code(code)
print(f"Certified: {result['success']}")
```

## API Reference

### Atelier801 Client

#### `Atelier801(session=None)`
Create a new Atelier801 client.

#### `login(username, password)`
Login to Atelier 801 account.

#### `get_account_status(force_refresh=False)`
Get comprehensive account status.

Returns:
- `username` - Full username
- `email` - Current email (masked)
- `email_validated` - Email validation status
- `certified` - Certification status
- `registration_date` - Registration date
- `is_banned` - Ban status
- `ban_info` - Ban details if banned

#### `change_email(new_email)`
Change account email address.

#### `validate_email(validation_link)`
Visit validation link to confirm email.

#### `request_certification()`
Request certification email.

#### `submit_certification_code(code)`
Submit certification code from email.

---

### MailTM Client

#### `MailTM(credentials_file="mailtm_accounts.txt")`
Create MailTM client.

#### `create_account(password=None, domain=None)`
Create new MailTM account. Returns (email, password).

#### `login(email, password)`
Login to existing MailTM account.

#### `get_inbox(limit=10)`
Get inbox messages.

#### `wait_for_email(sender_contains=None, subject_contains=None, timeout=60)`
Wait for email matching criteria.

#### `get_validation_link(timeout=60)`
Get validation link from email.

#### `get_certification_code(timeout=60)`
Get certification code from email.

#### `save_with_association(email, password, atelier_account, filename="em.txt")`
Save MailTM credentials with associated Atelier account.

#### `load_associations(filename="em.txt")`
Load all saved account associations.

Returns: [(mailtm_email, mailtm_password, atelier_account), ...]

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

## Error Handling

```python
from atelier801 import Atelier801

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
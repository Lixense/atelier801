# Atelier801 Python Library

[![Python Version](https://img.shields.io/pypi/pyversions/atelier801)](https://pypi.org/project/atelier801/)
[![License](https://img.shields.io/pypi/l/atelier801)](https://pypi.org/project/atelier801/)
[![Version](https://img.shields.io/pypi/v/atelier801)](https://pypi.org/project/atelier801/)
[![Stars](https://img.shields.io/github/stars/Lixense/atelier801)](https://github.com/Lixense/atelier801/stargazers)

A comprehensive Python library for automating Atelier 801 account operations including login, email management, certification, and account status checking.

---

## Features

| Feature | Description |
|---------|-------------|
| **Secure Login** | Login with encrypted password (SHAKikoo algorithm) |
| **Email Management** | Change account email to temporary MailTM addresses |
| **Certification** | Request and submit certification codes |
| **Status Check** | Check if account has validated email, banned, or valid |
| **Email Verification** | Validate email changes via link |
| **Account Storage** | Save email associations for multiple accounts |

---

## Installation

### From PyPI (Recommended)
```bash
pip install atelier801
```

### From Source
```bash
git clone https://github.com/Lixense/atelier801.git
cd atelier801
pip install -e .
```

---

## Quick Start

### Login to Account
```python
from atelier801 import Atelier801

client = Atelier801()
if client.login("Player#1234", "mypassword"):
    print("Successfully logged in!")
```

### Check Account Status
```python
client = Atelier801()
client.login("Player#1234", "mypassword")

status = client.get_account_status()
print(f"Email: {status['email']}")
print(f"Has Validated Email: {status['certified']}")
print(f"Banned: {status['is_banned']}")
```

---

## Important: Email Change Restriction

Email change via API only works for accounts that **do NOT have a validated email address**.

### What does this mean?

| Account State | Description | API Email Change |
|--------------|-------------|------------------|
| **No Validated Email** | "Nouveau mail" shown - email not verified yet | **Works** |
| **Has Validated Email** | "Vous devez d'abord certifier" - email is verified | **Does NOT work** |

### How to check?

```python
client = Atelier801()
client.login("Player#1234", "password")

html = client.get_account_page()

if 'Nouveau mail' in html:
    print("Can change email - not verified yet")
elif 'Vous devez d\'abord certifier' in html:
    print("Has validated email - cannot change via API")
else:
    print("Cannot change email")
```

This is an Atelier 801 website restriction, not a library limitation.

---

## Full Example: Email Change Flow

```python
from atelier801 import Atelier801
from mailtm import MailTM
import time

def change_email_flow(username, password):
    # Step 1: Create MailTM account
    mailtm = MailTM()
    email, mailtm_password = mailtm.create_account()
    print(f"Created: {email}")
    
    # Step 2: Login to Atelier 801
    client = Atelier801()
    client.login(username, password)
    
    # Step 3: Check if can change email
    html = client.get_account_page()
    if 'Nouveau mail' in html:
        # Step 4: Change email
        result = client.change_email(email)
        print(result['message'])
        
        # Step 5: Get validation link
        mailtm.login(email, mailtm_password)
        link = mailtm.get_validation_link(timeout=60)
        
        if link:
            # Step 6: Validate
            client.validate_email(link)
            time.sleep(2)
            
            # Step 7: Verify change
            if client.check_email_changed(email):
                print(f"SUCCESS! Email changed to {email[0]}***")
                
                # Save for later
                mailtm.save_with_association(email, mailtm_password, username)
            else:
                print("Change not confirmed")
    elif 'Vous devez d\'abord certifier' in html:
        print("Has validated email - change via game UI")
    else:
        print("No email form available")

# Run
change_email_flow("Player#1234", "mypassword")
```

---

## API Reference

### Atelier801 Client

#### `Atelier801(session=None)`
Create a new client instance.

```python
client = Atelier801()
```

#### `login(username, password)`
Login to account. Returns `bool`.

```python
if client.login("Player#1234", "password"):
    print("Logged in!")
```

#### `get_account_status(force_refresh=False)`
Get account info. Returns dict with:
- `username` - Account name
- `email` - Masked email (e.g., "p***@w***.net")
- `certified` - Has validated email
- `is_banned` - Ban status

```python
status = client.get_account_status()
print(status['email'])
print(status['certified'])
```

#### `change_email(new_email)`
Request email change. Returns dict with `success` and `message`.

```python
result = client.change_email("newemail@example.com")
print(result['message'])
```

#### `validate_email(validation_link)`
Visit validation link from email. Returns `bool`.

```python
client.validate_email("https://atelier801.com/validate-email?id=...")
```

#### `check_email_changed(new_email)`
Verify email was changed. Returns `bool`.

```python
if client.check_email_changed("newemail@example.com"):
    print("Email changed successfully!")
```

---

### MailTM Client

#### `MailTM(credentials_file="mailtm_accounts.txt")`
Create MailTM client.

```python
mailtm = MailTM()
```

#### `create_account(password=None, domain=None)`
Create new temporary email. Returns `(email, password)`.

```python
email, password = mailtm.create_account()
```

#### `login(email, password)`
Login to MailTM account.

```python
mailtm.login(email, password)
```

#### `get_validation_link(timeout=60)`
Get email validation link from inbox. Returns `str` or `None`.

```python
link = mailtm.get_validation_link()
```

#### `save_with_association(email, password, atelier_account, filename="em.txt")`
Save MailTM credentials with associated Atelier account.

```python
mailtm.save_with_association(email, password, "Player#1234")
```

---

## File Formats

### mailtm_accounts.txt
```
email:password
```

### em.txt (Associations)
```
email:password:account#
```

---

## License

MIT License - See LICENSE file for details.

---

## Support

For issues and feature requests, please open an issue on GitHub.

[![Stars](https://img.shields.io/github/forks/Lixense/atelier801?style=social)](https://github.com/Lixense/atelier801)
[![Stars](https://img.shields.io/github/stars/Lixense/atelier801?style=social)](https://github.com/Lixense/atelier801)
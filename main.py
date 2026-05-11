"""
Atelier 801 Email Change Automation
=====================================
Fast flow: Login → Create MailTM → Change Email → Validate Link → Verify Change
"""

from atelier801 import Atelier801
from mailtm import MailTM
import time


def change_email_for_account(username, password, existing_mailtm=None):
    """
    Change Atelier 801 account email to a MailTM address.
    Works for uncertified accounts only.
    
    Args:
        username: Atelier 801 username (e.g., "Hora#1469")
        password: Atelier 801 password
        existing_mailtm: Optional tuple (email, password) to reuse MailTM
    
    Returns:
        dict with status and details
    """
    result = {
        'success': False,
        'mailtm_email': None,
        'email_changed': False,
        'error': None
    }
    
    # Step 1: Create or use existing MailTM
    mailtm = MailTM()
    if existing_mailtm:
        mailtm_email, mailtm_password = existing_mailtm
        print(f"[1/4] Using existing MailTM: {mailtm_email}")
    else:
        mailtm_email, mailtm_password = mailtm.create_account()
        print(f"[1/4] Created MailTM: {mailtm_email}")
    
    result['mailtm_email'] = mailtm_email
    
    # Step 2: Login to Atelier 801
    print(f"[2/4] Logging into Atelier 801 as {username}...")
    client = Atelier801()
    if not client.login(username, password):
        result['error'] = 'Login failed'
        print("     FAILED!")
        return result
    
    print("     Logged in!")
    
    # Check if certified first
    status = client.get_account_status()
    if status['certified']:
        result['error'] = 'Account is certified - use game UI to change email'
        print("     SKIPPED: Account is certified")
        return result
    
    # Step 3: Change email
    print(f"[3/4] Changing email to {mailtm_email}...")
    resp = client.change_email(mailtm_email)
    if not resp['success']:
        result['error'] = f"Email change failed: {resp['message']}"
        print(f"     FAILED: {resp['message']}")
        return result
    
    print("     Change requested!")
    
    # Step 4: Get validation link
    print("[4/4] Validating email...")
    mailtm.login(mailtm_email, mailtm_password)
    
    link = mailtm.get_validation_link(timeout=60)
    if not link:
        result['error'] = 'No validation email received'
        print("     FAILED: No validation email")
        return result
    
    # Validate
    client.validate_email(link)
    time.sleep(2)  # Wait for page update
    
    # Verify email actually changed
    if client.check_email_changed(mailtm_email):
        result['success'] = True
        result['email_changed'] = True
        print(f"     SUCCESS! Email changed to {mailtm_email[0]}***")
        
        # Save association
        mailtm.save_with_association(mailtm_email, mailtm_password, username)
        print(f"     Saved to em.txt")
    else:
        result['error'] = 'Email change not confirmed'
        print("     FAILED: Change not confirmed")
    
    return result


# ============== QUICK EXAMPLE ==============
if __name__ == "__main__":
    print("=" * 50)
    print("ATELIER 801 EMAIL CHANGE")
    print("=" * 50)
    
    # Change these values for different accounts
    ATELIER_USERNAME = "Hora#1469"
    ATELIER_PASSWORD = "86yiuvvd4"
    
    result = change_email_for_account(
        ATELIER_USERNAME,
        ATELIER_PASSWORD
    )
    
    print("\n" + "=" * 50)
    print("RESULT")
    print("=" * 50)
    print(f"Success: {result['success']}")
    print(f"MailTM: {result['mailtm_email']}")
    print(f"Email Changed: {result['email_changed']}")
    if result['error']:
        print(f"Error: {result['error']}")
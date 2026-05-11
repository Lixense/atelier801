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
        username: Atelier 801 username (e.g., "Player#1234")
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
    
    # Check if email form is visible (certified accounts can change email if form is shown)
    html = client.get_account_page()
    if 'form_changer_mail' in html:
        idx = html.find('form_changer_mail')
        form_section = html[idx:idx+100] if idx >= 0 else ""
        if 'hidden' in form_section:
            result['error'] = 'Account is certified - use game UI to change email'
            print("     SKIPPED: Account is certified")
            return result
    else:
        # No form at all - can't change email
        result['error'] = 'No email form found'
        print("     SKIPPED: No email form")
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
# Usage: python main.py
# Change the values below to use with your accounts

if __name__ == "__main__":
    print("=" * 50)
    print("ATELIER 801 EMAIL CHANGE")
    print("=" * 50)
    print("\nUsage:")
    print("  from atelier801 import Atelier801")
    print("  from mailtm import MailTM")
    print("")
    print("  # Create new email")
    print("  mailtm = MailTM()")
    print("  email, password = mailtm.create_account()")
    print("")
    print("  # Login and change")
    print("  client = Atelier801()")
    print("  client.login('YourAccount#1234', 'yourpassword')")
    print("  client.change_email(email)")
    print("")
    print("  See README.md for full documentation!")
    print("=" * 50)
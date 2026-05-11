"""
Atelier801 - Python library for Atelier 801 automation
=======================================================

A comprehensive Python library for automating Atelier 801 account operations
including login, email change, certification, and account status checking.

Installation:
    pip install atelier801

Basic Usage:
    from atelier801 import Atelier801
    
    client = Atelier801()
    client.login("username#1234", "password")
    
    # Check account status
    status = client.get_account_status()
    print(status)

GitHub: https://github.com/Lixense/atelier801
"""

import requests
import re
import hashlib
import json
from typing import Optional, Dict, Any, Tuple, List
from .parser import extract_token_for_action, extract_any_token
from .crypto import crypte as encrypt_password


class Atelier801:
    """
    Main client for Atelier 801 operations.
    
    Attributes:
        base_url (str): Base URL for Atelier 801 API
        session (requests.Session): HTTP session for requests
        logged_in (bool): Login status
    
    Example:
        >>> client = Atelier801()
        >>> client.login("Player#1234", "mypassword")
        True
        >>> status = client.get_account_status()
        >>> print(status['email'])
    """
    
    BASE_URL = "https://atelier801.com"
    
    def __init__(self, session: Optional[requests.Session] = None):
        """
        Initialize Atelier 801 client.
        
        Args:
            session: Optional existing requests.Session to use
            
        Example:
            >>> client = Atelier801()
            >>> # or with custom session
            >>> sess = requests.Session()
            >>> client = Atelier801(session=sess)
        """
        self.session = session or requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        self.logged_in = False
        self.username = None
        self._account_cache = None
    
    def login(self, username: str, password: str) -> bool:
        """
        Login to Atelier 801 account.
        
        Args:
            username: Username with discriminator (e.g., "Player#1234")
            password: Account password
            
        Returns:
            bool: True if login successful, False otherwise
            
        Example:
            >>> client = Atelier801()
            >>> if client.login("Player#1234", "mypassword"):
            ...     print("Logged in!")
        """
        # Encrypt password
        encrypted = encrypt_password(password)
        
        # Get login page for initial token
        resp = self.session.get(f"{self.BASE_URL}/login")
        
        # Extract login token if needed
        token_match = re.search(r'name="token" value="([^"]+)"', resp.text)
        token = token_match.group(1) if token_match else ""
        
        # Login request
        data = {
            'login': username,
            'password': encrypted,
            'token': token,
            'connexion': '1'
        }
        
        resp = self.session.post(f"{self.BASE_URL}/login", data=data, allow_redirects=True)
        
        # Check if logged in by looking for account link
        if f"{username.split('#')[0]}#" in resp.text or 'deconnexion' in resp.text.lower():
            self.logged_in = True
            self.username = username
            self._account_cache = None  # Reset cache
            return True
        
        return False
    
    def logout(self) -> bool:
        """
        Logout from current session.
        
        Returns:
            bool: True if logged out successfully
            
        Example:
            >>> client.logout()
        """
        if not self.logged_in:
            return True
            
        resp = self.session.get(f"{self.BASE_URL}/deconnexion")
        self.logged_in = False
        self.username = None
        self._account_cache = None
        return resp.status_code == 200
    
    def get_account_page(self) -> str:
        """
        Get raw HTML of account page.
        
        Returns:
            str: HTML content of account page
            
        Example:
            >>> html = client.get_account_page()
        """
        resp = self.session.get(f"{self.BASE_URL}/account")
        return resp.text
    
    def get_account_status(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get comprehensive account status information.
        
        Args:
            force_refresh: Force refresh cached data (default: False)
            
        Returns:
            dict: Account status with keys:
                - username (str): Full username with discriminator
                - email (str): Current email (masked)
                - email_validated (bool): Whether email is validated
                - certified (bool): Whether account is certified
                - registration_date (str): Registration date if available
                - is_banned (bool): Whether account is banned
                - ban_info (dict): Ban details if banned (type, reason, duration, state)
                
        Example:
            >>> status = client.get_account_status()
            >>> print(status['email'])
            >>> print(status['certified'])
        """
        if self._account_cache and not force_refresh:
            return self._account_cache
        
        html = self.get_account_page()
        
        status = {
            'username': self.username,
            'email': None,
            'email_validated': False,
            'certified': False,
            'registration_date': None,
            'is_banned': False,
            'ban_info': None
        }
        
        # Extract email
        email_match = re.search(r'Email\s*:\s*</span><span[^>]*>([^<]+)</span>', html)
        if not email_match:
            email_match = re.search(r'Email\s*:\s*<span[^>]*>([^<]+)</span>', html)
        if email_match:
            status['email'] = email_match.group(1)
            status['email_validated'] = 'mail-non-certifie' not in html
        
        # Check if certified (email form visible = certified)
        if 'form_changer_mail' in html:
            idx = html.find('form_changer_mail')
            form_section = html[idx:idx+100]
            status['certified'] = 'hidden' not in form_section
        
        # Extract registration date
        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', html)
        if date_match:
            status['registration_date'] = date_match.group(1)
        
        # Check ban status
        if 'sanction' in html.lower() or 'banni' in html.lower():
            status['is_banned'] = True
            status['ban_info'] = self._parse_ban_info(html)
        
        self._account_cache = status
        return status
    
    def _parse_ban_info(self, html: str) -> Optional[Dict[str, Any]]:
        """Parse ban information from HTML"""
        ban_info = {}
        
        ban_type = re.search(r'<span class="texte-type-sanction">([^<]+)</span>', html)
        if ban_type:
            ban_info['type'] = ban_type.group(1)
        
        ban_reason = re.search(r'<td class="message-plus-moins"[^>]*>([^<]+)</td>', html)
        if ban_reason:
            ban_info['reason'] = ban_reason.group(1).strip()
        
        ban_duration = re.search(r'<span class="texte-duree-sanction"[^>]*>.*?(\d+)\s*heure', html)
        if ban_duration:
            ban_info['duration_hours'] = int(ban_duration.group(1))
        
        ban_state = re.search(r'<span class="texte-etat-sanction">([^<]+)</span>', html)
        if ban_state:
            ban_info['state'] = ban_state.group(1)
        
        return ban_info if ban_info else None
    
    def change_email(self, new_email: str) -> Dict[str, Any]:
        """
        Change account email address.
        
        Note: Account must be certified to change email directly.
        For uncertified accounts, this requests a validation email.
        
        Args:
            new_email: New email address
            
        Returns:
            dict: Result with keys:
                - success (bool): Whether change was successful
                - message (str): Response message
                - validation_sent (bool): Whether validation email was sent
                
        Example:
            >>> result = client.change_email("newemail@example.com")
            >>> if result['success']:
            ...     print("Email change requested!")
        """
        if not self.logged_in:
            return {'success': False, 'message': 'Not logged in', 'validation_sent': False}
        
        # Get token for set-email action
        html = self.get_account_page()
        token_name, token_value = extract_token_for_action(html, 'set-email')
        
        if not token_value:
            return {'success': False, 'message': 'Could not find token', 'validation_sent': False}
        
        headers = {
            'Referer': f'{self.BASE_URL}/account',
            'Origin': self.BASE_URL,
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        resp = self.session.post(
            f'{self.BASE_URL}/set-email',
            data={'mail': new_email, token_name: token_value},
            headers=headers
        )
        
        result = resp.json()
        success = 'SUCCES' in result.get('resultat', '')
        
        return {
            'success': success,
            'message': result.get('message', ''),
            'validation_sent': success
        }
    
    def validate_email(self, validation_link: str) -> bool:
        """
        Visit validation link to confirm email change.
        
        Args:
            validation_link: Full validation URL from email
            
        Returns:
            bool: True if validation successful
            
        Example:
            >>> # Get link from MailTM
            >>> link = mailtm.get_validation_link()
            >>> client.validate_email(link)
        """
        if not self.logged_in:
            return False
        
        resp = self.session.get(validation_link)
        self._account_cache = None  # Refresh cache
        return resp.status_code == 200
    
    def request_certification(self) -> Dict[str, Any]:
        """
        Request certification email to be sent to current email.
        
        Returns:
            dict: Result with keys:
                - success (bool): Whether request was successful
                - message (str): Response message
                - token_name (str): CSRF token name used
                - token_value (str): CSRF token value used
                
        Example:
            >>> result = client.request_certification()
            >>> if result['success']:
            ...     print("Certification email sent!")
        """
        if not self.logged_in:
            return {'success': False, 'message': 'Not logged in', 'token_name': None, 'token_value': None}
        
        html = self.get_account_page()
        token_name, token_value = extract_token_for_action(html, 'get-certification')
        
        if not token_value:
            return {'success': False, 'message': 'Could not find token', 'token_name': None, 'token_value': None}
        
        headers = {
            'Referer': f'{self.BASE_URL}/account',
            'Origin': self.BASE_URL,
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        resp = self.session.post(
            f'{self.BASE_URL}/get-certification',
            data={token_name: token_value},
            headers=headers
        )
        
        result = resp.json()
        success = 'SUCCES' in result.get('resultat', '')
        
        return {
            'success': success,
            'message': result.get('message', ''),
            'token_name': token_name,
            'token_value': token_value
        }
    
    def submit_certification_code(self, code: str) -> Dict[str, Any]:
        """
        Submit certification code received via email.
        
        Args:
            code: Certification code from email
            
        Returns:
            dict: Result with keys:
                - success (bool): Whether certification was successful
                - message (str): Response message
                
        Example:
            >>> # Get code from MailTM
            >>> code = mailtm.get_certification_code()
            >>> result = client.submit_certification_code(code)
            >>> if result['success']:
            ...     print("Certified!")
        """
        if not self.logged_in:
            return {'success': False, 'message': 'Not logged in'}
        
        html = self.get_account_page()
        token_name, token_value = extract_token_for_action(html, 'set-certification')
        
        if not token_value:
            return {'success': False, 'message': 'Could not find token'}
        
        headers = {
            'Referer': f'{self.BASE_URL}/account',
            'Origin': self.BASE_URL,
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        resp = self.session.post(
            f'{self.BASE_URL}/set-certification',
            data={'code': code, token_name: token_value},
            headers=headers
        )
        
        result = resp.json()
        success = 'SUCCES' in result.get('resultat', '')
        
        self._account_cache = None  # Refresh cache
        
        return {
            'success': success,
            'message': result.get('message', '')
        }
    
    def get_session(self) -> requests.Session:
        """
        Get the underlying requests session.
        
        Returns:
            requests.Session: The session object
            
        Example:
            >>> session = client.get_session()
            >>> # Use session directly for custom requests
        """
        return self.session
    
    def is_logged_in(self) -> bool:
        """
        Check if currently logged in.
        
        Returns:
            bool: Login status
            
        Example:
            >>> if client.is_logged_in():
            ...     print("Logged in!")
        """
        return self.logged_in
    
    def __repr__(self) -> str:
        return f"<Atelier801 logged_in={self.logged_in} username={self.username}>"

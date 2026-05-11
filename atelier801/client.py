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
    status = client.get_account_status()
    print(status)

GitHub: https://github.com/yourusername/atelier801
"""

import requests
import re
import hashlib
import json
from urllib.parse import quote
from typing import Optional, Dict, Any, Tuple, List
from .parser import extract_token_for_action, extract_any_token
from .crypto import crypte as encrypt_password


class Atelier801:
    """
    Main client for Atelier 801 operations.
    
    Attributes:
        BASE_URL: Base URL for Atelier 801 API
        logged_in: Whether client is currently logged in
        username: Current logged in username
    """

    BASE_URL = "https://atelier801.com"

    def __init__(self):
        """Initialize Atelier 801 client."""
        self.session = requests.Session()
        self.logged_in = False
        self.username = None
        self._account_cache = None
    
    def login(self, username: str, password: str) -> bool:
        """
        Login to Atelier 801.
        
        Args:
            username: Username with discriminator (e.g., "name#1234")
            password: Account password
            
        Returns:
            bool: True if login successful
            
        Example:
            >>> client = Atelier801()
            >>> client.login("Test#1234", "password123")
            True
        """
        if '#' not in username:
            print("Warning: Username should include discriminator (e.g., name#1234)")
        
        # Get login page to extract tokens
        resp = self.session.get(f"{self.BASE_URL}/login")
        if resp.status_code != 200:
            return False
        
        # Extract login token
        login_token = extract_token_for_action(resp.text, "login")
        if not login_token:
            login_token = extract_any_token(resp.text)
        
        if not login_token:
            return False
        
        # Prepare login data
        data = {
            "login": username,
            "password": encrypt_password(password),
            "nxlazdcqga": login_token
        }
        
        # Submit login
        resp = self.session.post(f"{self.BASE_URL}/login", data=data, allow_redirects=True)
        
        if resp.status_code == 200 and "deconnexion" in resp.text.lower():
            self.logged_in = True
            self.username = username
            self._account_cache = None
            return True
            
        return False
    
    def logout(self) -> bool:
        """
        Logout from Atelier 801.
        
        Returns:
            bool: True if logout successful
            
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
        Get raw HTML of profile page (includes ban info).
        
        Returns:
            str: HTML content of profile page
            
        Example:
            >>> html = client.get_account_page()
        """
        resp = self.session.get(f"{self.BASE_URL}/profile?pr={quote(self.username)}")
        return resp.text
    
    def get_settings_page(self) -> str:
        """
        Get raw HTML of account settings page (includes email info).
        
        Returns:
            str: HTML content of account settings page
            
        Example:
            >>> html = client.get_settings_page()
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
        
        profile_html = self.get_account_page()
        account_html = self.get_settings_page()
        
        status = {
            'username': self.username,
            'email': None,
            'email_validated': False,
            'certified': False,
            'registration_date': None,
            'is_banned': False,
            'ban_info': None
        }
        
        # Extract email from account settings page
        mail_patterns = [
            r'Mail\s*:\s*</span><span[^>]*>([^<]+)</span>',
            r'Mail\s*:\s*<span[^>]*>([^<]+)</span>',
            r'Email\s*:\s*</span><span[^>]*>([^<]+)</span>',
            r'Email\s*:\s*<span[^>]*>([^<]+)</span>',
        ]
        for pattern in mail_patterns:
            mail_match = re.search(pattern, account_html)
            if mail_match:
                status['email'] = mail_match.group(1).strip()
                break
        
        if status['email']:
            status['email_validated'] = 'mail-non-certifie' not in account_html
        
        # Check if has validated email (from account settings)
        # "Vous devez d'abord certifier" = has validated email
        # "Nouveau mail" = no validated email
        if 'Vous devez d\'abord certifier' in account_html or 'form-get-certification' in account_html:
            status['certified'] = True  # Has validated email
        elif 'Nouveau mail' in account_html:
            status['certified'] = False  # No validated email
        
        # Extract registration date from profile page
        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', profile_html)
        if date_match:
            status['registration_date'] = date_match.group(1)
        
        # Check ban status from profile page
        if 'sanction' in profile_html.lower() or 'banni' in profile_html.lower():
            status['is_banned'] = True
            status['ban_info'] = self._parse_ban_info(profile_html)
        
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
    
    def check_email_changed(self, new_email: str) -> bool:
        """
        Check if email has been changed successfully.
        
        Atelier801 masks emails showing only the first letter (e.g. "4***@w***.net").
        So we check if the first letter of the new email appears in the Mail field.
        
        Args:
            new_email: The new email address that was set
            
        Returns:
            bool: True if email appears to have changed (first letter matches)
            
        Example:
            >>> # After email change + validation
            >>> if client.check_email_changed("4aavysr73bea@wshu.net"):
            ...     print("Email changed successfully!")
        """
        html = self.get_settings_page()
        first_letter = new_email[0].lower() if new_email else ''
        
        # Check mail2 input value (shows masked email like "4***@w***.net")
        mail2_match = re.search(r'<input[^>]*id="mail2"[^>]*value="([^"]*)"', html)
        if mail2_match:
            current = mail2_match.group(1).lower()
            return current.startswith(first_letter)
        
        # Fallback: check if first letter appears near Mail field
        mail_section = re.search(r'Mail\s*:\s*<[^>]*>([^<]+)', html)
        if mail_section:
            displayed = mail_section.group(1).strip().lower()
            return displayed.startswith(first_letter)
        
        return False
    
    def change_email(self, new_email: str) -> bool:
        """
        Change account email address.
        
        Note: Only works for accounts WITHOUT validated email.
        
        Args:
            new_email: New email address to set
            
        Returns:
            bool: True if email change was initiated
            
        Example:
            >>> client.change_email("newemail@example.com")
            True
        """
        if not self.logged_in:
            return False
        
        # Get account page to extract token
        resp = self.session.get(f"{self.BASE_URL}/account")
        if resp.status_code != 200:
            return False
        
        # Extract change email token
        token = extract_token_for_action(resp.text, "change-email")
        if not token:
            token = extract_any_token(resp.text)
        
        if not token:
            return False
        
        # Submit email change
        data = {
            "mail2": new_email,
            "nxlazdcqga": token
        }
        
        resp = self.session.post(f"{self.BASE_URL}/change-email", data=data)
        return resp.status_code == 200
    
    def validate_email(self, validation_url: str) -> bool:
        """
        Validate email from validation link.
        
        Args:
            validation_url: Full URL from validation email
            
        Returns:
            bool: True if validation successful
            
        Example:
            >>> client.validate_email("https://atelier801.com/validate-email?token=xxx")
            True
        """
        if not self.logged_in:
            return False
        
        # Extract token from URL if full URL provided
        if "token=" in validation_url:
            token = validation_url.split("token=")[1].split("&")[0]
            resp = self.session.get(f"{self.BASE_URL}/validate-email?token={token}")
        else:
            resp = self.session.get(validation_url)
        
        return resp.status_code == 200

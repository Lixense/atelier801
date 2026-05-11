"""
MailTM - Python library for Mail.tm temporary email service
============================================================

A Python library for creating and managing temporary email accounts
using the Mail.tm API. Useful for email verification and receiving
confirmation emails.

Installation:
    pip install mailtm (or use the included mailtm package)

Basic Usage:
    from mailtm import MailTM
    
    # Create new email
    mailtm = MailTM()
    email, password = mailtm.create_account()
    print(f"Email: {email}, Password: {password}")
    
    # Wait for email
    msg = mailtm.wait_for_email(subject_contains="verification")

API Documentation: https://docs.mail.tm/
"""

import requests
import random
import string
import time
import os
import re
from typing import Optional, List, Dict, Any, Tuple


# Default credentials file
DEFAULT_CREDENTIALS_FILE = "mailtm_accounts.txt"
API_BASE = "https://api.mail.tm"


class MailTM:
    """
    Client for Mail.tm temporary email service.
    
    Attributes:
        credentials_file (str): Path to credentials storage file
        email (str): Current logged-in email address
        password (str): Current account password
        
    Example:
        >>> mailtm = MailTM()
        >>> email, password = mailtm.create_account()
        >>> print(f"Created: {email}")
        
        >>> # Login with existing account
        >>> mailtm.login("test@example.com", "password")
        
        >>> # Get messages
        >>> inbox = mailtm.get_inbox()
    """
    
    def __init__(self, credentials_file: str = DEFAULT_CREDENTIALS_FILE):
        """
        Initialize MailTM client.
        
        Args:
            credentials_file: Path to save/load credentials (default: mailtm_accounts.txt)
            
        Example:
            >>> mailtm = MailTM()
            >>> mailtm = MailTM(credentials_file="my_accounts.txt")
        """
        self.credentials_file = credentials_file
        self.session = requests.Session()
        self.token: Optional[str] = None
        self.email: Optional[str] = None
        self.password: Optional[str] = None
    
    # ============== ACCOUNT MANAGEMENT ==============
    
    def get_domains(self) -> List[Dict[str, Any]]:
        """
        Get available email domains.
        
        Returns:
            list: List of available domains with their info
            
        Example:
            >>> domains = mailtm.get_domains()
            >>> print(domains[0]['domain'])
            'wshu.net'
        """
        resp = self.session.get(f"{API_BASE}/domains")
        data = resp.json()
        return data.get("hydra:member", [])
    
    def create_account(self, password: Optional[str] = None, 
                       domain: Optional[str] = None) -> Tuple[str, str]:
        """
        Create a new MailTM account.
        
        Args:
            password: Optional custom password (generates random if not provided)
            domain: Optional specific domain to use (uses first available if not provided)
            
        Returns:
            tuple: (email, password)
            
        Raises:
            Exception: If no domains available or creation fails
            
        Example:
            >>> mailtm = MailTM()
            >>> email, password = mailtm.create_account()
            >>> print(f"Created: {email}")
            
            >>> # With custom password
            >>> email, password = mailtm.create_account(password="mypassword123")
            
            >>> # With specific domain
            >>> email, password = mailtm.create_account(domain="wshu.net")
        """
        domains = self.get_domains()
        if not domains:
            raise Exception("No domains available")
        
        # Use specified domain or first available
        if domain:
            domain_obj = next((d for d in domains if d["domain"] == domain), domains[0])
        else:
            domain_obj = domains[0]
        
        domain_name = domain_obj["domain"]
        
        # Generate random username
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        email = f"{username}@{domain_name}"
        
        # Generate password if not provided
        if not password:
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        
        # Create account
        resp = self.session.post(
            f"{API_BASE}/accounts",
            json={"address": email, "password": password}
        )
        
        if resp.status_code not in (200, 201):
            raise Exception(f"Failed to create account: {resp.text}")
        
        self.email = email
        self.password = password
        
        # Save credentials
        self._save_credentials(email, password)
        
        return email, password
    
    def login(self, email: Optional[str] = None, 
              password: Optional[str] = None) -> str:
        """
        Login to MailTM and get authentication token.
        
        Args:
            email: Email address (uses stored if not provided)
            password: Password (uses stored if not provided)
            
        Returns:
            str: Authentication token
            
        Raises:
            Exception: If login fails
            
        Example:
            >>> mailtm = MailTM()
            >>> mailtm.login("test@example.com", "password123")
        """
        if not email:
            email = self.email
        if not password:
            password = self.password
        
        if not email or not password:
            raise Exception("Email and password required")
        
        resp = self.session.post(
            f"{API_BASE}/token",
            json={"address": email, "password": password}
        )
        
        if resp.status_code != 200:
            raise Exception(f"Login failed: {resp.text}")
        
        data = resp.json()
        self.token = data.get("token")
        self.email = email
        self.password = password
        
        self.session.headers["Authorization"] = f"Bearer {self.token}"
        
        return self.token
    
    def _save_credentials(self, email: str, password: str) -> None:
        """
        Save credentials to file.
        
        Args:
            email: Email address
            password: Password
        """
        with open(self.credentials_file, "a") as f:
            f.write(f"{email}:{password}\n")
    
    # ============== EMAIL OPERATIONS ==============
    
    def _ensure_logged_in(self) -> None:
        """Ensure logged in, login if needed"""
        if not self.token:
            self.login()
    
    def get_inbox(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get inbox messages.
        
        Args:
            limit: Maximum number of messages to return (default: 10)
            
        Returns:
            list: List of message summaries
            
        Example:
            >>> inbox = mailtm.get_inbox()
            >>> for msg in inbox:
            ...     print(f"{msg['subject']} from {msg['from']['address']}")
        """
        self._ensure_logged_in()
        
        resp = self.session.get(f"{API_BASE}/messages", params={"limit": limit})
        
        if resp.status_code != 200:
            raise Exception(f"Failed to get inbox: {resp.text}")
        
        return resp.json().get("hydra:member", [])
    
    def get_message(self, message_id: str) -> Dict[str, Any]:
        """
        Get a specific message by ID.
        
        Args:
            message_id: ID of the message to retrieve
            
        Returns:
            dict: Full message data including 'text' and 'html' body
            
        Example:
            >>> msg = mailtm.get_message("abc123")
            >>> print(msg['subject'])
            >>> print(msg['text'])  # Plain text content
        """
        self._ensure_logged_in()
        
        resp = self.session.get(f"{API_BASE}/messages/{message_id}")
        
        if resp.status_code != 200:
            raise Exception(f"Failed to get message: {resp.text}")
        
        return resp.json()
    
    def delete_message(self, message_id: str) -> bool:
        """
        Delete a message.
        
        Args:
            message_id: ID of message to delete
            
        Returns:
            bool: True if deleted successfully
            
        Example:
            >>> mailtm.delete_message("abc123")
        """
        self._ensure_logged_in()
        
        resp = self.session.delete(f"{API_BASE}/messages/{message_id}")
        return resp.status_code in (200, 204)
    
    def wait_for_email(self, sender_contains: Optional[str] = None,
                       subject_contains: Optional[str] = None,
                       timeout: int = 60, 
                       interval: int = 2) -> Optional[Dict[str, Any]]:
        """
        Wait for an email matching criteria.
        
        Args:
            sender_contains: Substring to match in sender email/name
            subject_contains: Substring to match in subject line
            timeout: Maximum seconds to wait (default: 60)
            interval: Seconds between checks (default: 2)
            
        Returns:
            dict: Full message data if found, None if timeout
            
        Example:
            >>> # Wait for email from atelier801
            >>> msg = mailtm.wait_for_email(sender_contains="atelier801", timeout=120)
            >>> if msg:
            ...     print(f"Got: {msg['subject']}")
        """
        self._ensure_logged_in()
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            messages = self.get_inbox(20)
            
            for msg in messages:
                # Check sender filter
                if sender_contains:
                    from_addr = msg.get("from", {}).get("address", "").lower()
                    from_name = msg.get("from", {}).get("name", "").lower()
                    if sender_contains.lower() not in from_addr and sender_contains.lower() not in from_name:
                        continue
                
                # Check subject filter
                if subject_contains:
                    subject = msg.get("subject", "").lower()
                    if subject_contains.lower() not in subject:
                        continue
                
                # Get full message
                full_msg = self.get_message(msg["id"])
                return full_msg
            
            time.sleep(interval)
        
        return None
    
    # ============== EXTRACTION HELPERS ==============
    
    def get_validation_link(self, timeout: int = 60) -> Optional[str]:
        """
        Wait for and extract validation link from email.
        
        Args:
            timeout: Maximum seconds to wait (default: 60)
            
        Returns:
            str: Validation URL if found, None if timeout
            
        Example:
            >>> link = mailtm.get_validation_link()
            >>> if link:
            ...     print(f"Click: {link}")
        """
        msg = self.wait_for_email(
            sender_contains="atelier801",
            subject_contains="validation",
            timeout=timeout
        )
        
        if not msg:
            return None
        
        text = msg.get("text", "") or ""
        html = msg.get("html", "") or ""
        content = text + html
        
        # Extract validation URL
        match = re.search(r'https?://atelier801\.com/validate-email[^\s<>]+', content)
        return match.group(0) if match else None
    
    def get_certification_code(self, timeout: int = 60) -> Optional[str]:
        """
        Wait for and extract certification code from email.
        
        Args:
            timeout: Maximum seconds to wait (default: 60)
            
        Returns:
            str: Certification code if found, None if timeout
            
        Example:
            >>> code = mailtm.get_certification_code()
            >>> if code:
            ...     print(f"Code: {code}")
        """
        msg = self.wait_for_email(
            sender_contains="atelier801",
            subject_contains="validation",
            timeout=timeout
        )
        
        if not msg:
            return None
        
        text = msg.get("text", "") or ""
        html = msg.get("html", "") or ""
        content = text + html
        
        # Extract code surrounded by blank lines (the actual code format)
        match = re.search(r'\n\n([A-Z0-9]{3,10})\n\n', content)
        if match:
            return match.group(1)
        
        # Fallback: code after "input field in game"
        match = re.search(r'input field.*?\n+([A-Z0-9]{3,10})', content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def get_latest_message(self, subject_contains: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get the most recent message, optionally filtered by subject.
        
        Args:
            subject_contains: Optional subject filter
            
        Returns:
            dict: Most recent message or None
            
        Example:
            >>> msg = mailtm.get_latest_message(subject_contains="validation")
        """
        inbox = self.get_inbox(limit=5)
        
        if not inbox:
            return None
        
        if subject_contains:
            for msg in inbox:
                if subject_contains.lower() in msg.get('subject', '').lower():
                    return self.get_message(msg['id'])
            return None
        
        return self.get_message(inbox[0]['id'])
    
    # ============== CREDENTIALS MANAGEMENT ==============
    
    @staticmethod
    def load_credentials(credentials_file: str = DEFAULT_CREDENTIALS_FILE) -> Optional[Tuple[str, str]]:
        """
        Load saved credentials from file.
        
        Args:
            credentials_file: Path to credentials file
            
        Returns:
            tuple: (email, password) or None if not found
            
        Example:
            >>> creds = MailTM.load_credentials()
            >>> if creds:
            ...     email, password = creds
        """
        if not os.path.exists(credentials_file):
            return None
        
        with open(credentials_file, "r") as f:
            lines = f.readlines()
        
        if not lines:
            return None
        
        last_line = lines[-1].strip()
        if ":" in last_line:
            email, password = last_line.split(":", 1)
            return email, password
        
        return None
    
    @staticmethod
    def load_all_accounts(credentials_file: str = DEFAULT_CREDENTIALS_FILE) -> List[Tuple[str, str]]:
        """
        Load all saved accounts.
        
        Args:
            credentials_file: Path to credentials file
            
        Returns:
            list: List of (email, password) tuples
            
        Example:
            >>> accounts = MailTM.load_all_accounts()
            >>> for email, pwd in accounts:
            ...     print(email)
        """
        accounts = []
        
        if not os.path.exists(credentials_file):
            return accounts
        
        with open(credentials_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and ":" in line:
                    email, pwd = line.split(":", 1)
                    accounts.append((email, pwd))
        
        return accounts
    
    def load_last_account(self) -> bool:
        """
        Load and login with the last saved account.
        
        Returns:
            bool: True if successful, False if no accounts
            
        Example:
            >>> mailtm = MailTM()
            >>> if mailtm.load_last_account():
            ...     print("Logged in!")
        """
        creds = self.load_credentials()
        if creds:
            self.login(creds[0], creds[1])
            return True
        return False
    
    def __repr__(self) -> str:
        return f"<MailTM email={self.email} logged_in={self.token is not None}>"

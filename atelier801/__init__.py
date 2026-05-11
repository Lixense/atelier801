"""
Atelier801 - Python library for Atelier 801 automation
=======================================================

A comprehensive Python library for automating Atelier 801 account operations.

Main Classes:
    - Atelier801: Main client for account operations

Submodules:
    - account: Account-specific operations
    - parser: HTML parsing utilities
    - crypto: Password encryption

Example:
    >>> from atelier801 import Atelier801
    >>> client = Atelier801()
    >>> client.login("Player#1234", "password")
    >>> status = client.get_account_status()
    >>> print(status)
"""

from .client import Atelier801
from .crypto import crypte

__version__ = "1.0.0"
__author__ = "Lixense"
__all__ = ['Atelier801', 'crypte']

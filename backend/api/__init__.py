"""
API Layer Public API
HTTP interface for the Branch Dependency Analysis system
Single Responsibility: Provide clean HTTP API for analysis operations
"""

# Import what we have so far
from .utils.response_builder import APIResponse
from .validators.input_validators import InputValidator

# Version information
__version__ = "1.0.0"
__author__ = "Branch Analysis API Team"

# Public API (only what exists)
__all__ = [
    'APIResponse',
    'InputValidator'
]
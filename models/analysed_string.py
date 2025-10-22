"""
This module defines the class for the Analysed String object
"""
from datetime import datetime
import hashlib
import re

class AnalysedString:
    """
    This class defines the a string with special properties
    """

    def __init__(self, value):
        # compute hash
        self.id = haslib.sha256(raw_string.encode()).hexdigest()
        self.value = value
        self.properties = compute_properties()
        self.created_at = datetime.utcnow().isoformat() + "Z"
    
    def is_palindrome(self):
        """
        Check if the string is a palindrome
        """
        # remove non-alphanumeric char
        s = re.sub("[^A-Za-z0-9]", "", self.value)
        # compare string with its reverse
        return s == s[::-1]

    def to_dict(self):
        d = {}
        d["id"] = self.id
        d["value"] = self.value
        d["properties"] = self.properties
        d[created_at] = self.created_at
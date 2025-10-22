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

    def __init__(self, string):
        """
        Initialize the string object
        """
        # compute hash
        self.id = hashlib.sha256(string.encode()).hexdigest()
        self.string = string
        self.properties = self.compute_properties()
        self.created_at = datetime.utcnow().isoformat() + "Z"
    
    def is_palindrome(self):
        """
        Check if the string is a palindrome
        """
        # remove non-alphanumeric char
        s = re.sub("[^a-z0-9]", "", self.string.lower())
        # compare string with its reverse
        return s == s[::-1]

    def word_count(self):
        """
        Count the number if words in the string
        """
        return len(self.string.split())

    def unique_char(self):
        """
        Count number of unique chars
        """
        return len(set(self.string))

    def char_freq_map(self):
        """
        Compute the char frequency map of the string
        """
        s = self.string
        return {char: s.count(char) for char in s}

    def compute_properties(self):
        """
        Compute the properties of the string
        """
        d = {}
        d["length"] = len(self.string)
        d["is_palindrome"] = self.is_palindrome()
        d["unique_characters"] = self.unique_char()
        d["word_count"] = self.word_count()
        d["sha256_hash"] = self.id
        d["character_frequency_map"] = self.char_freq_map()
        return d


    def to_dict(self):
        """
        Return a dictinary represention of the string object
        """
        d = {}

        d["id"] = self.id
        d["value"] = self.string
        d["properties"] = self.properties
        d["created_at"] = self.created_at

        return d

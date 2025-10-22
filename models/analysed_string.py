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

    def __init__(self, *args):
        """
        Initialize the string object
        """
        if len(args) == 1 and isinstance(args[0], str):
            # Object instantiation
            self.id = hashlib.sha256(args[0].encode()).hexdigest()
            self.string = args[0]
            self.properties = self.compute_properties()
            self.created_at = datetime.utcnow().isoformat() + "Z"
   
        else:
            # If len[args] is not 1, it means a tuple
            # a tuple was passed. That tuple should 
            # contain three fields:
            # id, value, and created_at.
            print(args)
            self.id = args[0]
            self.string = args[1]
            self.properties = self.compute_properties()
            self.created_at = args[2]

    def is_palindrome(self):
        """
        Check if the string is a palindrome
        """
        # remove non-alphanumeric chars
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

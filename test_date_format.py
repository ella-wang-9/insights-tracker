#!/usr/bin/env python3
"""Test date formatting function."""

from dateutil import parser as date_parser
import re

def _format_date_consistently(date_str: str) -> str:
    """Format date to consistent MMM DD, YYYY format."""
    if not date_str or date_str.strip() == "":
        return ""
    
    try:
        # Parse the date string
        parsed_date = date_parser.parse(date_str, fuzzy=True)
        
        # Format as MMM DD, YYYY
        formatted = parsed_date.strftime("%b %d, %Y")
        print(f"Formatted date '{date_str}' -> '{formatted}'")
        return formatted
        
    except Exception as e:
        print(f"Could not parse date '{date_str}': {e}")
        # If parsing fails, return the original if it looks like it's already in correct format
        if re.match(r'^[A-Z][a-z]{2} \d{1,2}, \d{4}$', date_str.strip()):
            return date_str.strip()
        return date_str

# Test various date formats
test_dates = [
    "Mar 11, 2025",
    "March 11, 2025", 
    "3/11/2025",
    "2025-03-11",
    "11 March 2025",
    "Nov 12, 2024",
    "November 12, 2024",
    "12/11/2024",
    "2024-11-12",
    "12 Nov 2024"
]

print("Testing date formatting:")
for date in test_dates:
    result = _format_date_consistently(date)
    print(f"  {date} -> {result}")
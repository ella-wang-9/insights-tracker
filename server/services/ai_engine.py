"""AI engine for customer insights extraction."""

import asyncio
import json
import os
import re
from datetime import datetime
from typing import List, Optional, Tuple
from dateutil import parser as date_parser

import spacy
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

from server.models.document_models import CategoryResult, ExtractedEntity, QuickAnalysisResult
from server.models.schema_models import CategoryValueType, SchemaTemplate


class AIInsightsEngine:
  """AI engine for extracting customer insights from text."""

  def __init__(self):
    """Initialize the AI engine."""
    # Simple cache to avoid repeated calls
    self._cache = {}
    self._cache_max_size = 50
    
    # Initialize Databricks client
    try:
      self.databricks_client = WorkspaceClient()
      # Use available foundation model endpoints
      # Note: These endpoints have rate limits and may have availability issues
      self.available_endpoints = [
        'databricks-gemini-2-5-flash',  # Fast Gemini model that works
        'databricks-gemini-2-5-pro',  # Pro Gemini model
        'databricks-claude-3-7-sonnet',  # Claude Sonnet as backup
        'databricks-meta-llama-3-1-8b-instruct',  # 8B Llama (rate limited)
        'databricks-meta-llama-3-3-70b-instruct',  # 70B Llama
      ]
      self.model_endpoint = self.available_endpoints[0]
      self.llm_available = True  # Always try to use LLM
      self.consecutive_failures = 0  # Track consecutive failures
      self.max_consecutive_failures = 5  # Allow more failures before disabling
      print(f'Initialized Databricks AI engine with endpoints: {self.available_endpoints}')
    except Exception as e:
      print(f'Warning: Could not initialize Databricks client: {e}')
      self.databricks_client = None
      self.model_endpoint = None
      self.available_endpoints = []
      self.llm_available = False
      self.consecutive_failures = 0
      self.max_consecutive_failures = 5

    # Initialize spaCy for NER (we'll use a simple fallback if model not available)
    self.nlp = None
    try:
      self.nlp = spacy.load('en_core_web_sm')
    except OSError:
      print("Warning: spaCy model 'en_core_web_sm' not found. Using fallback entity extraction.")

  async def analyze_text(
    self,
    text: str,
    schema: SchemaTemplate,
    extract_customer_info: bool = True,
    fast_mode: bool = False,
  ) -> QuickAnalysisResult:
    """Analyze text content and extract insights according to schema."""
    start_time = datetime.now()

    # Extract customer information if requested
    customer_name = None
    meeting_date = None
    if extract_customer_info:
      print(f"Extracting customer info from text (first 200 chars): {text[:200]}...")
      # Use LLM for customer info extraction
      customer_name, meeting_date = await self._extract_customer_info(text)
      print(f"Extracted customer_name: {customer_name}, meeting_date: {meeting_date}")

    # Process each category in the schema
    categories = {}
    for category in schema.categories:
      print(f"\nProcessing category: {category.name} (type: {category.value_type})")
      print(f"Category description: {category.description}")
      if category.value_type == CategoryValueType.PREDEFINED and hasattr(category, 'possible_values'):
        print(f"Predefined values: {category.possible_values}")
      category_result = await self._process_category(text, category, fast_mode)
      print(f"Result for {category.name}: values={category_result.values}, confidence={category_result.confidence}")
      categories[category.name] = category_result

    # Calculate processing time
    processing_time = (datetime.now() - start_time).total_seconds() * 1000

    return QuickAnalysisResult(
      customer_name=customer_name,
      meeting_date=meeting_date,
      categories=categories,
      processing_time_ms=int(processing_time),
      word_count=len(text.split()),
    )

  async def _extract_customer_info(self, text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract customer name and meeting date from text using LLM."""
    prompt = f"""Extract the customer name and meeting date from this text.

Text: {text}

Return a JSON object with these fields:
- customer_name: The company or customer name (e.g., "7-Eleven", "a16z", "ActiveFence")
- meeting_date: The date in format "MMM DD, YYYY" (e.g., "Nov 12, 2024", "Mar 11, 2025")

IMPORTANT: Always format dates as "MMM DD, YYYY" where:
- MMM is the 3-letter month abbreviation (Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec)
- DD is the 2-digit day (01-31)
- YYYY is the 4-digit year

If a field is not found, use empty string "".

Example: {{"customer_name": "7-Eleven", "meeting_date": "Nov 12, 2024"}}"""
    
    print(f"Customer extraction prompt length: {len(prompt)} chars")
    response = await self._query_databricks_model(prompt, max_tokens=500)
    print(f"Customer extraction response: {response[:200] if response else 'None'}...")
    
    if not response:
      print("WARNING: No response from LLM for customer extraction")
      return None, None
    
    try:
      import json
      # Extract JSON from response (LLM might include extra text)
      # Handle markdown code blocks that Gemini often uses
      if '```json' in response:
        json_text = response.split('```json')[1].split('```')[0].strip()
        print(f"Extracted JSON from markdown: {json_text}")
      elif '```' in response:
        # Sometimes just ``` without json
        json_text = response.split('```')[1].split('```')[0].strip()
        print(f"Extracted from code block: {json_text}")
      else:
        # More robust JSON extraction that handles nested objects and arrays
        # Find the first { and try to match to the last }
        start_idx = response.find('{')
        if start_idx == -1:
          raise ValueError("No JSON found in response")
        
        # Try to extract complete JSON by balancing braces
        brace_count = 0
        end_idx = start_idx
        for i in range(start_idx, len(response)):
          if response[i] == '{':
            brace_count += 1
          elif response[i] == '}':
            brace_count -= 1
            if brace_count == 0:
              end_idx = i + 1
              break
        
        if brace_count != 0:
          # JSON might be truncated, try to extract what we can
          json_text = response[start_idx:].strip()
          # Try to fix common truncation issues
          if json_text.count('{') > json_text.count('}'):
            json_text += '}' * (json_text.count('{') - json_text.count('}'))
        else:
          json_text = response[start_idx:end_idx].strip()
      
      data = json.loads(json_text)
      
      # Get values and clean them
      customer = data.get('customer_name', '').strip()
      date = data.get('meeting_date', '').strip()
      
      # Clean up empty values
      if customer in ["", "null", "None", "N/A", "NA"]:
        customer = None
      if date in ["", "null", "None", "N/A", "NA"]:
        date = None
      
      # Format date consistently
      if date:
        date = self._format_date_consistently(date)
      
      print(f"Successfully extracted - Customer: '{customer}', Date: '{date}'")
      return customer, date
    except Exception as e:
      print(f"ERROR parsing customer extraction JSON: {e}")
      print(f"Response preview: {response[:500]}")
      
      # Try to extract from response text even if JSON parsing failed
      import re
      
      # Look for customer_name in various formats
      customer_match = re.search(r'customer_name["\']?\s*:\s*["\']([^"\']+)["\']', response, re.IGNORECASE)
      if not customer_match:
        customer_match = re.search(r'"customer_name"\s*:\s*"([^"]+)"', response)
      
      # Look for meeting_date in various formats  
      date_match = re.search(r'meeting_date["\']?\s*:\s*["\']([^"\']+)["\']', response, re.IGNORECASE)
      if not date_match:
        date_match = re.search(r'"meeting_date"\s*:\s*"([^"]+)"', response)
      
      customer = customer_match.group(1).strip() if customer_match else None
      date = date_match.group(1).strip() if date_match else None
      
      # Clean up empty values
      if customer in ["", "null", "None", "N/A", "NA"]:
        customer = None
      if date in ["", "null", "None", "N/A", "NA"]:
        date = None
        
      print(f"Extracted from regex parsing - Customer: '{customer}', Date: '{date}'")
      # Format date consistently if found
      if date:
        date = self._format_date_consistently(date)
      return customer, date

  def _format_date_consistently(self, date_str: str) -> str:
    """Format date to consistent MMM DD, YYYY format."""
    if not date_str or date_str.strip() == "":
      return ""
    
    try:
      from dateutil import parser as date_parser
      
      # Parse the date string
      parsed_date = date_parser.parse(date_str, fuzzy=True)
      
      # Format as MMM DD, YYYY
      formatted = parsed_date.strftime("%b %d, %Y")
      print(f"Formatted date '{date_str}' -> '{formatted}'")
      return formatted
      
    except Exception as e:
      print(f"Could not parse date '{date_str}': {e}")
      # If parsing fails, return the original if it looks like it's already in correct format
      import re
      if re.match(r'^[A-Z][a-z]{2} \d{1,2}, \d{4}$', date_str.strip()):
        return date_str.strip()
      return date_str

  async def _extract_customer_info_fallback(self, text: str) -> Tuple[Optional[str], Optional[str]]:
    """Fallback method for extracting customer info - kept for compatibility."""
    customer_name = None
    meeting_date = None
    
    # Look for company patterns
    company_patterns = [
        r'(?:meeting with|call with|discussion with)\s+([A-Z]\w+(?:\s+[A-Z]\w+)*)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:team|customer|client)',
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*[-–:]',
        r'(\w+\s+Fisher|\w+\s+Corp|\w+\s+Inc|\w+\s+LLC|\w+\s+Ltd)',  # Common company suffixes
        r'^(\w+(?:\s+\w+)*)\s*\|',  # Company name before pipe character
    ]

    for pattern in company_patterns:
      match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
      if match:
        candidate = match.group(1).strip()
        # Filter out common non-company words
        if not any(
          word in candidate.lower()
          for word in ['attendees', 'notes', 'tldr', 'eng', 'raw', 'context']
        ):
          customer_name = candidate
          break

    if not meeting_date:
      # Look for date patterns
      date_patterns = [
        r'(\d{1,2}\/\d{1,2}\/\d{4})',
        r'(\d{1,2}-\d{1,2}-\d{4})',
        r'((January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
        r'((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})',
        r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # ISO format
        r'^((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})',  # Start of line dates
      ]

      for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
          date_str = match.group(1)
          # Parse and format the date consistently
          formatted_date = self._format_date_consistently(date_str)
          if formatted_date:
            meeting_date = formatted_date
          else:
            meeting_date = date_str  # Fallback to original if parsing fails
          break

    return customer_name, meeting_date

  def _parse_and_format_date(self, date_str: str) -> Optional[str]:
    """Parse a date string and return it in ISO format (YYYY-MM-DD)."""
    if not date_str:
      return None
    
    # Remove common prefixes
    cleaned = date_str.strip()
    for prefix in ['Date:', 'Meeting date:', 'On', 'Meeting on']:
      if cleaned.lower().startswith(prefix.lower()):
        cleaned = cleaned[len(prefix):].strip()
    
    # Try manual patterns first for exact matches
    patterns = [
      (r'^(\d{1,2})/(\d{1,2})/(\d{4})$', lambda m: f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"),
      (r'^(\d{1,2})-(\d{1,2})-(\d{4})$', lambda m: f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"),
      (r'^(\d{4})/(\d{1,2})/(\d{1,2})$', lambda m: f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"),
      (r'^(\d{4})-(\d{1,2})-(\d{1,2})$', lambda m: f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"),
    ]
    
    for pattern, formatter in patterns:
      match = re.match(pattern, cleaned)
      if match:
        try:
          return formatter(match)
        except:
          continue
    
    # Try parsing with dateutil parser with stricter settings
    try:
      # Only parse if the string looks like a date
      if any(month in cleaned for month in ['January', 'February', 'March', 'April', 'May', 'June', 
                                              'July', 'August', 'September', 'October', 'November', 'December',
                                              'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
        parsed_date = date_parser.parse(cleaned, fuzzy=False)
        return parsed_date.strftime('%Y-%m-%d')
    except:
      pass
      
    return None

  async def _extract_customer_info_fallback(self, text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract customer name and meeting date using regex patterns (no AI calls)."""
    customer_name = None
    meeting_date = None

    # Look for company patterns using regex only
    company_patterns = [
      # Numbers-based names like "7-11" or "7-Eleven" (check first to avoid partial matches)
      r'(\d+[-\s]?Eleven)',
      r'(?<!\d)(\d{1,2}[-\s]\d{1,2})(?!\d)',  # Pattern for "7-11" (not dates)
      # Company names ending with Corp, Inc, etc (e.g., TechCorp, DataCorp)
      r'([A-Z][a-zA-Z]*(?:Corp|Inc|LLC|Ltd))(?:\.)?',
      # Company with suffix (Corp, Inc, etc) with space
      r'([A-Z][a-zA-Z]+\s+(?:Corp|Inc|LLC|Ltd))(?:\.)?',
      # "Meeting with X" where X is 1-3 words ending before "on"
      r'(?:meeting with|call with|discussion with)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})(?=\s+on\s)',
      # "Meeting with X" at end of sentence
      r'(?:meeting with|call with|discussion with)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})(?=[.,]|$)',
      # "X discussion" or "X meeting" where X is a company name
      r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})\s+(?:discussion|meeting|call)',
      # Company at start of line before colon/dash
      r'^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})\s*[-–:]',
      # After "Customer:" or "Client:" label
      r'(?:Customer|Client):\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})',
      # Before "team", "customer", "client"
      r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})\s+(?:team|customer|client)',
      # Standalone capitalized words that might be company names (fallback)
      r'^([A-Z][a-zA-Z]+)(?:\s|$)',
    ]

    for pattern in company_patterns:
      match = re.search(pattern, text, re.MULTILINE)
      if match:
        candidate = match.group(1).strip()
        # Filter out common non-company words and overly long matches
        if (not any(word in candidate.lower() for word in ['attendees', 'notes', 'tldr', 'eng', 'raw', 'context', 'very', 'but', 'with']) 
            and len(candidate.split()) <= 4  # Company names are usually 1-4 words
            and len(candidate) < 50):  # Reasonable length
          customer_name = candidate
          break

    # Look for date patterns using regex only
    date_patterns = [
      r'(\d{1,2}/\d{1,2}/\d{4})',
      r'(\d{1,2}-\d{1,2}-\d{4})',
      r'((January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
      r'((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})',
      r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # ISO format
      r'^((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})',  # Start of line dates
    ]

    for pattern in date_patterns:
      match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
      if match:
        date_str = match.group(1)
        # Parse and format the date consistently
        formatted_date = self._parse_and_format_date(date_str)
        if formatted_date:
          meeting_date = formatted_date
        else:
          meeting_date = date_str  # Fallback to original if parsing fails
        break

    return customer_name, meeting_date

  async def _process_category_fallback(self, text: str, category) -> CategoryResult:
    """Process category using fast fallback methods without AI."""
    print(f"Processing category '{category.name}' with fallback methods")

    if category.value_type == CategoryValueType.PREDEFINED:
      # Enhanced keyword matching for predefined categories
      found_values = []
      evidence = []

      for value in category.possible_values:
        value_lower = value.lower()
        text_lower = text.lower()

        # Direct match
        if value_lower in text_lower:
          found_values.append(value)
          # Find context around the keyword
          idx = text_lower.find(value_lower)
          start = max(0, idx - 50)
          end = min(len(text), idx + len(value) + 50)
          evidence.append(text[start:end].strip())

        # Semantic matching for satisfaction levels
        elif category.name.lower() in ['satisfaction', 'satisfaction level']:
          satisfaction_map = {
            'very satisfied': ['very happy', 'love', 'excellent', 'fantastic'],
            'satisfied': ['happy', 'pleased', 'good', 'works well'],
            'neutral': ['okay', 'average', 'fine'],
            'dissatisfied': ['frustrated', 'struggling', 'issues', 'problems', 'slow'],
            'very dissatisfied': ['very frustrated', 'angry', 'terrible', 'awful'],
          }
          if value_lower in satisfaction_map:
            for keyword in satisfaction_map[value_lower]:
              if keyword in text_lower:
                found_values.append(value)
                idx = text_lower.find(keyword)
                start = max(0, idx - 50)
                end = min(len(text), idx + len(keyword) + 50)
                evidence.append(text[start:end].strip())
                break

      return CategoryResult(
        category_name=category.name,
        values=found_values,
        confidence=0.7 if found_values else 0.0,
        evidence_text=evidence,
        model_used='keyword_fallback',
      )

    else:
      # Enhanced pattern matching for inferred categories
      found_values = []
      evidence = []
      category_lower = category.name.lower()

      # Pain points extraction
      if any(pattern in category_lower for pattern in ['pain', 'challenge', 'issue', 'problem']):
        pain_patterns = [
          r'(?:frustrated|struggling|issues?|problems?) (?:with|about|regarding) ([^.,]+)',
          r'(slow (?:performance|response|processing|loading|speed))',
          r'((?:lack|lacking|missing|need|needs) (?:of |for |better )?[^.,]+)',
          r'((?:difficult|hard|challenging) to [^.,]+)',
          r'((?:can\'t|cannot|unable to) [^.,]+)',
          r'(takes? (?:too long|hours|forever|ages))',
          r'((?:poor|bad|terrible) [^.,]+)',
        ]

        for pattern in pain_patterns:
          matches = re.findall(pattern, text, re.IGNORECASE)
          for match in matches:
            value = match.strip()
            # Clean up the match
            value = re.sub(r'^(with|about|regarding|of|for)\s+', '', value)
            if len(value) > 5 and len(value) < 100:  # Reasonable length
              found_values.append(value)
              # Find context
              idx = text.lower().find(match.lower())
              if idx >= 0:
                start = max(0, idx - 30)
                end = min(len(text), idx + len(match) + 30)
                evidence.append(text[start:end].strip())
              if len(found_values) >= 5:
                break

      # Feature requests extraction
      elif any(
        pattern in category_lower for pattern in ['feature', 'request', 'need', 'requirement']
      ):
        request_patterns = [
          r'(?:need|needs?|want|wants?) (?:to have |for |better |improved |new )?([^.,]+)',
          r'(?:would like|we\'d like) (?:to have |to see |better )?([^.,]+)',
          r'(?:looking for|interested in) ([^.,]+)',
          r'(?:it would be (?:great|nice|helpful) (?:to have|if)) ([^.,]+)',
          r'(?:feature request|request):\s*([^.,]+)',
          r'(?:wishlist|wish list):\s*([^.,]+)',
        ]

        for pattern in request_patterns:
          matches = re.findall(pattern, text, re.IGNORECASE)
          for match in matches:
            value = match.strip()
            # Clean up the match
            value = re.sub(r'^(to |for |if |have |see )\s*', '', value)
            # Skip if too short or contains only common words
            if len(value) > 8 and not all(
              word in ['the', 'a', 'an', 'to', 'it', 'that', 'this']
              for word in value.lower().split()
            ):
              found_values.append(value)
              # Find evidence
              sentences = text.split('.')
              for sentence in sentences:
                if match.lower() in sentence.lower():
                  evidence.append(sentence.strip())
                  break
              if len(found_values) >= 5:
                break

      # Industry extraction
      elif 'industry' in category_lower:
        industry_keywords = {
          'e-commerce': ['e-commerce', 'ecommerce', 'online retail', 'online store', 'marketplace'],
          'financial services': [
            'financial',
            'banking',
            'fintech',
            'insurance',
            'trading',
            'payments',
          ],
          'healthcare': ['healthcare', 'medical', 'hospital', 'health', 'pharma', 'clinical'],
          'technology': [
            'software',
            'saas',
            'tech company',
            'it company',
            'technology',
            'platform',
          ],
          'retail': ['retail', 'store', 'shops', 'merchandising', 'pos', 'point of sale'],
          'manufacturing': ['manufacturing', 'factory', 'production', 'assembly', 'industrial'],
          'media': ['media', 'entertainment', 'streaming', 'content', 'publishing', 'broadcasting'],
        }

        text_lower = text.lower()
        for industry, keywords in industry_keywords.items():
          for keyword in keywords:
            if keyword in text_lower:
              if industry not in found_values:
                found_values.append(industry)
                idx = text_lower.find(keyword)
                start = max(0, idx - 50)
                end = min(len(text), idx + len(keyword) + 50)
                evidence.append(text[start:end].strip())
                break

      # Use case extraction
      elif 'use case' in category_lower:
        use_case_patterns = [
          r'(?:use|using|used) (?:it |this |that )?(?:for|to) ([^.,]+)',
          r'(?:helps?|helping) (?:us |them )?(?:with|to) ([^.,]+)',
          r'(?:solution for|platform for) ([^.,]+)',
          r'(?:enables?|enabling) ([^.,]+)',
        ]

        for pattern in use_case_patterns:
          matches = re.findall(pattern, text, re.IGNORECASE)
          for match in matches:
            value = match.strip()
            if len(value) > 10 and len(value) < 80:
              found_values.append(value)
              # Find context
              sentences = text.split('.')
              for sentence in sentences:
                if match.lower() in sentence.lower():
                  evidence.append(sentence.strip())
                  break
              if len(found_values) >= 3:
                break

      # Customer/company extraction (for backward compatibility)
      elif any(pattern in category_lower for pattern in ['customer', 'company', 'client']):
        # Look for company names with common patterns
        company_patterns = [
          r'\b([A-Z][a-zA-Z]+(?:\s+(?:Corp|Inc|Ltd|LLC|Co|Company))?)\b',
          r'meeting with ([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
          r'client ([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
        ]

        companies_found = set()
        for pattern in company_patterns:
          matches = re.findall(pattern, text)
          companies_found.update(matches)

        # Filter out common non-company words
        skip_words = [
          'Meeting',
          'Call',
          'Discussion',
          'The',
          'This',
          'That',
          'They',
          'Their',
          'Team',
          'Customer',
        ]
        for company in companies_found:
          if company not in skip_words and len(company) > 2:
            found_values.append(company)
            evidence.append(f'Company mentioned: {company}')
            if len(found_values) >= 3:
              break

      # General fallback - look for relevant phrases
      else:
        # Try to extract based on category description
        if category.description:
          desc_lower = category.description.lower()
          if 'satisfaction' in desc_lower or 'sentiment' in desc_lower:
            sentiment_words = [
              'happy',
              'satisfied',
              'frustrated',
              'disappointed',
              'pleased',
              'concerned',
            ]
            for word in sentiment_words:
              if word in text.lower():
                found_values.append(word)
                idx = text.lower().find(word)
                start = max(0, idx - 30)
                end = min(len(text), idx + len(word) + 30)
                evidence.append(text[start:end].strip())

      return CategoryResult(
        category_name=category.name,
        values=found_values[:5],  # Limit to 5 values
        confidence=0.6 if found_values else 0.0,
        evidence_text=evidence[:5],
        model_used='pattern_fallback',
      )

  async def _process_category(self, text: str, category, fast_mode: bool = False) -> CategoryResult:
    """Process a single category using AI only."""
    # Always use LLM, no fallback
    result = None
    
    # Try extraction, with one retry if we get empty result
    for attempt in range(2):
      if attempt > 0:
        print(f"\nRetrying extraction for {category.name} (attempt {attempt + 1}/2)")
        
      if category.value_type == CategoryValueType.PREDEFINED:
        result = await self._process_predefined_category(text, category)
      else:
        result = await self._process_inferred_category(text, category)
      
      # If we got values, we're done
      if result and result.values and len(result.values) > 0:
        break
      
      # Otherwise, we'll retry once
      if attempt == 0:
        print(f"Got empty result for {category.name}, will retry once")
        await asyncio.sleep(1)  # Brief pause before retry
    
    return result

  async def _query_databricks_model(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
    """Query the Databricks Foundation Model endpoint."""
    # TEMPORARY: Use mock responses for testing while LLMs are rate limited
    if os.getenv('USE_MOCK_LLM', 'false').lower() == 'true':
      print("  Using mock LLM response for testing")
      if "customer" in prompt.lower():
        return '{"customer_name": "ACME Corp", "meeting_date": "2025-01-15"}'
      elif "predefined" in prompt.lower():
        return '{"values": ["Vector Search"], "evidence": ["needs Vector Search"], "confidence": 0.9}'
      else:
        return '{"values": ["product catalog search"], "evidence": ["for their product catalog"], "confidence": 0.8}'
    
    if not self.databricks_client or not self.available_endpoints:
      print('Databricks client or endpoints not available')
      return None
    
    # Check cache first - make cache key more specific
    # Include more context to prevent cache collisions
    import hashlib
    cache_key = hashlib.md5(f"{prompt}_{max_tokens}".encode()).hexdigest()
    if cache_key in self._cache:
      print("  Using cached response")
      return self._cache[cache_key]

    # Try each endpoint until one works
    for endpoint_idx, endpoint in enumerate(self.available_endpoints):
      print(f'\nTrying LLM endpoint {endpoint_idx + 1}/{len(self.available_endpoints)}: {endpoint}')
      
      # Retry logic for rate limits
      for retry in range(3):
        try:
          # Create ChatMessage for the user prompt
          messages = [ChatMessage(role=ChatMessageRole.USER, content=prompt)]

          # Query with a reasonable timeout
          print(f'  Attempt {retry + 1}/3: Sending request...')
          
          # Make the synchronous call in a thread to avoid blocking
          import asyncio
          response = await asyncio.wait_for(
            asyncio.to_thread(
              self.databricks_client.serving_endpoints.query,
              name=endpoint, 
              messages=messages, 
              max_tokens=max_tokens, 
              temperature=0.1
            ),
            timeout=120.0  # 120 second timeout to give LLM more time
          )

          print(f'  ✓ Success with {endpoint}!')

          # Extract the response content
          if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            print(f'  Response length: {len(content)} chars')
            print(f'  Response preview: {content[:200]}...')
            if len(content) < 500:
              print(f'  Full response: {content}')
            # Reset failure counter on success
            self.consecutive_failures = 0
            self.llm_available = True
            # Update primary endpoint for future calls
            if endpoint_idx > 0:
              self.available_endpoints[0], self.available_endpoints[endpoint_idx] = (
                self.available_endpoints[endpoint_idx], self.available_endpoints[0]
              )
            
            # Cache the response
            self._cache[cache_key] = content
            if len(self._cache) > self._cache_max_size:
              # Remove oldest entry
              self._cache.pop(next(iter(self._cache)))
            
            return content
          else:
            print('  No choices found in response')
            break  # Don't retry for empty responses

        except asyncio.TimeoutError:
          print(f'  Timeout after 120 seconds')
          self.consecutive_failures += 1
          break  # Don't retry timeouts, try next endpoint
        except Exception as e:
          error_str = str(e)[:200]
          print(f'  Error: {error_str}')
          
          # Check for rate limit error
          if 'REQUEST_LIMIT_EXCEEDED' in error_str or 'rate limit' in error_str.lower():
            if retry < 2:
              wait_time = (retry + 1) * 10  # 10s, 20s
              print(f'  Rate limited. Waiting {wait_time} seconds before retry...')
              await asyncio.sleep(wait_time)
              continue
            else:
              print('  Rate limited after 3 attempts. Trying next endpoint.')
              break
          
          # If it's an upstream error or endpoint not found, try next
          if 'upstream' in error_str.lower() or 'not found' in error_str.lower():
            break
          
          # For other errors, don't retry
          self.consecutive_failures += 1
          break
    
    print('\nAll LLM endpoints failed.')
    # Mark LLM as unavailable after multiple failures
    if self.consecutive_failures >= self.max_consecutive_failures:
      self.llm_available = False
      print('  Disabling LLM usage due to repeated failures')
    return None

  async def _process_predefined_category(self, text: str, category) -> CategoryResult:
    """Process a category with predefined values using document comprehension."""
    
    # Concise guidance for Vector Search schema categories
    if category.name == "Usage Pattern":
      guidance = "Select how they use the solution: Real Time (instant/live), Batch (scheduled/bulk), Interactive (on-demand queries), Scheduled (recurring/automated)."

    elif category.name == "Product":
      guidance = "Identify mentioned Databricks products: Vector Search, Embedding FT, Unstructured, MLflow, Delta Lake, Unity Catalog."

    elif category.name == "Search Tags":  
      guidance = "Select search capabilities: RAG (retrieval/contextual), Matching (similarity), Search (text/document), Similarity (semantic/vector)."

    elif category.name == "Unstructured Tags":
      guidance = "Select data processing: RAG (text retrieval), Automation (workflows), Document Processing (parsing), Text Analysis (NLP)."

    elif category.name == "End User Tags":
      guidance = "Select user type: Internal (employees), External (customers), Customer-Facing (public), Partner (third-party)."

    elif category.name == "Production Status":
      guidance = "Select deployment stage: Production (live), Development (building), POC (pilot/trial), Planning (future)."

    else:
      guidance = f"Read the document and select options that best match what they describe for {category.name}."
    
    prompt = f"""Options: {', '.join(category.possible_values)}

{guidance}

Text: "{text}"

JSON: {{"values": ["option"], "evidence": ["text"], "confidence": 0.9}}"""

    # Try Databricks Foundation Model first
    print(f"\n=== PREDEFINED CATEGORY EXTRACTION: {category.name} ===")
    print(f"Sending prompt to LLM (length: {len(prompt)} chars)")
    response_text = await self._query_databricks_model(prompt, max_tokens=1000)

    if response_text:
      try:
        print(f'Raw Foundation Model response: {response_text[:500]}...')
        
        # Check if response is empty or just whitespace
        if not response_text.strip():
          print("ERROR: LLM returned empty response")
          raise ValueError("Empty response from LLM")

        # Extract JSON from response (in case there's extra text)
        json_text = ''
        if '```json' in response_text:
          json_text = response_text.split('```json')[1].split('```')[0].strip()
          print(f'Extracted JSON: {json_text}')
        else:
          # More robust JSON extraction that handles nested objects and arrays
          start_idx = response_text.find('{')
          if start_idx == -1:
            print(f'No JSON pattern found in response: {response_text[:200]}')
            raise ValueError('No valid JSON found in response')
          
          # Try to extract complete JSON by balancing braces
          brace_count = 0
          end_idx = start_idx
          for i in range(start_idx, len(response_text)):
            if response_text[i] == '{':
              brace_count += 1
            elif response_text[i] == '}':
              brace_count -= 1
              if brace_count == 0:
                end_idx = i + 1
                break
          
          if brace_count != 0:
            # JSON might be truncated, try to extract what we can
            json_text = response_text[start_idx:].strip()
            # Fix unterminated strings
            lines = json_text.split('\n')
            for i in range(len(lines)):
              line = lines[i].strip()
              # Count quotes in the line
              quote_count = line.count('"')
              if quote_count % 2 == 1:  # Odd number of quotes means unterminated string
                if line.endswith(','):
                  lines[i] = line[:-1] + '"'  # Close the string before comma
                else:
                  lines[i] = line + '"'  # Just close the string
            json_text = '\n'.join(lines)
            
            # Remove trailing comma if present
            json_text = json_text.rstrip().rstrip(',')
            # Try to fix common truncation issues
            if json_text.count('[') > json_text.count(']'):
              json_text += ']' * (json_text.count('[') - json_text.count(']'))
            if json_text.count('{') > json_text.count('}'):
              json_text += '}' * (json_text.count('{') - json_text.count('}'))
            print(f'Extracted JSON (with truncation fix): {json_text}')
          else:
            json_text = response_text[start_idx:end_idx].strip()
            print(f'Extracted JSON: {json_text}')
        
        result_data = json.loads(json_text)

        print(f'Parsed JSON data successfully: {result_data}')

        # Validate extracted values
        extracted_values = result_data.get('values', [])
        if not extracted_values or (len(extracted_values) == 1 and not extracted_values[0]):
          print(f"WARNING: No valid values extracted for {category.name}")
          extracted_values = []
        
        print(f"Successfully extracted {len(extracted_values)} values for {category.name}: {extracted_values}")
        
        return CategoryResult(
          category_name=category.name,
          values=extracted_values,
          confidence=result_data.get('confidence', 0.5),
          evidence_text=result_data.get('evidence', []),
          model_used=self.model_endpoint,
        )
      except json.JSONDecodeError as e:
        print(f'JSON parsing error: {e}')
        print(f'Attempted to parse: {json_text if "json_text" in locals() else "N/A"}')
      except Exception as e:
        print(f'Error parsing Databricks model response: {e}')
        print(f'Response was: {response_text[:200]}...')

    # No fallback - return empty result if LLM fails
    print(f"\n!!! WARNING: Failed to extract {category.name} - returning empty result")
    print(f"Category type: {category.value_type}")
    if hasattr(category, 'possible_values'):
      print(f"Possible values: {category.possible_values}")
    return CategoryResult(
      category_name=category.name,
      values=[],
      confidence=0.0,
      evidence_text=[],
      model_used="none",
      error="LLM extraction failed - no response or parsing error"
    )

  async def _process_inferred_category(self, text: str, category) -> CategoryResult:
    """Process a category where values should be inferred by AI using document comprehension."""
    
    # Simple guidance focusing on document understanding  
    if category.name == "Industry":
      guidance = "Read the document and understand what type of business this customer operates. Focus on their core business purpose and industry sector."
    elif category.name == "Use Case":
      guidance = "Read the document and understand what specific business problem or application they want to solve. Focus on the business value they're trying to create."
    else:
      guidance = f"Read the document and understand what they describe related to {category.name}."
    
    prompt = f"""Extract values for "{category.name}" from the text.

{guidance}

Text: "{text}"

Return JSON: {{"values": ["value"], "evidence": ["supporting text"], "confidence": 0.9}}"""

    # Try Databricks Foundation Model first
    print(f"\n=== INFERRED CATEGORY EXTRACTION: {category.name} ===")
    print(f"Prompt for {category.name} (first 500 chars):\n{prompt[:500]}...")
    print(f"Full prompt length: {len(prompt)} chars")
    response_text = await self._query_databricks_model(prompt, max_tokens=1000)

    if response_text:
      try:
        print(f'Raw Foundation Model response (inferred): {response_text[:500]}...')
        
        # Check if response is empty or just whitespace
        if not response_text.strip():
          print("ERROR: LLM returned empty response")
          raise ValueError("Empty response from LLM")

        # Extract JSON from response (in case there's extra text)
        json_text = ''
        if '```json' in response_text:
          json_text = response_text.split('```json')[1].split('```')[0].strip()
          print(f'Extracted JSON (inferred): {json_text}')
        else:
          # More robust JSON extraction that handles nested objects and arrays
          start_idx = response_text.find('{')
          if start_idx == -1:
            print(f'No JSON pattern found in response (inferred): {response_text[:200]}')
            raise ValueError('No valid JSON found in response')
          
          # Try to extract complete JSON by balancing braces
          brace_count = 0
          end_idx = start_idx
          for i in range(start_idx, len(response_text)):
            if response_text[i] == '{':
              brace_count += 1
            elif response_text[i] == '}':
              brace_count -= 1
              if brace_count == 0:
                end_idx = i + 1
                break
          
          if brace_count != 0:
            # JSON might be truncated, try to extract what we can
            json_text = response_text[start_idx:].strip()
            # Fix unterminated strings
            lines = json_text.split('\n')
            for i in range(len(lines)):
              line = lines[i].strip()
              # Count quotes in the line
              quote_count = line.count('"')
              if quote_count % 2 == 1:  # Odd number of quotes means unterminated string
                if line.endswith(','):
                  lines[i] = line[:-1] + '"'  # Close the string before comma
                else:
                  lines[i] = line + '"'  # Just close the string
            json_text = '\n'.join(lines)
            
            # Remove trailing comma if present
            json_text = json_text.rstrip().rstrip(',')
            # Try to fix common truncation issues
            if json_text.count('[') > json_text.count(']'):
              json_text += ']' * (json_text.count('[') - json_text.count(']'))
            if json_text.count('{') > json_text.count('}'):
              json_text += '}' * (json_text.count('{') - json_text.count('}'))
            print(f'Extracted JSON (inferred, with truncation fix): {json_text}')
          else:
            json_text = response_text[start_idx:end_idx].strip()
            print(f'Extracted JSON (inferred): {json_text}')
        
        result_data = json.loads(json_text)

        print(f'Parsed JSON data successfully (inferred): {result_data}')

        # Validate extracted values
        extracted_values = result_data.get('values', [])
        if not extracted_values or (len(extracted_values) == 1 and not extracted_values[0]):
          print(f"WARNING: No valid values extracted for {category.name}")
          extracted_values = []
        
        print(f"Successfully extracted {len(extracted_values)} values for {category.name}: {extracted_values}")
        
        return CategoryResult(
          category_name=category.name,
          values=extracted_values,
          confidence=result_data.get('confidence', 0.5),
          evidence_text=result_data.get('evidence', []),
          model_used=self.model_endpoint,
        )
      except json.JSONDecodeError as e:
        print(f'JSON parsing error (inferred): {e}')
        print(f'Attempted to parse: {json_text if "json_text" in locals() else "N/A"}')
      except Exception as e:
        print(f'Error parsing Databricks model response for inferred category: {e}')
        print(f'Response was: {response_text[:200]}...')

    # No fallback - return empty result if LLM fails
    print(f"\n!!! WARNING: Failed to extract {category.name} - returning empty result")
    print(f"Category type: {category.value_type}")
    if hasattr(category, 'possible_values'):
      print(f"Possible values: {category.possible_values}")
    return CategoryResult(
      category_name=category.name,
      values=[],
      confidence=0.0,
      evidence_text=[],
      model_used="none",
      error="LLM extraction failed - no response or parsing error"
    )

  def extract_entities(self, text: str) -> List[ExtractedEntity]:
    """Extract named entities from text."""
    entities = []

    if self.nlp:
      doc = self.nlp(text)
      for ent in doc.ents:
        entities.append(
          ExtractedEntity(
            entity_text=ent.text,
            entity_type=ent.label_,
            confidence=0.8,  # spaCy doesn't provide confidence scores by default
            start_pos=ent.start_char,
            end_pos=ent.end_char,
          )
        )
    else:
      # Fallback: simple regex-based entity extraction
      # Extract potential company names (capitalized words)
      company_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
      for match in re.finditer(company_pattern, text):
        entities.append(
          ExtractedEntity(
            entity_text=match.group(),
            entity_type='ORG',
            confidence=0.6,
            start_pos=match.start(),
            end_pos=match.end(),
          )
        )

    return entities


# Global instance
ai_engine = AIInsightsEngine()

"""AI engine for customer insights extraction."""

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
    # Initialize Databricks client
    try:
      self.databricks_client = WorkspaceClient()
      # Use available foundation model endpoints
      # Note: These endpoints have rate limits and may have availability issues
      self.available_endpoints = [
        'llama_3_1_70b',  # This was listed as READY
        'meta_llama_3_70b_instruct-chat',  # Also listed as READY
        'databricks-meta-llama-3-1-8b-instruct',  # Fallback option
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
      # Use LLM for customer info extraction
      customer_name, meeting_date = await self._extract_customer_info(text)

    # Process each category in the schema
    categories = {}
    for category in schema.categories:
      category_result = await self._process_category(text, category, fast_mode)
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
    prompt = f"""Extract the customer/company name and meeting date from this text. 
    Return ONLY a JSON object with 'customer_name' and 'meeting_date' fields.
    
    Text: {text[:500]}
    
    Example response: {{"customer_name": "ACME Corp", "meeting_date": "2024-09-15"}}
    """
    
    response = await self._query_databricks_model(prompt, max_tokens=200)
    
    if not response:
      # Return None values if LLM fails
      return None, None
    
    try:
      import json
      # Extract JSON from response (LLM might include extra text)
      json_match = re.search(r'\{[^{}]*\}', response)
      if json_match:
        json_text = json_match.group()
        data = json.loads(json_text)
        return data.get('customer_name'), data.get('meeting_date')
      else:
        raise ValueError("No JSON found in response")
    except Exception as e:
      print(f"Error parsing LLM response: {e}")
      print(f"Response was: {response[:200]}")
      # Return None values if parsing fails
      return None, None

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
          formatted_date = self._parse_and_format_date(date_str)
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
    if category.value_type == CategoryValueType.PREDEFINED:
      return await self._process_predefined_category(text, category)
    else:
      return await self._process_inferred_category(text, category)

  async def _query_databricks_model(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
    """Query the Databricks Foundation Model endpoint."""
    if not self.databricks_client or not self.available_endpoints:
      print('Databricks client or endpoints not available')
      return None

    # Try each endpoint until one works
    for endpoint_idx, endpoint in enumerate(self.available_endpoints):
      print(f'\nTrying LLM endpoint {endpoint_idx + 1}/{len(self.available_endpoints)}: {endpoint}')
      
      try:
        # Create ChatMessage for the user prompt
        messages = [ChatMessage(role=ChatMessageRole.USER, content=prompt)]

        # Query with a reasonable timeout
        print(f'  Sending request...')
        
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
          timeout=60.0  # 60 second timeout to give LLM more time
        )

        print(f'  ✓ Success with {endpoint}!')

        # Extract the response content
        if response.choices and len(response.choices) > 0:
          content = response.choices[0].message.content
          print(f'  Response preview: {content[:100]}...')
          # Reset failure counter on success
          self.consecutive_failures = 0
          self.llm_available = True
          # Update primary endpoint for future calls
          if endpoint_idx > 0:
            self.available_endpoints[0], self.available_endpoints[endpoint_idx] = (
              self.available_endpoints[endpoint_idx], self.available_endpoints[0]
            )
          return content
        else:
          print('  No choices found in response')
          continue

      except asyncio.TimeoutError:
        print(f'  Timeout after 30 seconds')
        self.consecutive_failures += 1
        continue
      except Exception as e:
        error_str = str(e)[:200]
        print(f'  Error: {error_str}')
        self.consecutive_failures += 1
        
        # If it's an upstream error or endpoint not found, try next
        if 'upstream' in error_str.lower() or 'not found' in error_str.lower():
          continue
        # For other errors, also try next endpoint
        continue
    
    print('\nAll LLM endpoints failed. Using fallback.')
    # Mark LLM as unavailable after multiple failures
    if self.consecutive_failures >= self.max_consecutive_failures:
      self.llm_available = False
      print('  Disabling LLM usage due to repeated failures')
    return None

  async def _process_predefined_category(self, text: str, category) -> CategoryResult:
    """Process a category with predefined values."""
    prompt = f"""You are an AI assistant specialized in extracting customer insights from business meeting notes. Your task is to analyze customer conversations and identify relevant information based on predefined categories.

CONTEXT: This is a Customer Insights Extraction system designed to help sales and product teams understand customer needs, preferences, and requirements from meeting notes.

ANALYSIS TASK:
Category: {category.name}
Description: {category.description or 'No description provided'}
Available Options: {', '.join(category.possible_values)}

CUSTOMER MEETING NOTES:
"{text}"

ANALYSIS INSTRUCTIONS:
1. Carefully read the customer meeting notes above
2. Identify which of the available options are explicitly mentioned or clearly implied
3. Look for direct mentions, synonyms, or contextual references
4. Consider the business context - these are customer meetings about products/services
5. Only include values that have clear evidence in the text
6. Include multiple values if multiple are mentioned
7. Return empty list if no clear matches are found

RESPONSE FORMAT:
Respond with ONLY a JSON object in this exact format:
{{"values": ["option1", "option2"], "evidence": ["supporting text 1", "supporting text 2"], "confidence": 0.85}}

Where:
- values: list of matching options from the available options list
- evidence: specific text snippets that support each identified value
- confidence: score from 0.0 to 1.0 indicating your confidence level

Do not include any explanatory text, just the JSON object."""

    # Try Databricks Foundation Model first
    response_text = await self._query_databricks_model(prompt, max_tokens=500)

    if response_text:
      try:
        print(f'Raw Foundation Model response: {response_text[:500]}...')

        # Extract JSON from response (in case there's extra text)
        # Try to find JSON object - look for curly braces
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if not json_match:
          # Fallback: try to extract just the basic structure
          json_match = re.search(r'\{.*?"values".*?\}', response_text, re.DOTALL)

        if json_match:
          json_text = json_match.group()
          print(f'Extracted JSON: {json_text}')

          # Clean up the JSON text - remove any newlines inside strings
          json_text = re.sub(r'\n\s*', ' ', json_text)
          result_data = json.loads(json_text)

          print(f'Parsed JSON data successfully: {result_data}')

          return CategoryResult(
            category_name=category.name,
            values=result_data.get('values', []),
            confidence=result_data.get('confidence', 0.5),
            evidence_text=result_data.get('evidence', []),
            model_used=self.model_endpoint,
          )
        else:
          print(f'No JSON pattern found in response: {response_text}')
          raise ValueError('No valid JSON found in response')
      except json.JSONDecodeError as e:
        print(f'JSON parsing error: {e}')
        print(f'Attempted to parse: {json_text if "json_text" in locals() else "N/A"}')
      except Exception as e:
        print(f'Error parsing Databricks model response: {e}')
        print(f'Response was: {response_text[:200]}...')

    # No fallback - return empty result if LLM fails
    return CategoryResult(
      category_name=category.name,
      values=[],
      confidence=0.0,
      evidence_text=[],
      model_used="none",
      error="LLM failed to process this category"
    )

  async def _process_inferred_category(self, text: str, category) -> CategoryResult:
    """Process a category where values should be inferred by AI."""
    prompt = f"""You are an AI assistant specialized in extracting customer insights from business meeting notes. Your task is to analyze customer conversations and intelligently infer relevant information for open-ended categories.

CONTEXT: This is a Customer Insights Extraction system designed to help sales and product teams understand customer needs, preferences, and requirements from meeting notes.

ANALYSIS TASK:
Category: {category.name}
Description: {category.description or 'No description provided'}
Type: Open-ended (AI should infer appropriate values)

CUSTOMER MEETING NOTES:
"{text}"

ANALYSIS INSTRUCTIONS:
1. Carefully read the customer meeting notes above
2. Based on the category name and description, identify relevant information
3. Infer appropriate values that fit this category from the business context
4. Provide specific, concise values (1-4 words each)
5. Focus on business-relevant terms (products, industries, use cases, etc.)
6. Include multiple values if multiple aspects are mentioned or implied
7. Only include values that are clearly supported by the text content
8. Consider industry terminology, company context, and business needs

RESPONSE FORMAT:
Respond with ONLY a JSON object in this exact format:
{{"values": ["value1", "value2"], "evidence": ["supporting text 1", "supporting text 2"], "confidence": 0.85}}

Where:
- values: list of inferred values that fit this category
- evidence: specific text snippets that support each identified value
- confidence: score from 0.0 to 1.0 indicating your confidence level

Do not include any explanatory text, just the JSON object."""

    # Try Databricks Foundation Model first
    response_text = await self._query_databricks_model(prompt, max_tokens=500)

    if response_text:
      try:
        print(f'Raw Foundation Model response (inferred): {response_text[:500]}...')

        # Extract JSON from response (in case there's extra text)
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if not json_match:
          json_match = re.search(r'\{.*?"values".*?\}', response_text, re.DOTALL)

        if json_match:
          json_text = json_match.group()
          print(f'Extracted JSON (inferred): {json_text}')

          # Clean up the JSON text
          json_text = re.sub(r'\n\s*', ' ', json_text)
          result_data = json.loads(json_text)

          print(f'Parsed JSON data successfully (inferred): {result_data}')

          return CategoryResult(
            category_name=category.name,
            values=result_data.get('values', []),
            confidence=result_data.get('confidence', 0.5),
            evidence_text=result_data.get('evidence', []),
            model_used=self.model_endpoint,
          )
        else:
          raise ValueError('No valid JSON found in response')
      except json.JSONDecodeError as e:
        print(f'JSON parsing error (inferred): {e}')
        print(f'Attempted to parse: {json_text if "json_text" in locals() else "N/A"}')
      except Exception as e:
        print(f'Error parsing Databricks model response for inferred category: {e}')
        print(f'Response was: {response_text[:200]}...')

    # No fallback - return empty result if LLM fails
    return CategoryResult(
      category_name=category.name,
      values=[],
      confidence=0.0,
      evidence_text=[],
      model_used="none",
      error="LLM failed to process this category"
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

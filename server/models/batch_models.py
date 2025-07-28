"""Pydantic models for batch processing and spreadsheet export."""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field


class BatchInputType(str, Enum):
  """Type of input for batch processing."""
  TEXT = 'text'
  FILE = 'file'
  URL = 'url'


class BatchInput(BaseModel):
  """Single input item for batch processing."""
  input_type: BatchInputType
  content: str = Field(..., description='Text content, file path, or URL')
  filename: Optional[str] = Field(None, description='Original filename if applicable')
  
  model_config = {'use_enum_values': True}


class BatchAnalysisRequest(BaseModel):
  """Request for batch analysis of multiple inputs."""
  schema_template_id: str = Field(..., description='Schema template to use for analysis')
  inputs: List[BatchInput] = Field(..., description='List of inputs to process')
  extract_customer_info: bool = Field(True, description='Whether to extract customer name and meeting date')
  export_format: str = Field('csv', description='Export format (csv, xlsx)')
  
  model_config = {'use_enum_values': True}


class BatchItemResult(BaseModel):
  """Result for a single item in batch processing."""
  index: int = Field(..., description='Index in the original batch')
  input_type: BatchInputType
  filename: Optional[str] = None
  customer_name: Optional[str] = None
  meeting_date: Optional[str] = None
  categories: dict = Field(default_factory=dict)
  processing_time_ms: int
  word_count: int
  error: Optional[str] = None
  
  model_config = {'use_enum_values': True}


class BatchAnalysisResult(BaseModel):
  """Result of batch analysis with spreadsheet export."""
  total_items: int
  successful_items: int
  failed_items: int
  processing_time_ms: int
  results: List[BatchItemResult]
  spreadsheet_filename: str = Field(..., description='Suggested filename for download')
  
  model_config = {'use_enum_values': True}
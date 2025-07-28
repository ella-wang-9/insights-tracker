"""Pydantic models for document processing."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentSource(str, Enum):
  """Source type of the document."""

  TEXT_PASTE = 'text_paste'
  FILE_UPLOAD = 'file_upload'
  GOOGLE_DOCS = 'google_docs'


class DocumentInput(BaseModel):
  """Input document for processing."""

  document_id: Optional[str] = Field(None, description='Unique identifier for the document')
  source_type: DocumentSource = Field(..., description='How the document was provided')
  content: str = Field(..., description='Text content of the document')
  source_url: Optional[str] = Field(None, description='URL if from Google Docs')
  filename: Optional[str] = Field(None, description='Original filename if uploaded')
  metadata: Optional[Dict[str, Any]] = Field(
    default_factory=dict, description='Additional metadata'
  )

  model_config = {'use_enum_values': True}


class ProcessingRequest(BaseModel):
  """Request to process documents with a schema."""

  session_name: Optional[str] = Field(None, description='Name for this analysis session')
  schema_template_id: str = Field(..., description='ID of the schema template to use')
  documents: List[DocumentInput] = Field(..., description='Documents to process')
  user_id: Optional[str] = Field(None, description='User ID for the session')

  model_config = {'use_enum_values': True}


class ExtractedEntity(BaseModel):
  """An entity extracted from the document."""

  entity_text: str = Field(..., description='The extracted text')
  entity_type: str = Field(..., description="Type of entity (e.g., 'PERSON', 'ORG', 'DATE')")
  confidence: float = Field(..., description='Confidence score from 0 to 1')
  start_pos: Optional[int] = Field(None, description='Start position in text')
  end_pos: Optional[int] = Field(None, description='End position in text')


class CategoryResult(BaseModel):
  """Result for a single category classification."""

  category_name: str = Field(..., description='Name of the category')
  values: List[str] = Field(..., description='Extracted values for this category')
  confidence: float = Field(..., description='Overall confidence score for this category')
  evidence_text: List[str] = Field(
    default_factory=list, description='Text passages that support this classification'
  )
  model_used: str = Field(..., description='AI model used for this classification')
  error: Optional[str] = Field(None, description='Error message if processing failed')


class DocumentAnalysisResult(BaseModel):
  """Result of analyzing a single document."""

  document_id: str = Field(..., description='Unique identifier for the document')
  session_id: str = Field(..., description='Analysis session ID')
  customer_name: Optional[str] = Field(None, description='Extracted customer/company name')
  meeting_date: Optional[datetime] = Field(None, description='Extracted meeting date')
  extracted_categories: Dict[str, CategoryResult] = Field(
    ..., description='Results for each category'
  )
  extracted_entities: List[ExtractedEntity] = Field(
    default_factory=list, description='All extracted entities'
  )
  processing_time_ms: int = Field(..., description='Processing time in milliseconds')
  processed_at: datetime = Field(
    default_factory=datetime.now, description='When processing completed'
  )
  source_info: DocumentInput = Field(..., description='Original document information')

  model_config = {'use_enum_values': True}


class AnalysisSession(BaseModel):
  """An analysis session containing multiple documents."""

  session_id: str = Field(..., description='Unique session identifier')
  session_name: Optional[str] = Field(None, description='Human-readable session name')
  user_id: Optional[str] = Field(None, description='User who created this session')
  schema_template_id: str = Field(..., description='Schema template used for analysis')
  status: str = Field('running', description='Session status: running, completed, failed')
  total_documents: int = Field(0, description='Total number of documents in session')
  processed_documents: int = Field(0, description='Number of documents processed so far')
  created_at: datetime = Field(default_factory=datetime.now, description='When session was created')
  completed_at: Optional[datetime] = Field(None, description='When session completed')
  results: List[DocumentAnalysisResult] = Field(
    default_factory=list, description='Analysis results'
  )

  @property
  def progress_percentage(self) -> float:
    """Calculate progress as percentage."""
    if self.total_documents == 0:
      return 0.0
    return (self.processed_documents / self.total_documents) * 100

  model_config = {'use_enum_values': True}


class ProcessingProgress(BaseModel):
  """Progress update for real-time streaming."""

  session_id: str = Field(..., description='Session ID')
  document_id: Optional[str] = Field(None, description='Current document being processed')
  progress_percentage: float = Field(..., description='Overall progress percentage')
  current_stage: str = Field(..., description='Current processing stage')
  message: str = Field(..., description='Human-readable progress message')
  completed_documents: int = Field(..., description='Number of completed documents')
  total_documents: int = Field(..., description='Total number of documents')
  estimated_time_remaining_s: Optional[int] = Field(
    None, description='Estimated time remaining in seconds'
  )


class TextAnalysisRequest(BaseModel):
  """Simple request for analyzing text content."""

  text: str = Field(..., description='Text content to analyze')
  schema_template_id: str = Field(..., description='Schema template to use for analysis')
  extract_customer_info: bool = Field(
    True, description='Whether to extract customer name and meeting date'
  )

  model_config = {'use_enum_values': True}


class QuickAnalysisResult(BaseModel):
  """Quick analysis result for immediate feedback."""

  customer_name: Optional[str] = Field(None, description='Extracted customer name')
  meeting_date: Optional[str] = Field(None, description='Extracted meeting date as string')
  categories: Dict[str, CategoryResult] = Field(..., description='Category analysis results')
  processing_time_ms: int = Field(..., description='Time taken to process')
  word_count: int = Field(..., description='Number of words in the input text')

  model_config = {'use_enum_values': True}

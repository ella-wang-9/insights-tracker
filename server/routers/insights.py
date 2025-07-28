"""API endpoints for insights extraction."""

import io
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
import pandas as pd
from io import BytesIO

import docx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from server.models.document_models import (
  AnalysisSession,
  ProcessingRequest,
  QuickAnalysisResult,
  TextAnalysisRequest,
)
from server.models.batch_models import (
  BatchAnalysisRequest,
  BatchAnalysisResult,
  BatchInput,
  BatchInputType,
  BatchItemResult,
)
from server.routers.schema import _schemas
from server.services.ai_engine import ai_engine

router = APIRouter(prefix='/insights', tags=['Insights Extraction'])

# In-memory storage for development (will be replaced with Delta Tables)
_sessions: dict[str, AnalysisSession] = {}


@router.post('/analyze-text', response_model=QuickAnalysisResult)
async def analyze_text(request: TextAnalysisRequest) -> QuickAnalysisResult:
  """Quickly analyze text content with a given schema."""
  # Get the schema template
  if request.schema_template_id not in _schemas:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Schema template '{request.schema_template_id}' not found",
    )

  schema = _schemas[request.schema_template_id]

  # Analyze the text
  try:
    result = await ai_engine.analyze_text(
      text=request.text,
      schema=schema,
      extract_customer_info=request.extract_customer_info,
      fast_mode=False,
    )
    return result
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Error analyzing text: {str(e)}'
    )


@router.post('/analyze-document')
async def analyze_document(
  schema_template_id: str = Form(...),
  text: Optional[str] = Form(None),
  file: Optional[UploadFile] = File(None),
  google_drive_url: Optional[str] = Form(None),
) -> QuickAnalysisResult:
  """Analyze a document from various sources (text, file upload, or Google Drive)."""
  # Validate that at least one input source is provided
  if not any([text, file, google_drive_url]):
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail='Please provide either text, a file, or a Google Drive URL',
    )

  # Get the schema template
  if schema_template_id not in _schemas:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Schema template '{schema_template_id}' not found",
    )

  schema = _schemas[schema_template_id]

  # Extract text content based on source
  try:
    if text:
      content = text
    elif file:
      content = await extract_text_from_file(file)
    elif google_drive_url:
      content = await extract_text_from_google_drive(google_drive_url)
    else:
      raise ValueError('No valid input source')

    # Analyze the content
    result = await ai_engine.analyze_text(
      text=content, schema=schema, extract_customer_info=True, fast_mode=False
    )
    return result

  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f'Error processing document: {str(e)}',
    )


@router.post('/sessions', response_model=AnalysisSession)
async def create_analysis_session(request: ProcessingRequest) -> AnalysisSession:
  """Create a new analysis session for batch processing."""
  session_id = str(uuid4())

  # Create the session
  session = AnalysisSession(
    session_id=session_id,
    session_name=request.session_name or f'Session {datetime.now().strftime("%Y-%m-%d %H:%M")}',
    user_id=request.user_id,
    schema_template_id=request.schema_template_id,
    status='created',
    total_documents=len(request.documents),
    processed_documents=0,
  )

  # Store session
  _sessions[session_id] = session

  return session


@router.get('/sessions', response_model=List[AnalysisSession])
async def list_analysis_sessions(user_id: Optional[str] = None) -> List[AnalysisSession]:
  """List all analysis sessions, optionally filtered by user."""
  sessions = list(_sessions.values())
  if user_id:
    sessions = [s for s in sessions if s.user_id == user_id]
  return sessions


@router.get('/sessions/{session_id}', response_model=AnalysisSession)
async def get_analysis_session(session_id: str) -> AnalysisSession:
  """Get details of a specific analysis session."""
  if session_id not in _sessions:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND, detail=f"Analysis session '{session_id}' not found"
    )
  return _sessions[session_id]


@router.post('/sessions/{session_id}/start')
async def start_analysis_session(session_id: str) -> dict:
  """Start processing documents in an analysis session."""
  if session_id not in _sessions:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND, detail=f"Analysis session '{session_id}' not found"
    )

  session = _sessions[session_id]

  # Check if session is already running or completed
  if session.status != 'created':
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST, detail=f'Session is already {session.status}'
    )

  # Update session status
  session.status = 'running'
  _sessions[session_id] = session

  # TODO: Start background processing of documents
  # For now, just return success
  return {
    'message': f"Analysis session '{session_id}' started",
    'session_id': session_id,
    'status': 'running',
  }


@router.delete('/sessions/{session_id}')
async def delete_analysis_session(session_id: str) -> dict:
  """Delete an analysis session."""
  if session_id not in _sessions:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND, detail=f"Analysis session '{session_id}' not found"
    )

  session = _sessions[session_id]
  del _sessions[session_id]

  return {'message': f"Analysis session '{session.session_name}' deleted successfully"}


async def extract_text_from_file(file: UploadFile) -> str:
  """Extract text content from uploaded file."""
  content = await file.read()

  if file.filename.endswith('.txt'):
    return content.decode('utf-8', errors='ignore')
  elif file.filename.endswith('.docx'):
    doc = docx.Document(io.BytesIO(content))
    return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
  else:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail='Unsupported file type. Please upload .txt or .docx files.',
    )


async def extract_text_from_google_drive(google_drive_url: str) -> str:
  """Extract text content from Google Drive URL."""
  # For now, return a placeholder implementation
  # In production, this would:
  # 1. Parse the Google Drive file ID from the URL
  # 2. Use Google Drive API to download the file
  # 3. Extract text based on file type

  # Extract file ID from URL
  import re

  file_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', google_drive_url)
  if file_id_match:
    file_id = file_id_match.group(1)
    # Return placeholder text that indicates the feature is not implemented
    return (
      f'[Google Drive Integration Not Implemented]\n\n'
      f'This feature would extract content from Google Drive file ID: {file_id}\n\n'
      f'To implement this feature:\n'
      f'1. Set up Google Drive API credentials\n'
      f'2. Use Google Drive API to download the file\n'
      f'3. Extract text based on file type (Docs, Sheets, PDFs, etc.)'
    )
  else:
    return (
      '[Google Drive Integration Error]\n\n'
      'Could not extract file ID from the provided URL. '
      'Please ensure the URL is in the format: https://drive.google.com/file/d/FILE_ID/view'
    )


@router.get('/test-ai')
async def test_ai_connection() -> dict:
  """Test the AI engine connection and capabilities."""
  import os

  from databricks.sdk import WorkspaceClient

  # Environment diagnostics
  env_info = {
    'databricks_host': os.getenv('DATABRICKS_HOST', 'Not set'),
    'databricks_token_present': bool(os.getenv('DATABRICKS_TOKEN')),
    'databricks_auth_type': os.getenv('DATABRICKS_AUTH_TYPE', 'Not set'),
  }

  # Test Databricks client initialization
  databricks_status = {'initialized': False, 'error': None}
  try:
    client = WorkspaceClient()
    # Test basic connectivity
    user_info = client.current_user.me()
    databricks_status['initialized'] = True
    databricks_status['user'] = user_info.user_name
  except Exception as e:
    databricks_status['error'] = str(e)

  try:
    # Test with a simple text
    test_text = """
        Meeting with Acme Corp on March 15, 2024

        They are looking for a vector search solution for their e-commerce platform.
        Currently using keyword search but need semantic capabilities.
        Timeline is urgent - need to go live by Q2.
        """

    # Get a default schema for testing
    default_schema = _schemas.get('default_product_feedback')
    if not default_schema:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail='No default schema available for testing',
      )

    # Test direct Foundation Model query first
    direct_query_result = await ai_engine._query_databricks_model(
      'What company is mentioned in this text: Meeting with Acme Corp on March 15, 2024', 50
    )

    # Test the AI analysis
    result = await ai_engine.analyze_text(
      text=test_text, schema=default_schema, extract_customer_info=True
    )

    return {
      'status': 'success',
      'message': 'AI engine is working correctly',
      'environment': env_info,
      'databricks_client': databricks_status,
      'ai_engine_info': {
        'client_available': ai_engine.databricks_client is not None,
        'endpoint': ai_engine.model_endpoint,
      },
      'direct_query_test': {
        'result': direct_query_result,
        'success': direct_query_result is not None,
      },
      'test_result': {
        'customer_name': result.customer_name,
        'meeting_date': result.meeting_date,
        'categories_processed': len(result.categories),
        'processing_time_ms': result.processing_time_ms,
        'word_count': result.word_count,
        'models_used': [cat.model_used for cat in result.categories.values()],
      },
    }

  except Exception as e:
    return {
      'status': 'error',
      'message': f'AI engine test failed: {str(e)}',
      'error_type': type(e).__name__,
      'environment': env_info,
      'databricks_client': databricks_status,
    }


@router.post('/batch-analyze')
async def batch_analyze(
  inputs: List[UploadFile] = File(None),
  texts: Optional[List[str]] = Form(None),
  urls: Optional[List[str]] = Form(None),
  schema_template_id: str = Form(...),
  extract_customer_info: bool = Form(True),
  export_format: str = Form('xlsx')
):
  """Analyze multiple inputs (text, files, URLs) and export results as spreadsheet."""
  # Get the schema template
  if request.schema_template_id not in _schemas:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Schema template '{request.schema_template_id}' not found",
    )
  
  schema = _schemas[request.schema_template_id]
  start_time = datetime.now()
  results = []
  
  # Process each input
  for idx, input_item in enumerate(request.inputs):
    try:
      # Extract text based on input type
      if input_item.input_type == BatchInputType.TEXT:
        text_content = input_item.content
      elif input_item.input_type == BatchInputType.FILE:
        # Assume content is base64 encoded file content
        # In production, this would handle file uploads properly
        text_content = input_item.content  # Placeholder
      elif input_item.input_type == BatchInputType.URL:
        # Extract from Google Drive or other URLs
        text_content = await extract_text_from_google_drive(input_item.content)
      else:
        raise ValueError(f"Unknown input type: {input_item.input_type}")
      
      # Analyze the text
      analysis_result = await ai_engine.analyze_text(
        text=text_content,
        schema=schema,
        extract_customer_info=request.extract_customer_info,
        fast_mode=False,
      )
      
      # Convert to batch item result
      item_result = BatchItemResult(
        index=idx,
        input_type=input_item.input_type,
        filename=input_item.filename,
        customer_name=analysis_result.customer_name,
        meeting_date=analysis_result.meeting_date,
        categories={
          name: {
            'values': cat.values,
            'confidence': cat.confidence,
            'evidence': cat.evidence_text,
          }
          for name, cat in analysis_result.categories.items()
        },
        processing_time_ms=analysis_result.processing_time_ms,
        word_count=analysis_result.word_count,
      )
      results.append(item_result)
      
    except Exception as e:
      # Add error result
      results.append(
        BatchItemResult(
          index=idx,
          input_type=input_item.input_type,
          filename=input_item.filename,
          processing_time_ms=0,
          word_count=0,
          error=str(e),
        )
      )
  
  # Calculate stats
  successful_items = sum(1 for r in results if r.error is None)
  failed_items = len(results) - successful_items
  total_time = int((datetime.now() - start_time).total_seconds() * 1000)
  
  # Create spreadsheet
  spreadsheet_data, filename = create_spreadsheet(results, schema, request.export_format)
  
  # Store spreadsheet data temporarily (in production, use a proper storage)
  import tempfile
  temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{request.export_format}')
  temp_file.write(spreadsheet_data)
  temp_file.close()
  
  return BatchAnalysisResult(
    total_items=len(results),
    successful_items=successful_items,
    failed_items=failed_items,
    processing_time_ms=total_time,
    results=results,
    spreadsheet_filename=filename,
  )


def create_spreadsheet(results: List[BatchItemResult], schema, export_format: str) -> tuple[bytes, str]:
  """Create a spreadsheet from batch analysis results."""
  # Prepare data for DataFrame
  rows = []
  
  for result in results:
    row = {
      'Index': result.index + 1,
      'Input Type': result.input_type,
      'Filename': result.filename or '',
      'Customer Name': result.customer_name or '',
      'Meeting Date': result.meeting_date or '',
      'Word Count': result.word_count,
      'Processing Time (ms)': result.processing_time_ms,
      'Error': result.error or '',
    }
    
    # Add category columns
    for category in schema.categories:
      if result.categories and category.name in result.categories:
        cat_data = result.categories[category.name]
        row[f'{category.name} - Values'] = ', '.join(cat_data.get('values', []))
        row[f'{category.name} - Confidence'] = cat_data.get('confidence', 0)
        row[f'{category.name} - Evidence'] = ' | '.join(cat_data.get('evidence', []))[:200]  # Limit evidence length
      else:
        row[f'{category.name} - Values'] = ''
        row[f'{category.name} - Confidence'] = 0
        row[f'{category.name} - Evidence'] = ''
    
    rows.append(row)
  
  # Create DataFrame
  df = pd.DataFrame(rows)
  
  # Export to desired format
  output = BytesIO()
  timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
  
  if export_format == 'xlsx':
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
      df.to_excel(writer, index=False, sheet_name='Analysis Results')
      
      # Auto-adjust column widths
      worksheet = writer.sheets['Analysis Results']
      for column in df:
        column_length = max(df[column].astype(str).map(len).max(), len(column))
        col_idx = df.columns.get_loc(column)
        worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_length + 2, 50)
    
    filename = f'insights_analysis_{timestamp}.xlsx'
  else:  # CSV
    df.to_csv(output, index=False)
    filename = f'insights_analysis_{timestamp}.csv'
  
  output.seek(0)
  return output.read(), filename


@router.post('/batch-analyze/download')
async def batch_analyze_download(request: BatchAnalysisRequest):
  """Analyze multiple inputs and return spreadsheet file for download."""
  # Get the schema template
  if request.schema_template_id not in _schemas:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Schema template '{request.schema_template_id}' not found",
    )
  
  schema = _schemas[request.schema_template_id]
  start_time = datetime.now()
  results = []
  
  # Process each input (same logic as batch_analyze)
  for idx, input_item in enumerate(request.inputs):
    try:
      # Extract text based on input type
      if input_item.input_type == BatchInputType.TEXT:
        text_content = input_item.content
      elif input_item.input_type == BatchInputType.FILE:
        text_content = input_item.content  # Placeholder
      elif input_item.input_type == BatchInputType.URL:
        text_content = await extract_text_from_google_drive(input_item.content)
      else:
        raise ValueError(f"Unknown input type: {input_item.input_type}")
      
      # Analyze the text
      analysis_result = await ai_engine.analyze_text(
        text=text_content,
        schema=schema,
        extract_customer_info=request.extract_customer_info,
        fast_mode=False,
      )
      
      # Convert to batch item result
      item_result = BatchItemResult(
        index=idx,
        input_type=input_item.input_type,
        filename=input_item.filename,
        customer_name=analysis_result.customer_name,
        meeting_date=analysis_result.meeting_date,
        categories={
          name: {
            'values': cat.values,
            'confidence': cat.confidence,
            'evidence': cat.evidence_text,
          }
          for name, cat in analysis_result.categories.items()
        },
        processing_time_ms=analysis_result.processing_time_ms,
        word_count=analysis_result.word_count,
      )
      results.append(item_result)
      
    except Exception as e:
      # Add error result
      results.append(
        BatchItemResult(
          index=idx,
          input_type=input_item.input_type,
          filename=input_item.filename,
          processing_time_ms=0,
          word_count=0,
          error=str(e),
        )
      )
  
  # Create spreadsheet
  spreadsheet_data, filename = create_spreadsheet(results, schema, request.export_format)
  
  # Return file for download
  media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if request.export_format == 'xlsx' else 'text/csv'
  
  return StreamingResponse(
    BytesIO(spreadsheet_data),
    media_type=media_type,
    headers={
      'Content-Disposition': f'attachment; filename="{filename}"'
    }
  )
"""Batch processing endpoints for insights extraction."""

import io
from typing import List, Optional
from datetime import datetime
import pandas as pd
from io import BytesIO
import base64
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from server.models.batch_models import (
  BatchAnalysisRequest,
  BatchAnalysisResult,
  BatchInput,
  BatchInputType,
  BatchItemResult,
)
from server.routers.schema import _schemas
from server.services.ai_engine import ai_engine
from server.routers.insights import extract_text_from_file, extract_text_from_google_drive

router = APIRouter(prefix='/batch', tags=['Batch Processing'])


@router.get('/available-columns/{schema_template_id}')
async def get_available_columns(schema_template_id: str):
  """Get list of available columns for export selection."""
  if schema_template_id not in _schemas:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Schema template '{schema_template_id}' not found",
    )
  
  schema = _schemas[schema_template_id]
  
  # Base columns
  base_columns = [
    'Index',
    'Input Type', 
    'Source',
    'Customer Name',
    'Meeting Date',
    'Word Count',
    'Processing Time (ms)',
    'Error'
  ]
  
  # Category columns
  category_columns = [category.name for category in schema.categories]
  
  return {
    'base_columns': base_columns,
    'category_columns': category_columns,
    'all_columns': base_columns + category_columns
  }


@router.post('/analyze-files')
async def batch_analyze_files(
  files: List[UploadFile] = File(...),
  schema_template_id: str = Form(...),
  extract_customer_info: bool = Form(True),
  export_format: str = Form('xlsx'),
  selected_columns: Optional[str] = Form(None)  # JSON array of selected column names
):
  """Analyze multiple files and export results as spreadsheet."""
  # Get the schema template
  if schema_template_id not in _schemas:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Schema template '{schema_template_id}' not found",
    )
  
  schema = _schemas[schema_template_id]
  start_time = datetime.now()
  results = []
  
  # Process each file
  for idx, file in enumerate(files):
    try:
      # Extract text from file
      text_content = await extract_text_from_file(file)
      
      # Analyze the text
      analysis_result = await ai_engine.analyze_text(
        text=text_content,
        schema=schema,
        extract_customer_info=extract_customer_info,
        fast_mode=False,  # Always use LLM, no fast mode
      )
      
      # Convert to batch item result
      item_result = BatchItemResult(
        index=idx,
        input_type=BatchInputType.FILE,
        filename=file.filename,
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
          input_type=BatchInputType.FILE,
          filename=file.filename,
          processing_time_ms=0,
          word_count=0,
          error=str(e),
        )
      )
  
  # Create spreadsheet
  spreadsheet_data, filename = create_batch_spreadsheet(results, schema, export_format, selected_columns)
  
  # Return file for download
  media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if export_format == 'xlsx' else 'text/csv'
  
  return StreamingResponse(
    BytesIO(spreadsheet_data),
    media_type=media_type,
    headers={
      'Content-Disposition': f'attachment; filename="{filename}"'
    }
  )


@router.post('/analyze-mixed')
async def batch_analyze_mixed(
  schema_template_id: str = Form(...),
  texts: Optional[str] = Form(None),  # JSON array of texts
  urls: Optional[str] = Form(None),   # JSON array of URLs
  extract_customer_info: bool = Form(True),
  export_format: str = Form('xlsx'),
  selected_columns: Optional[str] = Form(None)  # JSON array of selected column names
):
  """Analyze multiple texts and URLs, export results as spreadsheet."""
  # Get the schema template
  if schema_template_id not in _schemas:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Schema template '{schema_template_id}' not found",
    )
  
  schema = _schemas[schema_template_id]
  start_time = datetime.now()
  results = []
  idx = 0
  
  # Parse JSON inputs
  import json
  text_list = json.loads(texts) if texts else []
  url_list = json.loads(urls) if urls else []
  
  # Process texts
  for text_content in text_list:
    try:
      # Analyze the text
      analysis_result = await ai_engine.analyze_text(
        text=text_content,
        schema=schema,
        extract_customer_info=extract_customer_info,
        fast_mode=False,  # Always use LLM, no fast mode
      )
      
      # Convert to batch item result
      item_result = BatchItemResult(
        index=idx,
        input_type=BatchInputType.TEXT,
        filename=f"Text {idx + 1}",
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
          input_type=BatchInputType.TEXT,
          filename=f"Text {idx + 1}",
          processing_time_ms=0,
          word_count=0,
          error=str(e),
        )
      )
    idx += 1
  
  # Process URLs
  for url in url_list:
    try:
      # Extract text from URL
      text_content = await extract_text_from_google_drive(url)
      
      # Analyze the text
      analysis_result = await ai_engine.analyze_text(
        text=text_content,
        schema=schema,
        extract_customer_info=extract_customer_info,
        fast_mode=False,  # Always use LLM, no fast mode
      )
      
      # Convert to batch item result
      item_result = BatchItemResult(
        index=idx,
        input_type=BatchInputType.URL,
        filename=url,
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
          input_type=BatchInputType.URL,
          filename=url,
          processing_time_ms=0,
          word_count=0,
          error=str(e),
        )
      )
    idx += 1
  
  # Create spreadsheet
  spreadsheet_data, filename = create_batch_spreadsheet(results, schema, export_format, selected_columns)
  
  # Return file for download
  media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if export_format == 'xlsx' else 'text/csv'
  
  return StreamingResponse(
    BytesIO(spreadsheet_data),
    media_type=media_type,
    headers={
      'Content-Disposition': f'attachment; filename="{filename}"'
    }
  )


@router.post('/analyze-all-with-preview')
async def batch_analyze_all_with_preview(
  files: List[UploadFile] = File(default=[]),
  schema_template_id: str = Form(...),
  texts: Optional[str] = Form(None),  # JSON array of texts
  urls: Optional[str] = Form(None),   # JSON array of URLs
  extract_customer_info: bool = Form(True),
  export_format: str = Form('xlsx'),
  selected_columns: Optional[str] = Form(None),  # JSON array of selected column names
  preview_only: bool = Form(False)
):
  """Unified endpoint to analyze files, texts, and URLs with preview."""
  # Get the schema template
  if schema_template_id not in _schemas:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Schema template '{schema_template_id}' not found",
    )
  
  schema = _schemas[schema_template_id]
  start_time = datetime.now()
  results = []
  idx = 0
  
  # Parse JSON inputs
  import json
  text_list = json.loads(texts) if texts else []
  url_list = json.loads(urls) if urls else []
  
  # Process files
  for file in files:
    try:
      # Extract text from file
      text = await extract_text_from_file(file)
      
      # Analyze the text
      analysis_result = await ai_engine.analyze_text(
        text=text,
        schema=schema,
        extract_customer_info=extract_customer_info,
        fast_mode=False,
      )
      
      # Convert to batch item result
      item_result = BatchItemResult(
        index=idx,
        input_type=BatchInputType.FILE,
        filename=file.filename,
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
          input_type=BatchInputType.FILE,
          filename=file.filename,
          processing_time_ms=0,
          word_count=0,
          error=str(e),
        )
      )
    idx += 1
  
  # Process texts
  for text_content in text_list:
    try:
      # Analyze the text
      analysis_result = await ai_engine.analyze_text(
        text=text_content,
        schema=schema,
        extract_customer_info=extract_customer_info,
        fast_mode=False,
      )
      
      # Convert to batch item result
      item_result = BatchItemResult(
        index=idx,
        input_type=BatchInputType.TEXT,
        filename=f'Text Input {idx + 1}',
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
          input_type=BatchInputType.TEXT,
          filename=f'Text Input {idx + 1}',
          processing_time_ms=0,
          word_count=0,
          error=str(e),
        )
      )
    idx += 1
  
  # Process URLs
  for url in url_list:
    try:
      # Extract text from URL
      text = await extract_text_from_google_drive(url)
      
      # Analyze the text
      analysis_result = await ai_engine.analyze_text(
        text=text,
        schema=schema,
        extract_customer_info=extract_customer_info,
        fast_mode=False,
      )
      
      # Convert to batch item result
      item_result = BatchItemResult(
        index=idx,
        input_type=BatchInputType.URL,
        filename=url,
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
          input_type=BatchInputType.URL,
          filename=url,
          processing_time_ms=0,
          word_count=0,
          error=str(e),
        )
      )
    idx += 1
  
  # Create spreadsheet
  spreadsheet_data, filename = create_batch_spreadsheet(results, schema, export_format, selected_columns)
  
  # Convert to base64 for JSON response
  import base64
  spreadsheet_base64 = base64.b64encode(spreadsheet_data).decode('utf-8')
  
  # Create table data for preview
  table_data = []
  for result in results:
    row = {
      'index': result.index + 1,
      'input_type': result.input_type,
      'filename': result.filename or '',
      'customer_name': result.customer_name or '',
      'meeting_date': result.meeting_date or '',
      'word_count': result.word_count,
      'processing_time_ms': result.processing_time_ms,
      'error': result.error or '',
      'categories': result.categories or {}
    }
    table_data.append(row)
  
  return {
    'filename': filename,
    'spreadsheet_base64': spreadsheet_base64,
    'table_data': table_data,
    'total_processed': len(results),
    'processing_time_ms': int((datetime.now() - start_time).total_seconds() * 1000)
  }


def create_batch_spreadsheet(results: List[BatchItemResult], schema, export_format: str, selected_columns: Optional[str] = None) -> tuple[bytes, str]:
  """Create a spreadsheet from batch analysis results."""
  # Parse selected columns if provided
  import json
  selected_cols_list = []
  if selected_columns:
    try:
      selected_cols_list = json.loads(selected_columns)
    except json.JSONDecodeError:
      selected_cols_list = []
  
  # Define all possible columns with their display names
  all_columns = [
    'Index',
    'Input Type', 
    'Source',
    'Customer Name',
    'Meeting Date',
    'Word Count',
    'Processing Time (ms)',
    'Error'
  ]
  
  # Add category columns
  category_columns = [category.name for category in schema.categories]
  all_columns.extend(category_columns)
  
  # If no columns selected, use all columns
  if not selected_cols_list:
    columns_to_include = all_columns
  else:
    columns_to_include = [col for col in all_columns if col in selected_cols_list]
  
  # Prepare data for DataFrame
  rows = []
  
  for result in results:
    # Create full row with all possible columns
    full_row = {
      'Index': result.index + 1,
      'Input Type': result.input_type,
      'Source': result.filename or '',
      'Customer Name': result.customer_name or '',
      'Meeting Date': result.meeting_date or '',
      'Word Count': result.word_count,
      'Processing Time (ms)': result.processing_time_ms,
      'Error': result.error or '',
    }
    
    # Add category columns with proper formatting
    for category in schema.categories:
      # Format category name: convert to title case and ensure proper spacing
      formatted_name = category.name
      if result.categories and category.name in result.categories:
        cat_data = result.categories[category.name]
        full_row[formatted_name] = ', '.join(cat_data.get('values', []))
      else:
        full_row[formatted_name] = ''
    
    # Filter row to only include selected columns
    filtered_row = {col: full_row.get(col, '') for col in columns_to_include if col in full_row}
    rows.append(filtered_row)
  
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
        if col_idx < 26:  # Excel columns A-Z
          worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_length + 2, 50)
    
    filename = f'batch_insights_{timestamp}.xlsx'
  else:  # CSV
    df.to_csv(output, index=False)
    filename = f'batch_insights_{timestamp}.csv'
  
  output.seek(0)
  return output.read(), filename


@router.post('/analyze-files-with-preview')
async def batch_analyze_files_with_preview(
  files: List[UploadFile] = File(...),
  schema_template_id: str = Form(...),
  extract_customer_info: bool = Form(True),
  export_format: str = Form('xlsx')
):
  """Analyze multiple files and return both preview data and download link."""
  # Get the schema template
  if schema_template_id not in _schemas:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Schema template '{schema_template_id}' not found",
    )
  
  schema = _schemas[schema_template_id]
  results = []
  
  # Process each file
  for idx, file in enumerate(files):
    try:
      # Extract text from file
      text_content = await extract_text_from_file(file)
      
      # Analyze the text
      analysis_result = await ai_engine.analyze_text(
        text=text_content,
        schema=schema,
        extract_customer_info=extract_customer_info,
        fast_mode=False,  # Always use LLM, no fast mode
      )
      
      # Convert to batch item result
      item_result = BatchItemResult(
        index=idx,
        input_type=BatchInputType.FILE,
        filename=file.filename,
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
          input_type=BatchInputType.FILE,
          filename=file.filename,
          processing_time_ms=0,
          word_count=0,
          error=str(e),
        )
      )
  
  # Create table data for preview
  table_data = []
  for result in results:
    row = {
      'source': result.filename or '',
      'customer_name': result.customer_name or '',
      'meeting_date': result.meeting_date or '',
    }
    
    # Add category columns
    for category in schema.categories:
      if result.categories and category.name in result.categories:
        cat_data = result.categories[category.name]
        row[category.name.lower().replace(' ', '_')] = ', '.join(cat_data.get('values', []))
      else:
        row[category.name.lower().replace(' ', '_')] = ''
    
    if result.error:
      row['error'] = result.error
    
    table_data.append(row)
  
  # Create spreadsheet
  spreadsheet_data, filename = create_batch_spreadsheet(results, schema, export_format, selected_columns)
  
  # Return preview data and download info
  import base64
  
  return {
    'filename': filename,
    'table_data': table_data,
    'spreadsheet_base64': base64.b64encode(spreadsheet_data).decode('utf-8'),
    'column_headers': ['Source', 'Customer Name', 'Meeting Date'] + [cat.name for cat in schema.categories]
  }


@router.post('/analyze-with-preview')
async def batch_analyze_with_preview(
  schema_template_id: str = Form(...),
  texts: Optional[str] = Form(None),  # JSON array of texts
  urls: Optional[str] = Form(None),   # JSON array of URLs
  extract_customer_info: bool = Form(True),
  export_format: str = Form('xlsx')
):
  """Analyze multiple documents and return both preview data and download link."""
  # Get the schema template
  if schema_template_id not in _schemas:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Schema template '{schema_template_id}' not found",
    )
  
  schema = _schemas[schema_template_id]
  results = []
  idx = 0
  
  # Parse JSON inputs
  import json
  text_list = json.loads(texts) if texts else []
  url_list = json.loads(urls) if urls else []
  
  # Process texts
  for text_content in text_list:
    try:
      analysis_result = await ai_engine.analyze_text(
        text=text_content,
        schema=schema,
        extract_customer_info=extract_customer_info,
        fast_mode=False,  # Always use LLM, no fast mode
      )
      
      item_result = BatchItemResult(
        index=idx,
        input_type=BatchInputType.TEXT,
        filename=f"Text {idx + 1}",
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
      results.append(
        BatchItemResult(
          index=idx,
          input_type=BatchInputType.TEXT,
          filename=f"Text {idx + 1}",
          processing_time_ms=0,
          word_count=0,
          error=str(e),
        )
      )
    idx += 1
  
  # Process URLs
  for url in url_list:
    try:
      text_content = await extract_text_from_google_drive(url)
      
      analysis_result = await ai_engine.analyze_text(
        text=text_content,
        schema=schema,
        extract_customer_info=extract_customer_info,
        fast_mode=False,  # Always use LLM, no fast mode
      )
      
      item_result = BatchItemResult(
        index=idx,
        input_type=BatchInputType.URL,
        filename=url,
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
      results.append(
        BatchItemResult(
          index=idx,
          input_type=BatchInputType.URL,
          filename=url,
          processing_time_ms=0,
          word_count=0,
          error=str(e),
        )
      )
    idx += 1
  
  # Create table data for preview
  table_data = []
  for result in results:
    row = {
      'source': result.filename or '',
      'customer_name': result.customer_name or '',
      'meeting_date': result.meeting_date or '',
    }
    
    # Add category columns
    for category in schema.categories:
      if result.categories and category.name in result.categories:
        cat_data = result.categories[category.name]
        row[category.name.lower().replace(' ', '_')] = ', '.join(cat_data.get('values', []))
      else:
        row[category.name.lower().replace(' ', '_')] = ''
    
    if result.error:
      row['error'] = result.error
    
    table_data.append(row)
  
  # Create spreadsheet
  spreadsheet_data, filename = create_batch_spreadsheet(results, schema, export_format, selected_columns)
  
  # Store in temporary storage with UUID
  import uuid
  import base64
  download_id = str(uuid.uuid4())
  
  # Return preview data and download info
  return {
    'download_id': download_id,
    'filename': filename,
    'table_data': table_data,
    'spreadsheet_base64': base64.b64encode(spreadsheet_data).decode('utf-8'),
    'column_headers': ['Source', 'Customer Name', 'Meeting Date'] + [cat.name for cat in schema.categories]
  }


@router.post('/analyze-all-with-preview')
async def batch_analyze_all_with_preview(
  files: List[UploadFile] = File(default=[]),
  texts: Optional[str] = Form(None),  # JSON array of texts
  urls: Optional[str] = Form(None),   # JSON array of URLs
  schema_template_id: str = Form(...),
  extract_customer_info: bool = Form(True),
  export_format: str = Form('xlsx')
):
  """Analyze all types of inputs (files, texts, URLs) and return both preview data and download link."""
  # Get the schema template
  if schema_template_id not in _schemas:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Schema template '{schema_template_id}' not found",
    )
  
  schema = _schemas[schema_template_id]
  results = []
  idx = 0
  
  # Parse JSON inputs
  import json
  text_list = json.loads(texts) if texts else []
  url_list = json.loads(urls) if urls else []
  
  # Define batch size for concurrent processing
  # Reduced to 2 to avoid overwhelming LLM endpoints
  batch_size = 2
  
  # Process files concurrently
  async def process_file(file, idx):
    try:
      # Extract text from file
      text_content = await extract_text_from_file(file)
      
      # Analyze the text
      analysis_result = await ai_engine.analyze_text(
        text=text_content,
        schema=schema,
        extract_customer_info=extract_customer_info,
        fast_mode=False,  # Always use LLM, no fast mode
      )
      
      # Convert to batch item result
      return BatchItemResult(
        index=idx,
        input_type=BatchInputType.FILE,
        filename=file.filename,
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
      
    except Exception as e:
      # Return error result
      return BatchItemResult(
        index=idx,
        input_type=BatchInputType.FILE,
        filename=file.filename,
        processing_time_ms=0,
        word_count=0,
        error=str(e),
      )
  
  # Process all files concurrently with limited concurrency
  file_tasks = []
  for i, file in enumerate(files):
    file_tasks.append(process_file(file, idx + i))
  
  # Process in batches of 3 to avoid overwhelming the LLM
  batch_size = 3
  for i in range(0, len(file_tasks), batch_size):
    batch = file_tasks[i:i + batch_size]
    batch_results = await asyncio.gather(*batch)
    results.extend(batch_results)
  
  idx += len(files)
  
  # Process texts concurrently
  async def process_text(text_content, text_idx, base_idx):
    try:
      # Analyze the text
      analysis_result = await ai_engine.analyze_text(
        text=text_content,
        schema=schema,
        extract_customer_info=extract_customer_info,
        fast_mode=False,  # Always use LLM, no fast mode
      )
      
      # Convert to batch item result
      return BatchItemResult(
        index=base_idx,
        input_type=BatchInputType.TEXT,
        filename=f"Text {text_idx + 1}",
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
      
    except Exception as e:
      # Return error result
      return BatchItemResult(
        index=base_idx,
        input_type=BatchInputType.TEXT,
        filename=f"Text {text_idx + 1}",
        processing_time_ms=0,
        word_count=0,
        error=str(e),
      )
  
  # Process all texts concurrently
  text_tasks = []
  for i, text_content in enumerate(text_list):
    text_tasks.append(process_text(text_content, i, idx + i))
  
  # Process in batches
  for i in range(0, len(text_tasks), batch_size):
    batch = text_tasks[i:i + batch_size]
    batch_results = await asyncio.gather(*batch)
    results.extend(batch_results)
  
  idx += len(text_list)
  
  # Process URLs concurrently
  async def process_url(url, url_idx, base_idx):
    try:
      # Extract text from URL
      text_content = await extract_text_from_google_drive(url)
      
      # Analyze the text
      analysis_result = await ai_engine.analyze_text(
        text=text_content,
        schema=schema,
        extract_customer_info=extract_customer_info,
        fast_mode=False,  # Always use LLM, no fast mode
      )
      
      # Convert to batch item result
      return BatchItemResult(
        index=base_idx,
        input_type=BatchInputType.URL,
        filename=url,
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
      
    except Exception as e:
      # Return error result
      return BatchItemResult(
        index=base_idx,
        input_type=BatchInputType.URL,
        filename=url,
        processing_time_ms=0,
        word_count=0,
        error=str(e),
      )
  
  # Process all URLs concurrently
  url_tasks = []
  for i, url in enumerate(url_list):
    url_tasks.append(process_url(url, i, idx + i))
  
  # Process in batches
  for i in range(0, len(url_tasks), batch_size):
    batch = url_tasks[i:i + batch_size]
    batch_results = await asyncio.gather(*batch)
    results.extend(batch_results)
  
  idx += len(url_list)
  
  # Create spreadsheet
  spreadsheet_data, filename = create_batch_spreadsheet(results, schema, export_format, selected_columns)
  
  # Also create table data for preview
  table_data = []
  column_headers = ['Source', 'Customer Name', 'Meeting Date'] + [cat.name for cat in schema.categories]
  
  for result in results:
    row_data = {
      'source': result.filename,
      'customer_name': result.customer_name or '',
      'meeting_date': result.meeting_date or '',
    }
    
    # Add category values
    for cat in schema.categories:
      if result.categories and cat.name in result.categories:
        values = result.categories[cat.name].get('values', [])
        row_data[cat.name.lower().replace(' ', '_')] = ', '.join(values) if values else ''
      else:
        row_data[cat.name.lower().replace(' ', '_')] = ''
    
    table_data.append(row_data)
  
  # Return both preview data and downloadable file
  return {
    'filename': filename,
    'table_data': table_data,
    'spreadsheet_base64': base64.b64encode(spreadsheet_data).decode('utf-8'),
    'column_headers': column_headers
  }
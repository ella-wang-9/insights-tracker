# Customer Insights Extractor - Technical Design Document

## Executive Summary

This document outlines the technical architecture for a streaming, AI-powered customer insights extraction platform built on Databricks. The system processes customer meeting notes through multiple input channels, applies intelligent categorization using foundation models, and delivers real-time results with persistent storage in Delta Tables.

## High-Level Architecture

### System Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Input Layer   │───▶│ Processing Core │───▶│  AI/ML Engine   │───▶│  Storage Layer  │
│                 │    │                 │    │                 │    │                 │
│ • Google Docs   │    │ • Document      │    │ • Databricks    │    │ • Delta Tables  │
│ • File Upload   │    │   Parsing       │    │   Foundation    │    │ • Schema Store  │
│ • Text Paste    │    │ • Content       │    │   Models        │    │ • Results Cache │
│                 │    │   Extraction    │    │ • OpenAI GPT-4  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Frontend (React)│    │ Streaming API   │    │ Confidence      │    │ Analytics &     │
│                 │    │                 │    │ Scoring         │    │ Reporting       │
│ • Real-time UI  │    │ • WebSocket     │    │ • Learning      │    │                 │
│ • Progress Bars │    │ • Background    │    │   Pipeline      │    │ • Dashboards    │
│ • Result Tables │    │   Jobs          │    │ • Model         │    │ • Exports       │
│                 │    │ • Status Track  │    │   Comparison    │    │ • Visualizations│
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack

**Backend Framework**: FastAPI with Python 3.11+
- **Rationale**: Excellent async support for streaming, automatic OpenAPI generation, strong typing

**Frontend Framework**: React 18 + TypeScript + Vite
- **Rationale**: Already configured, excellent ecosystem, great TypeScript support

**AI/ML Platform**: Databricks Foundation Models + OpenAI GPT-4
- **Rationale**: Best of both worlds - Databricks integration + proven NLP capabilities

**Data Storage**: Databricks Delta Tables
- **Rationale**: ACID transactions, time travel, schema evolution, perfect Databricks integration

**Real-time Communication**: WebSockets + Server-Sent Events
- **Rationale**: True bidirectional streaming for progress updates and results

## Libraries and Frameworks

### Backend Dependencies (Add to pyproject.toml)
```toml
# Document Processing
"python-docx>=1.1.0"           # Word document parsing
"PyPDF2>=3.0.1"               # PDF parsing (future use)
"google-api-python-client>=2.108.0"  # Google Docs API
"google-auth>=2.23.4"         # Google OAuth

# AI/ML and NLP
"openai>=1.3.0"               # OpenAI GPT models
"spacy>=3.7.2"                # Named entity recognition
"transformers>=4.35.0"        # Hugging Face models (backup)

# Streaming and Async
"websockets>=12.0"            # WebSocket support
"asyncio-mqtt>=0.16.0"        # Message queuing
"celery>=5.3.4"               # Background job processing

# Data Processing
"pandas>=2.1.0"               # Already included
"numpy>=1.24.0"               # Already included
"sqlalchemy>=2.0.0"           # Already included

# API and Authentication
"google-auth-oauthlib>=1.1.0" # Google OAuth flow
"jwt>=1.3.1"                  # JWT token handling
```

### Frontend Dependencies (Add to client/package.json)
```json
{
  "dependencies": {
    "@tanstack/react-table": "^8.10.7",     // Data tables
    "react-dropzone": "^14.2.3",            // File upload
    "file-saver": "^2.0.5",                 // File downloads
    "zustand": "^4.4.7",                    // State management
    "react-hook-form": "^7.48.2",           // Form handling
    "socket.io-client": "^4.7.4",           // WebSocket client
    "react-markdown": "^9.0.1",             // Markdown rendering
    "react-virtualized": "^9.22.5"          // Large data virtualization
  }
}
```

## Data Architecture

### Delta Tables Schema Design

```sql
-- User Schema Templates
CREATE TABLE schema_templates (
  template_id STRING NOT NULL,
  user_id STRING NOT NULL,
  template_name STRING NOT NULL,
  categories ARRAY<STRUCT<
    name: STRING,
    description: STRING,
    value_type: STRING,  -- 'predefined' or 'inferred'
    possible_values: ARRAY<STRING>
  >>,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  is_default BOOLEAN DEFAULT FALSE
) USING DELTA
PARTITIONED BY (user_id)
LOCATION 's3://databricks-workspace/insights-tracker/schema_templates'

-- Analysis Sessions
CREATE TABLE analysis_sessions (
  session_id STRING NOT NULL,
  user_id STRING NOT NULL,
  session_name STRING,
  schema_template_id STRING,
  status STRING, -- 'running', 'completed', 'failed'
  total_documents INT DEFAULT 0,
  processed_documents INT DEFAULT 0,
  created_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP,
  metadata MAP<STRING, STRING>
) USING DELTA
PARTITIONED BY (user_id, DATE(created_at))
LOCATION 's3://databricks-workspace/insights-tracker/analysis_sessions'

-- Document Processing Results
CREATE TABLE document_insights (
  insight_id STRING NOT NULL,
  session_id STRING NOT NULL,
  document_id STRING NOT NULL,
  document_source STRING, -- 'google_docs', 'file_upload', 'text_paste'
  source_url STRING,
  customer_name STRING,
  meeting_date DATE,
  extracted_categories MAP<STRING, STRUCT<
    values: ARRAY<STRING>,
    confidence: DOUBLE,
    evidence_text: ARRAY<STRING>,
    model_used: STRING
  >>,
  processing_time_ms BIGINT,
  processed_at TIMESTAMP NOT NULL,
  user_corrections MAP<STRING, ARRAY<STRING>> -- User feedback for learning
) USING DELTA
PARTITIONED BY (session_id, DATE(processed_at))
LOCATION 's3://databricks-workspace/insights-tracker/document_insights'

-- Model Performance Tracking
CREATE TABLE model_performance (
  performance_id STRING NOT NULL,
  model_name STRING NOT NULL,
  category_name STRING,
  accuracy_score DOUBLE,
  confidence_score DOUBLE,
  processing_time_ms BIGINT,
  sample_size INT,
  evaluated_at TIMESTAMP NOT NULL
) USING DELTA
PARTITIONED BY (model_name, DATE(evaluated_at))
LOCATION 's3://databricks-workspace/insights-tracker/model_performance'
```

### Databricks Workspace Integration

**Shared Access Pattern**:
```python
# Generate sharable links for Delta Tables
def create_shared_analysis_link(session_id: str, user_id: str) -> str:
    """Create a shareable Databricks SQL dashboard link for analysis results"""
    dashboard_query = f"""
    SELECT 
      customer_name,
      meeting_date,
      extracted_categories,
      source_url
    FROM document_insights 
    WHERE session_id = '{session_id}'
    ORDER BY meeting_date DESC
    """
    return f"https://databricks.com/workspace/sql/dashboards/shared/{session_id}"
```

## AI/ML Pipeline Architecture

### Hybrid Model Strategy

**Primary Processing Pipeline**:
```python
class HybridCategorizationEngine:
    def __init__(self):
        self.databricks_client = DatabricksClient()
        self.openai_client = OpenAIClient()
        self.spacy_nlp = spacy.load("en_core_web_lg")
    
    async def categorize_document(self, text: str, schema: CategorySchema) -> CategoryResults:
        # 1. Preprocessing
        entities = self.extract_entities(text)
        chunks = self.chunk_document(text)
        
        # 2. Parallel Model Processing
        databricks_results = await self.databricks_categorize(chunks, schema)
        openai_results = await self.openai_categorize(chunks, schema)
        
        # 3. Confidence Scoring & Model Selection
        final_results = self.merge_results(databricks_results, openai_results)
        
        return final_results
```

**Model Performance Optimization**:
- **A/B Testing**: Track which model performs better for different category types
- **Confidence Thresholding**: Use high-confidence results immediately, queue low-confidence for review
- **Caching**: Cache common categorizations to reduce API calls
- **Learning Pipeline**: Incorporate user corrections to improve future predictions

## Streaming Processing Architecture

### Real-time Communication Flow

```python
# FastAPI WebSocket endpoint
@app.websocket("/ws/analysis/{session_id}")
async def analysis_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    # Start background processing
    task = asyncio.create_task(process_documents_stream(session_id, websocket))
    
    try:
        while True:
            # Listen for client messages (pause, resume, cancel)
            message = await websocket.receive_json()
            await handle_client_message(message, task)
    except WebSocketDisconnect:
        task.cancel()

async def process_documents_stream(session_id: str, websocket: WebSocket):
    """Stream processing results as they complete"""
    async for document_result in process_document_batch(session_id):
        # Send real-time update
        await websocket.send_json({
            "type": "document_completed",
            "document_id": document_result.id,
            "results": document_result.categories,
            "progress": calculate_progress(session_id)
        })
        
        # Save to Delta Table
        await save_document_insight(document_result)
```

### Background Job Processing

**Celery Task Queue**:
```python
from celery import Celery

celery_app = Celery('insights_extractor')

@celery_app.task
async def process_document_async(document_id: str, session_id: str, content: str):
    """Background task for document processing"""
    try:
        result = await categorization_engine.process(content)
        await update_session_progress(session_id, document_id, result)
        return result
    except Exception as e:
        await mark_document_failed(document_id, str(e))
        raise
```

## Integration Points

### Google Docs API Integration

**OAuth Flow**:
```python
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow

class GoogleDocsClient:
    def __init__(self):
        self.flow = Flow.from_client_config(
            client_config=GOOGLE_CLIENT_CONFIG,
            scopes=['https://www.googleapis.com/auth/documents.readonly']
        )
    
    async def get_document_content(self, doc_url: str, access_token: str) -> str:
        """Extract text content from Google Docs"""
        doc_id = self.extract_doc_id(doc_url)
        service = build('docs', 'v1', credentials=credentials)
        document = service.documents().get(documentId=doc_id).execute()
        return self.extract_text_from_doc(document)
```

### File Processing Integration

**Multi-format Support**:
```python
class DocumentProcessor:
    async def process_file(self, file: UploadFile) -> str:
        if file.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            return await self.process_docx(file)
        elif file.content_type == 'application/pdf':
            return await self.process_pdf(file)
        elif file.content_type == 'text/plain':
            return await self.process_txt(file)
        else:
            raise UnsupportedFileTypeError(f"Unsupported file type: {file.content_type}")
```

## Implementation Plan

### Phase 1: Core Analysis Engine (Weeks 1-3)

**Week 1: Foundation**
- ✅ **Replace WelcomePage** with Insights Extractor UI
- ✅ **Add core backend dependencies** (openai, python-docx, google-api-client)
- ✅ **Create basic schema management** (define categories, save/load templates)
- ✅ **Implement text input processing** (paste area with analysis)

**Week 2: Document Processing**
- ✅ **Add file upload capability** (.docx, .txt support)
- ✅ **Implement Google Docs URL processing** (basic content extraction)
- ✅ **Create AI categorization pipeline** (OpenAI GPT-4 integration)
- ✅ **Add customer name/date extraction** (NER with spacy)

**Week 3: Results & Export**
- ✅ **Build results display table** (with confidence indicators)
- ✅ **Implement CSV export** (Google Sheets compatible format)
- ✅ **Add basic error handling** (graceful failure modes)
- ✅ **Create simple progress indicators** (document-by-document updates)

### Phase 2: Intelligence and Streaming (Weeks 4-6)

**Week 4: Databricks Integration**
- ✅ **Set up Delta Tables** (create schemas, test data persistence)
- ✅ **Integrate Databricks Foundation Models** (parallel with OpenAI)
- ✅ **Implement model performance comparison** (A/B testing framework)
- ✅ **Add confidence scoring system** (hybrid model confidence)

**Week 5: Real-time Processing**
- ✅ **Implement WebSocket streaming** (real-time progress updates)
- ✅ **Create background job processing** (async document handling)
- ✅ **Add batch processing capabilities** (multiple URLs/files)
- ✅ **Build review queue interface** (low-confidence results)

**Week 6: Learning System**
- ✅ **Create correction interface** (edit AI categorizations)
- ✅ **Implement learning pipeline** (incorporate user feedback)
- ✅ **Add transparency features** (show evidence text)
- ✅ **Build schema template system** (save/reuse schemas)

### Phase 3: Advanced Analytics (Weeks 7-8)

**Week 7: Analytics Dashboard**
- ✅ **Create executive summary dashboard** (high-level insights)
- ✅ **Implement cross-category analysis** (relationship insights)
- ✅ **Add trend visualization** (time-based patterns)
- ✅ **Build customer segmentation views** (group by attributes)

**Week 8: Polish and Optimization**
- ✅ **Performance optimization** (caching, parallel processing)
- ✅ **Enhanced error handling** (retry logic, graceful degradation)
- ✅ **UI/UX improvements** (loading states, animations)
- ✅ **Comprehensive testing** (unit tests, integration tests)

## Development Workflow

### Additive Development Approach
**The implementation will ONLY add to the existing system**:
- ✅ **REPLACE** WelcomePage.tsx with InsightsExtractorApp.tsx
- ✅ **ADD** new API endpoints to `server/routers/insights.py`
- ✅ **ADD** new React components to `client/src/components/insights/`
- ✅ **ADD** new pages to `client/src/pages/`
- ✅ **EXTEND** existing FastAPI app configuration
- ✅ **ENHANCE** existing React app structure

### Validation Workflow
**During implementation, ALWAYS**:
1. **Start development server**: `nohup ./watch.sh > /tmp/databricks-app-watch.log 2>&1 &`
2. **Test each API endpoint**: Verify with curl after adding each endpoint
3. **Use Playwright for UI validation**: Take snapshots after each UI change
4. **Check logs continuously**: Monitor `/tmp/databricks-app-watch.log`
5. **Iterative testing**: Verify each feature before moving to next

### File Structure
```
server/
├── routers/
│   ├── insights.py          # Main insights extraction API
│   ├── schema.py            # Schema management API
│   └── analytics.py         # Dashboard and reporting API
├── services/
│   ├── document_processor.py    # Document parsing and extraction
│   ├── ai_engine.py            # AI categorization pipeline
│   ├── databricks_client.py    # Delta Tables integration
│   └── google_docs_client.py   # Google Docs API client
└── models/
    ├── schema_models.py        # Pydantic models for schemas
    ├── document_models.py      # Document processing models
    └── result_models.py        # Analysis result models

client/src/
├── components/insights/
│   ├── SchemaBuilder.tsx       # Category schema creation
│   ├── DocumentInput.tsx       # File upload and URL input
│   ├── ProcessingProgress.tsx  # Real-time progress display
│   ├── ResultsTable.tsx       # Analysis results display
│   └── AnalyticsDashboard.tsx  # Executive summary dashboard
├── pages/
│   └── InsightsExtractorApp.tsx  # Main application page
└── hooks/
    ├── useWebSocket.ts         # WebSocket streaming hook
    ├── useDocumentProcessor.ts # Document processing hook
    └── useAnalytics.ts         # Analytics data hook
```

## Performance and Scalability Considerations

### Processing Optimization
- **Parallel Document Processing**: Process multiple documents simultaneously
- **Intelligent Chunking**: Break large documents into optimal-sized chunks
- **Result Caching**: Cache common categorizations to reduce API calls
- **Model Selection**: Use faster models for simple categories, complex models for nuanced ones

### Data Architecture Scalability
- **Partitioned Delta Tables**: Partition by user_id and date for optimal query performance
- **Incremental Processing**: Only reprocess changed documents
- **Retention Policies**: Automated cleanup of old analysis sessions
- **Backup Strategy**: Regular snapshots of Delta Tables for disaster recovery

### User Experience Optimization
- **Progressive Loading**: Show results as they become available
- **Offline Capability**: Cache schemas and partial results for offline editing
- **Mobile Responsiveness**: Ensure dashboard works on mobile devices
- **Accessibility**: Full WCAG 2.1 compliance for inclusive design

---

*This technical design provides a comprehensive blueprint for building a production-ready, scalable customer insights extraction platform that leverages the full power of the Databricks ecosystem while maintaining excellent user experience through modern web technologies.*
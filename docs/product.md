# Customer Insights Extractor - Product Requirements Document

## Executive Summary

**Problem Statement**: Product managers spend countless hours manually reviewing customer call notes to extract actionable insights, categorize feedback, and identify patterns. This manual process is time-consuming, inconsistent, and doesn't scale as customer interactions grow.

**Solution**: A smart customer insights extraction platform that transforms unstructured customer feedback from meeting notes into structured, analyzable data. The system uses AI to automatically categorize feedback based on custom schemas while providing transparency and learning capabilities.

**Key Value Propositions**:
- Transform hours of manual analysis into minutes of automated processing
- Ensure consistent categorization across all customer feedback
- Generate executive-ready dashboards and reports
- Enable data-driven product decisions through structured insights

## Target Users

**Primary User**: Product Managers
- **Pain Points**: Manual analysis of customer feedback, inconsistent categorization, difficulty identifying patterns across multiple customer interactions
- **Goals**: Quickly understand customer needs, track feedback trends, generate reports for stakeholders
- **Usage Context**: Weekly/monthly analysis of customer call notes, preparing for product planning sessions, creating executive updates

**User Personas**:
- Senior PM analyzing 20-50 customer interactions per month
- PM leads needing cross-team visibility into customer feedback
- Product teams preparing quarterly business reviews

## Core Features

### 1. Flexible Document Input System
**Description**: Multiple ways to input customer meeting notes for analysis
**Capabilities**:
- **Google Docs URL Input**: Paste links to Google Docs containing meeting notes
- **File Upload**: Upload .docx files directly
- **Text Paste**: Direct paste of meeting notes for quick analysis
- **Bulk Processing**: Handle multiple documents simultaneously with progress tracking
- **Document Preview**: Verify content before processing

### 2. Smart Category Schema System
**Description**: Flexible categorization system supporting both predefined and AI-inferred values
**Capabilities**:
- **Custom Categories**: Users define category names (e.g., "Product", "Industry", "Usage Pattern")
- **Dual Value Types**:
  - **Predefined Values**: Specific list provided by user (e.g., Product: "Vector Search, Embedding FT, Keyword Search")
  - **AI-Inferred Values**: System infers appropriate values based on category name/description (e.g., Industry → automatically detects "Retail", "Finance", etc.)
- **Category Descriptions**: Optional descriptions to guide AI inference
- **Schema Management**: Save, reuse, and modify schemas across analysis sessions
- **Confidence Indicators**: Visual indicators showing AI confidence in categorizations

### 3. Intelligent Content Analysis
**Description**: AI-powered extraction and categorization of insights from unstructured text
**Capabilities**:
- **Customer Identification**: Automatically extract customer/company names from documents
- **Meeting Date Extraction**: Identify and extract meeting dates
- **Implicit Information Inference**: Understand context and implied meanings (e.g., "overnight processing" → "Batch" usage pattern)
- **Ambiguity Handling**: Manage cases where content fits multiple categories
- **Multi-value Support**: Extract multiple relevant values per category when appropriate

### 4. Learning and Correction System
**Description**: Human-in-the-loop system for improving AI accuracy over time
**Capabilities**:
- **Review Queue**: Low-confidence categorizations flagged for manual review
- **Correction Interface**: Easy way to modify AI categorizations
- **Learning System**: AI improves based on user corrections
- **Transparency**: Show which text passages led to specific categorizations

### 5. Structured Output Generation
**Description**: Transform analyzed insights into ready-to-use formats
**Capabilities**:
- **Google Sheets Format**: Table with hyperlinked customer names, meeting dates, and category columns
- **CSV Export**: Standard CSV format for further analysis
- **Hyperlink Generation**: Customer names as clickable links to source documents
- **Multi-value Cell Support**: Comma-separated values for Google Sheets "chips"

### 6. Analytics and Reporting
**Description**: Visual insights and summary reports from extracted data
**Capabilities**:
- **Executive Dashboards**: High-level overview of customer feedback trends
- **Cross-Category Insights**: Relationship analysis between different categories (e.g., "Retail customers 3x more likely to request Real-Time features")
- **Historical Comparison**: Track changes over time periods
- **Action Item Generation**: Identify patterns that suggest specific actions
- **Stakeholder Sharing**: Export reports for different audiences

## User Stories

### Schema Creation and Management
- **As a PM**, I want to create custom category schemas so that I can analyze feedback relevant to my product area
- **As a PM**, I want to save and reuse schemas so that I can maintain consistency across analysis sessions
- **As a PM**, I want to define some categories with specific values and others as open-ended so that I have flexibility in my analysis

### Document Processing
- **As a PM**, I want to paste multiple Google Docs URLs so that I can analyze all my customer meetings from this week
- **As a PM**, I want to upload Word documents so that I can analyze offline meeting notes
- **As a PM**, I want to see processing progress so that I know when my analysis will be complete

### Analysis and Review
- **As a PM**, I want to review low-confidence categorizations so that I can ensure accuracy
- **As a PM**, I want to correct AI mistakes so that the system learns and improves
- **As a PM**, I want to see which text led to each categorization so that I can understand the AI's reasoning

### Output and Reporting
- **As a PM**, I want to export results to Google Sheets so that I can share with my team
- **As a PM**, I want to see cross-category insights so that I can identify customer patterns
- **As a PM**, I want to generate executive summaries so that I can update leadership on customer feedback trends

## Success Metrics

### Efficiency Metrics
- **Time Reduction**: 90% reduction in time spent on manual categorization
- **Processing Speed**: Analyze 10+ documents in under 5 minutes
- **Accuracy Rate**: 85%+ correct categorizations without human intervention

### Usage Metrics
- **User Adoption**: Weekly active users among target PM population
- **Processing Volume**: Number of documents processed per user per month
- **Schema Reuse**: Percentage of analyses using saved schemas

### Business Impact
- **Decision Speed**: Faster time-to-insight for product decisions
- **Coverage**: Increased percentage of customer feedback being systematically analyzed
- **Consistency**: Reduced variance in categorization across different PMs

## Implementation Priority

### Phase 1: Core Analysis Engine (MVP)
- Document input (Google Docs URLs, file upload, text paste)
- Basic schema creation (categories with predefined values)
- AI-powered categorization
- Google Sheets/CSV export
- Customer name extraction

### Phase 2: Intelligence and Learning
- AI-inferred category values
- Confidence indicators and review queue
- Correction system with learning
- Schema management (save/reuse)
- Transparency features

### Phase 3: Advanced Analytics
- Cross-category insights
- Executive dashboards
- Historical comparison
- Action item generation
- Enhanced visualizations

## Technical Considerations

### Data Sources
- Google Docs API integration
- Document parsing (.docx, .txt)
- Text preprocessing and cleaning

### AI/ML Requirements
- Natural language processing for categorization
- Named entity recognition for customer extraction
- Machine learning pipeline for continuous improvement
- Confidence scoring algorithms

### Output Formats
- Google Sheets API integration
- CSV generation
- Hyperlink formatting
- Report templating system

### Infrastructure
- Databricks platform for data processing
- Scalable document processing pipeline
- User session management
- Schema persistence

---

*This PRD serves as the foundation for technical architecture planning and implementation. All features are designed to directly address the core user need: transforming unstructured customer feedback into actionable product insights with minimal manual effort.*
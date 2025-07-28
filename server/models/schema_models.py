"""Pydantic models for schema management."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class CategoryValueType(str, Enum):
  """Type of category values."""

  PREDEFINED = 'predefined'  # User provides specific values
  INFERRED = 'inferred'  # AI infers values from category name/description


class CategoryDefinition(BaseModel):
  """Definition of a single category in a schema."""

  name: str = Field(..., description="Name of the category (e.g., 'Product', 'Industry')")
  description: Optional[str] = Field(None, description='Optional description to guide AI inference')
  value_type: CategoryValueType = Field(
    ..., description='Whether values are predefined or AI-inferred'
  )
  possible_values: Optional[List[str]] = Field(
    None, description='Predefined values (only for predefined type)'
  )

  model_config = {'use_enum_values': True}


class SchemaTemplate(BaseModel):
  """A schema template for categorizing customer insights."""

  template_id: Optional[str] = Field(None, description='Unique identifier for the template')
  template_name: str = Field(..., description='Human-readable name for the template')
  categories: List[CategoryDefinition] = Field(..., description='List of categories in this schema')
  user_id: Optional[str] = Field(None, description='User who created this template')
  is_default: bool = Field(False, description='Whether this is a default template')
  created_at: Optional[datetime] = Field(None, description='When the template was created')
  updated_at: Optional[datetime] = Field(None, description='When the template was last updated')

  model_config = {'use_enum_values': True}


class CreateSchemaRequest(BaseModel):
  """Request to create a new schema template."""

  template_name: str = Field(..., description='Name for the new template')
  categories: List[CategoryDefinition] = Field(
    ..., description='Categories to include in the schema'
  )

  model_config = {'use_enum_values': True}


class UpdateSchemaRequest(BaseModel):
  """Request to update an existing schema template."""

  template_name: Optional[str] = Field(None, description='New name for the template')
  categories: Optional[List[CategoryDefinition]] = Field(None, description='Updated categories')

  model_config = {'use_enum_values': True}


class SchemaValidationError(BaseModel):
  """Error details for schema validation."""

  field: str = Field(..., description='Field that failed validation')
  message: str = Field(..., description='Error message')


class SchemaValidationResponse(BaseModel):
  """Response for schema validation requests."""

  is_valid: bool = Field(..., description='Whether the schema is valid')
  errors: List[SchemaValidationError] = Field(
    default_factory=list, description='Validation errors if any'
  )


# Default schema templates
DEFAULT_PRODUCT_FEEDBACK_SCHEMA = SchemaTemplate(
  template_id='default_product_feedback',
  template_name='Product Feedback Template',
  categories=[
    CategoryDefinition(
      name='Product',
      description='Databricks products mentioned in the feedback',
      value_type=CategoryValueType.PREDEFINED,
      possible_values=[
        'Vector Search',
        'Embedding FT',
        'Keyword Search',
        'MLflow',
        'Delta Lake',
        'Unity Catalog',
      ],
    ),
    CategoryDefinition(
      name='Industry',
      description="Customer's industry vertical",
      value_type=CategoryValueType.INFERRED,
    ),
    CategoryDefinition(
      name='Usage Pattern',
      description='How the customer uses or plans to use the product',
      value_type=CategoryValueType.PREDEFINED,
      possible_values=['Batch', 'Real-Time', 'Interactive', 'Scheduled'],
    ),
    CategoryDefinition(
      name='Use Case',
      description='Specific use case or application area',
      value_type=CategoryValueType.INFERRED,
    ),
  ],
  is_default=True,
  created_at=datetime.now(),
)

DEFAULT_FEATURE_REQUESTS_SCHEMA = SchemaTemplate(
  template_id='default_feature_requests',
  template_name='Feature Requests Template',
  categories=[
    CategoryDefinition(
      name='Feature Category',
      description='Type of feature being requested',
      value_type=CategoryValueType.PREDEFINED,
      possible_values=[
        'UI/UX',
        'Performance',
        'Integration',
        'Analytics',
        'Security',
        'Compliance',
      ],
    ),
    CategoryDefinition(
      name='Priority Level',
      description="Customer's stated priority for the feature",
      value_type=CategoryValueType.PREDEFINED,
      possible_values=['Critical', 'High', 'Medium', 'Low', 'Nice to Have'],
    ),
    CategoryDefinition(
      name='Business Impact',
      description="How the feature would impact the customer's business",
      value_type=CategoryValueType.INFERRED,
    ),
    CategoryDefinition(
      name='Timeline',
      description='When the customer needs this feature',
      value_type=CategoryValueType.INFERRED,
    ),
  ],
  is_default=True,
  created_at=datetime.now(),
)

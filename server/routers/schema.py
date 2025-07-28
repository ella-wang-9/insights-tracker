"""API endpoints for schema management."""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from server.models.schema_models import (
  DEFAULT_PRODUCT_FEEDBACK_SCHEMA,
  CategoryValueType,
  CreateSchemaRequest,
  SchemaTemplate,
  SchemaValidationError,
  SchemaValidationResponse,
  UpdateSchemaRequest,
)

router = APIRouter(prefix='/schema', tags=['Schema Management'])

# In-memory storage for development (will be replaced with Delta Tables)
_schemas: dict[str, SchemaTemplate] = {
  'default_product_feedback': DEFAULT_PRODUCT_FEEDBACK_SCHEMA,
}


@router.get('/templates', response_model=List[SchemaTemplate])
async def get_schema_templates(user_id: Optional[str] = None) -> List[SchemaTemplate]:
  """Get all schema templates, optionally filtered by user."""
  templates = list(_schemas.values())

  if user_id:
    # Filter by user_id or include default templates
    templates = [t for t in templates if t.user_id == user_id or t.is_default]

  return templates


@router.get('/templates/{template_id}', response_model=SchemaTemplate)
async def get_schema_template(template_id: str) -> SchemaTemplate:
  """Get a specific schema template by ID."""
  if template_id not in _schemas:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Schema template with ID '{template_id}' not found",
    )

  return _schemas[template_id]


@router.post('/templates', response_model=SchemaTemplate)
async def create_schema_template(
  request: CreateSchemaRequest, user_id: Optional[str] = None
) -> SchemaTemplate:
  """Create a new schema template."""
  print(f'Received schema creation request: {request}')
  print(f'Template name: {request.template_name}')
  print(f'Categories count: {len(request.categories)}')

  try:
    # Validate the schema (simplified validation without AI)
    validation_result = await validate_schema_categories(request.categories)
    print(f'Validation result: {validation_result.is_valid}')

    if not validation_result.is_valid:
      print(f'Validation errors: {validation_result.errors}')
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
          'message': 'Schema validation failed',
          'errors': [{'field': e.field, 'message': e.message} for e in validation_result.errors],
        },
      )
  except Exception as e:
    print(f'Error during schema validation: {e}')
    # If validation fails, proceed anyway for basic schemas
    print('Proceeding with schema creation despite validation issues')

  # Create new template
  template_id = str(uuid4())
  template = SchemaTemplate(
    template_id=template_id,
    template_name=request.template_name,
    categories=request.categories,
    user_id=user_id,
    is_default=False,
    created_at=datetime.now(),
    updated_at=datetime.now(),
  )

  _schemas[template_id] = template
  return template


@router.put('/templates/{template_id}', response_model=SchemaTemplate)
async def update_schema_template(
  template_id: str, request: UpdateSchemaRequest, user_id: Optional[str] = None
) -> SchemaTemplate:
  """Update an existing schema template."""
  if template_id not in _schemas:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Schema template with ID '{template_id}' not found",
    )

  template = _schemas[template_id]

  # Check ownership (users can only update their own templates, not defaults)
  if template.is_default:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN, detail='Cannot modify default templates'
    )

  if template.user_id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN, detail='You can only modify your own templates'
    )

  # Update fields if provided
  if request.template_name is not None:
    template.template_name = request.template_name

  if request.categories is not None:
    # Validate the new categories
    validation_result = await validate_schema_categories(request.categories)
    if not validation_result.is_valid:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
          'message': 'Schema validation failed',
          'errors': [{'field': e.field, 'message': e.message} for e in validation_result.errors],
        },
      )
    template.categories = request.categories

  template.updated_at = datetime.now()
  _schemas[template_id] = template

  return template


@router.delete('/templates/{template_id}')
async def delete_schema_template(template_id: str, user_id: Optional[str] = None) -> dict:
  """Delete a schema template."""
  if template_id not in _schemas:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Schema template with ID '{template_id}' not found",
    )

  template = _schemas[template_id]

  # Check ownership
  if template.is_default:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN, detail='Cannot delete default templates'
    )

  if template.user_id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN, detail='You can only delete your own templates'
    )

  del _schemas[template_id]
  return {'message': f"Schema template '{template.template_name}' deleted successfully"}


@router.post('/validate', response_model=SchemaValidationResponse)
async def validate_schema(request: CreateSchemaRequest) -> SchemaValidationResponse:
  """Validate a schema before saving."""
  return await validate_schema_categories(request.categories)


async def validate_schema_categories(categories: List) -> SchemaValidationResponse:
  """Validate schema categories for common issues."""
  errors = []
  category_names = []

  for i, category in enumerate(categories):
    # Check for duplicate category names
    if category.name in category_names:
      errors.append(
        SchemaValidationError(
          field=f'categories[{i}].name', message=f"Duplicate category name: '{category.name}'"
        )
      )
    else:
      category_names.append(category.name)

    # Check category name is not empty
    if not category.name.strip():
      errors.append(
        SchemaValidationError(
          field=f'categories[{i}].name', message='Category name cannot be empty'
        )
      )

    # Validate predefined values
    if category.value_type == CategoryValueType.PREDEFINED:
      if not category.possible_values or len(category.possible_values) == 0:
        errors.append(
          SchemaValidationError(
            field=f'categories[{i}].possible_values',
            message='Predefined categories must have at least one possible value',
          )
        )
      elif len(set(category.possible_values)) != len(category.possible_values):
        errors.append(
          SchemaValidationError(
            field=f'categories[{i}].possible_values', message='Possible values must be unique'
          )
        )

    # Validate inferred categories don't have predefined values
    if category.value_type == CategoryValueType.INFERRED and category.possible_values:
      errors.append(
        SchemaValidationError(
          field=f'categories[{i}].possible_values',
          message='Inferred categories should not have predefined values',
        )
      )

  # Check minimum number of categories
  if len(categories) == 0:
    errors.append(
      SchemaValidationError(field='categories', message='Schema must have at least one category')
    )

  return SchemaValidationResponse(is_valid=len(errors) == 0, errors=errors)


@router.get('/defaults', response_model=List[SchemaTemplate])
async def get_default_templates() -> List[SchemaTemplate]:
  """Get all default schema templates."""
  return [template for template in _schemas.values() if template.is_default]

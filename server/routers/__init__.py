# Generic router module for the Databricks app template
# Add your FastAPI routes here

from fastapi import APIRouter

from .insights import router as insights_router
from .schema import router as schema_router
from .user import router as user_router
from .batch import router as batch_router

router = APIRouter()
router.include_router(user_router, prefix='/user', tags=['user'])
router.include_router(schema_router, tags=['schema'])
router.include_router(insights_router, tags=['insights'])
router.include_router(batch_router, tags=['batch'])

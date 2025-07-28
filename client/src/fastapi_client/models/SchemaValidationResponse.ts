/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { SchemaValidationError } from './SchemaValidationError';
/**
 * Response for schema validation requests.
 */
export type SchemaValidationResponse = {
    /**
     * Whether the schema is valid
     */
    is_valid: boolean;
    /**
     * Validation errors if any
     */
    errors?: Array<SchemaValidationError>;
};


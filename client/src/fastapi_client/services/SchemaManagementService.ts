/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CreateSchemaRequest } from '../models/CreateSchemaRequest';
import type { SchemaTemplate } from '../models/SchemaTemplate';
import type { SchemaValidationResponse } from '../models/SchemaValidationResponse';
import type { UpdateSchemaRequest } from '../models/UpdateSchemaRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class SchemaManagementService {
    /**
     * Get Schema Templates
     * Get all schema templates, optionally filtered by user.
     * @param userId
     * @returns SchemaTemplate Successful Response
     * @throws ApiError
     */
    public static getSchemaTemplatesApiSchemaTemplatesGet(
        userId?: (string | null),
    ): CancelablePromise<Array<SchemaTemplate>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/schema/templates',
            query: {
                'user_id': userId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Schema Template
     * Create a new schema template.
     * @param requestBody
     * @param userId
     * @returns SchemaTemplate Successful Response
     * @throws ApiError
     */
    public static createSchemaTemplateApiSchemaTemplatesPost(
        requestBody: CreateSchemaRequest,
        userId?: (string | null),
    ): CancelablePromise<SchemaTemplate> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/schema/templates',
            query: {
                'user_id': userId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Schema Template
     * Get a specific schema template by ID.
     * @param templateId
     * @returns SchemaTemplate Successful Response
     * @throws ApiError
     */
    public static getSchemaTemplateApiSchemaTemplatesTemplateIdGet(
        templateId: string,
    ): CancelablePromise<SchemaTemplate> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/schema/templates/{template_id}',
            path: {
                'template_id': templateId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Schema Template
     * Update an existing schema template.
     * @param templateId
     * @param requestBody
     * @param userId
     * @returns SchemaTemplate Successful Response
     * @throws ApiError
     */
    public static updateSchemaTemplateApiSchemaTemplatesTemplateIdPut(
        templateId: string,
        requestBody: UpdateSchemaRequest,
        userId?: (string | null),
    ): CancelablePromise<SchemaTemplate> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/schema/templates/{template_id}',
            path: {
                'template_id': templateId,
            },
            query: {
                'user_id': userId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Schema Template
     * Delete a schema template.
     * @param templateId
     * @param userId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteSchemaTemplateApiSchemaTemplatesTemplateIdDelete(
        templateId: string,
        userId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/schema/templates/{template_id}',
            path: {
                'template_id': templateId,
            },
            query: {
                'user_id': userId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Validate Schema
     * Validate a schema before saving.
     * @param requestBody
     * @returns SchemaValidationResponse Successful Response
     * @throws ApiError
     */
    public static validateSchemaApiSchemaValidatePost(
        requestBody: CreateSchemaRequest,
    ): CancelablePromise<SchemaValidationResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/schema/validate',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Default Templates
     * Get all default schema templates.
     * @returns SchemaTemplate Successful Response
     * @throws ApiError
     */
    public static getDefaultTemplatesApiSchemaDefaultsGet(): CancelablePromise<Array<SchemaTemplate>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/schema/defaults',
        });
    }
}

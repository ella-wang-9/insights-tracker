/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AnalysisSession } from '../models/AnalysisSession';
import type { BatchAnalysisRequest } from '../models/BatchAnalysisRequest';
import type { Body_analyze_document_api_insights_analyze_document_post } from '../models/Body_analyze_document_api_insights_analyze_document_post';
import type { Body_batch_analyze_all_with_preview_api_batch_analyze_all_with_preview_post } from '../models/Body_batch_analyze_all_with_preview_api_batch_analyze_all_with_preview_post';
import type { Body_batch_analyze_api_insights_batch_analyze_post } from '../models/Body_batch_analyze_api_insights_batch_analyze_post';
import type { Body_batch_analyze_files_api_batch_analyze_files_post } from '../models/Body_batch_analyze_files_api_batch_analyze_files_post';
import type { Body_batch_analyze_files_with_preview_api_batch_analyze_files_with_preview_post } from '../models/Body_batch_analyze_files_with_preview_api_batch_analyze_files_with_preview_post';
import type { Body_batch_analyze_mixed_api_batch_analyze_mixed_post } from '../models/Body_batch_analyze_mixed_api_batch_analyze_mixed_post';
import type { Body_batch_analyze_with_preview_api_batch_analyze_with_preview_post } from '../models/Body_batch_analyze_with_preview_api_batch_analyze_with_preview_post';
import type { CreateSchemaRequest } from '../models/CreateSchemaRequest';
import type { ProcessingRequest } from '../models/ProcessingRequest';
import type { QuickAnalysisResult } from '../models/QuickAnalysisResult';
import type { SchemaTemplate } from '../models/SchemaTemplate';
import type { SchemaValidationResponse } from '../models/SchemaValidationResponse';
import type { TextAnalysisRequest } from '../models/TextAnalysisRequest';
import type { UpdateSchemaRequest } from '../models/UpdateSchemaRequest';
import type { UserInfo } from '../models/UserInfo';
import type { UserWorkspaceInfo } from '../models/UserWorkspaceInfo';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ApiService {
    /**
     * Get Current User
     * Get current user information from Databricks.
     * @returns UserInfo Successful Response
     * @throws ApiError
     */
    public static getCurrentUserApiUserMeGet(): CancelablePromise<UserInfo> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/user/me',
        });
    }
    /**
     * Get User Workspace Info
     * Get user information along with workspace details.
     * @returns UserWorkspaceInfo Successful Response
     * @throws ApiError
     */
    public static getUserWorkspaceInfoApiUserMeWorkspaceGet(): CancelablePromise<UserWorkspaceInfo> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/user/me/workspace',
        });
    }
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
    /**
     * Analyze Text
     * Quickly analyze text content with a given schema.
     * @param requestBody
     * @returns QuickAnalysisResult Successful Response
     * @throws ApiError
     */
    public static analyzeTextApiInsightsAnalyzeTextPost(
        requestBody: TextAnalysisRequest,
    ): CancelablePromise<QuickAnalysisResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/insights/analyze-text',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Analyze Document
     * Analyze a document from various sources (text, file upload, or Google Drive).
     * @param formData
     * @returns QuickAnalysisResult Successful Response
     * @throws ApiError
     */
    public static analyzeDocumentApiInsightsAnalyzeDocumentPost(
        formData: Body_analyze_document_api_insights_analyze_document_post,
    ): CancelablePromise<QuickAnalysisResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/insights/analyze-document',
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Analysis Session
     * Create a new analysis session for batch processing.
     * @param requestBody
     * @returns AnalysisSession Successful Response
     * @throws ApiError
     */
    public static createAnalysisSessionApiInsightsSessionsPost(
        requestBody: ProcessingRequest,
    ): CancelablePromise<AnalysisSession> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/insights/sessions',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Analysis Sessions
     * List all analysis sessions, optionally filtered by user.
     * @param userId
     * @returns AnalysisSession Successful Response
     * @throws ApiError
     */
    public static listAnalysisSessionsApiInsightsSessionsGet(
        userId?: (string | null),
    ): CancelablePromise<Array<AnalysisSession>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/insights/sessions',
            query: {
                'user_id': userId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Analysis Session
     * Get details of a specific analysis session.
     * @param sessionId
     * @returns AnalysisSession Successful Response
     * @throws ApiError
     */
    public static getAnalysisSessionApiInsightsSessionsSessionIdGet(
        sessionId: string,
    ): CancelablePromise<AnalysisSession> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/insights/sessions/{session_id}',
            path: {
                'session_id': sessionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Analysis Session
     * Delete an analysis session.
     * @param sessionId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteAnalysisSessionApiInsightsSessionsSessionIdDelete(
        sessionId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/insights/sessions/{session_id}',
            path: {
                'session_id': sessionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Start Analysis Session
     * Start processing documents in an analysis session.
     * @param sessionId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static startAnalysisSessionApiInsightsSessionsSessionIdStartPost(
        sessionId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/insights/sessions/{session_id}/start',
            path: {
                'session_id': sessionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Test Ai Connection
     * Test the AI engine connection and capabilities.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static testAiConnectionApiInsightsTestAiGet(): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/insights/test-ai',
        });
    }
    /**
     * Batch Analyze
     * Analyze multiple inputs (text, files, URLs) and export results as spreadsheet.
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static batchAnalyzeApiInsightsBatchAnalyzePost(
        formData: Body_batch_analyze_api_insights_batch_analyze_post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/insights/batch-analyze',
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Batch Analyze Download
     * Analyze multiple inputs and return spreadsheet file for download.
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static batchAnalyzeDownloadApiInsightsBatchAnalyzeDownloadPost(
        requestBody: BatchAnalysisRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/insights/batch-analyze/download',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Batch Analyze Files
     * Analyze multiple files and export results as spreadsheet.
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static batchAnalyzeFilesApiBatchAnalyzeFilesPost(
        formData: Body_batch_analyze_files_api_batch_analyze_files_post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/batch/analyze-files',
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Batch Analyze Mixed
     * Analyze multiple texts and URLs, export results as spreadsheet.
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static batchAnalyzeMixedApiBatchAnalyzeMixedPost(
        formData: Body_batch_analyze_mixed_api_batch_analyze_mixed_post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/batch/analyze-mixed',
            formData: formData,
            mediaType: 'application/x-www-form-urlencoded',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Batch Analyze Files With Preview
     * Analyze multiple files and return both preview data and download link.
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static batchAnalyzeFilesWithPreviewApiBatchAnalyzeFilesWithPreviewPost(
        formData: Body_batch_analyze_files_with_preview_api_batch_analyze_files_with_preview_post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/batch/analyze-files-with-preview',
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Batch Analyze With Preview
     * Analyze multiple documents and return both preview data and download link.
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static batchAnalyzeWithPreviewApiBatchAnalyzeWithPreviewPost(
        formData: Body_batch_analyze_with_preview_api_batch_analyze_with_preview_post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/batch/analyze-with-preview',
            formData: formData,
            mediaType: 'application/x-www-form-urlencoded',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Batch Analyze All With Preview
     * Analyze all types of inputs (files, texts, URLs) and return both preview data and download link.
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static batchAnalyzeAllWithPreviewApiBatchAnalyzeAllWithPreviewPost(
        formData: Body_batch_analyze_all_with_preview_api_batch_analyze_all_with_preview_post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/batch/analyze-all-with-preview',
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}

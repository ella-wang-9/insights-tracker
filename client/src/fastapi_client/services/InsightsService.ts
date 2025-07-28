/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AnalysisSession } from '../models/AnalysisSession';
import type { BatchAnalysisRequest } from '../models/BatchAnalysisRequest';
import type { Body_analyze_document_api_insights_analyze_document_post } from '../models/Body_analyze_document_api_insights_analyze_document_post';
import type { Body_batch_analyze_api_insights_batch_analyze_post } from '../models/Body_batch_analyze_api_insights_batch_analyze_post';
import type { ProcessingRequest } from '../models/ProcessingRequest';
import type { QuickAnalysisResult } from '../models/QuickAnalysisResult';
import type { TextAnalysisRequest } from '../models/TextAnalysisRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class InsightsService {
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
}

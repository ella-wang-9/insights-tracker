/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_batch_analyze_all_with_preview_api_batch_analyze_all_with_preview_post } from '../models/Body_batch_analyze_all_with_preview_api_batch_analyze_all_with_preview_post';
import type { Body_batch_analyze_files_api_batch_analyze_files_post } from '../models/Body_batch_analyze_files_api_batch_analyze_files_post';
import type { Body_batch_analyze_files_with_preview_api_batch_analyze_files_with_preview_post } from '../models/Body_batch_analyze_files_with_preview_api_batch_analyze_files_with_preview_post';
import type { Body_batch_analyze_mixed_api_batch_analyze_mixed_post } from '../models/Body_batch_analyze_mixed_api_batch_analyze_mixed_post';
import type { Body_batch_analyze_with_preview_api_batch_analyze_with_preview_post } from '../models/Body_batch_analyze_with_preview_api_batch_analyze_with_preview_post';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class BatchService {
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

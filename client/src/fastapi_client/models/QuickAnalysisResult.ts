/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CategoryResult } from './CategoryResult';
/**
 * Quick analysis result for immediate feedback.
 */
export type QuickAnalysisResult = {
    /**
     * Extracted customer name
     */
    customer_name?: (string | null);
    /**
     * Extracted meeting date as string
     */
    meeting_date?: (string | null);
    /**
     * Category analysis results
     */
    categories: Record<string, CategoryResult>;
    /**
     * Time taken to process
     */
    processing_time_ms: number;
    /**
     * Number of words in the input text
     */
    word_count: number;
};


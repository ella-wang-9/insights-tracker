/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CategoryResult } from './CategoryResult';
import type { DocumentInput } from './DocumentInput';
import type { ExtractedEntity } from './ExtractedEntity';
/**
 * Result of analyzing a single document.
 */
export type DocumentAnalysisResult = {
    /**
     * Unique identifier for the document
     */
    document_id: string;
    /**
     * Analysis session ID
     */
    session_id: string;
    /**
     * Extracted customer/company name
     */
    customer_name?: (string | null);
    /**
     * Extracted meeting date
     */
    meeting_date?: (string | null);
    /**
     * Results for each category
     */
    extracted_categories: Record<string, CategoryResult>;
    /**
     * All extracted entities
     */
    extracted_entities?: Array<ExtractedEntity>;
    /**
     * Processing time in milliseconds
     */
    processing_time_ms: number;
    /**
     * When processing completed
     */
    processed_at?: string;
    /**
     * Original document information
     */
    source_info: DocumentInput;
};


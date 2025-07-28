/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Result for a single category classification.
 */
export type CategoryResult = {
    /**
     * Name of the category
     */
    category_name: string;
    /**
     * Extracted values for this category
     */
    values: Array<string>;
    /**
     * Overall confidence score for this category
     */
    confidence: number;
    /**
     * Text passages that support this classification
     */
    evidence_text?: Array<string>;
    /**
     * AI model used for this classification
     */
    model_used: string;
    /**
     * Error message if processing failed
     */
    error?: (string | null);
};


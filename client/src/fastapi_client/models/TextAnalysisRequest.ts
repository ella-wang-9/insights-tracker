/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Simple request for analyzing text content.
 */
export type TextAnalysisRequest = {
    /**
     * Text content to analyze
     */
    text: string;
    /**
     * Schema template to use for analysis
     */
    schema_template_id: string;
    /**
     * Whether to extract customer name and meeting date
     */
    extract_customer_info?: boolean;
};


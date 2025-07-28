/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BatchInput } from './BatchInput';
/**
 * Request for batch analysis of multiple inputs.
 */
export type BatchAnalysisRequest = {
    /**
     * Schema template to use for analysis
     */
    schema_template_id: string;
    /**
     * List of inputs to process
     */
    inputs: Array<BatchInput>;
    /**
     * Whether to extract customer name and meeting date
     */
    extract_customer_info?: boolean;
    /**
     * Export format (csv, xlsx)
     */
    export_format?: string;
};


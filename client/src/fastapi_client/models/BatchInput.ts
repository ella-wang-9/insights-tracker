/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BatchInputType } from './BatchInputType';
/**
 * Single input item for batch processing.
 */
export type BatchInput = {
    input_type: BatchInputType;
    /**
     * Text content, file path, or URL
     */
    content: string;
    /**
     * Original filename if applicable
     */
    filename?: (string | null);
};


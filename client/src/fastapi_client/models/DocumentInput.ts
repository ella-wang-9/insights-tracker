/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DocumentSource } from './DocumentSource';
/**
 * Input document for processing.
 */
export type DocumentInput = {
    /**
     * Unique identifier for the document
     */
    document_id?: (string | null);
    /**
     * How the document was provided
     */
    source_type: DocumentSource;
    /**
     * Text content of the document
     */
    content: string;
    /**
     * URL if from Google Docs
     */
    source_url?: (string | null);
    /**
     * Original filename if uploaded
     */
    filename?: (string | null);
    /**
     * Additional metadata
     */
    metadata?: (Record<string, any> | null);
};


/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DocumentInput } from './DocumentInput';
/**
 * Request to process documents with a schema.
 */
export type ProcessingRequest = {
    /**
     * Name for this analysis session
     */
    session_name?: (string | null);
    /**
     * ID of the schema template to use
     */
    schema_template_id: string;
    /**
     * Documents to process
     */
    documents: Array<DocumentInput>;
    /**
     * User ID for the session
     */
    user_id?: (string | null);
};


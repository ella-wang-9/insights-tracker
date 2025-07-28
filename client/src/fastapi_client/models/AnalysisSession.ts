/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DocumentAnalysisResult } from './DocumentAnalysisResult';
/**
 * An analysis session containing multiple documents.
 */
export type AnalysisSession = {
    /**
     * Unique session identifier
     */
    session_id: string;
    /**
     * Human-readable session name
     */
    session_name?: (string | null);
    /**
     * User who created this session
     */
    user_id?: (string | null);
    /**
     * Schema template used for analysis
     */
    schema_template_id: string;
    /**
     * Session status: running, completed, failed
     */
    status?: string;
    /**
     * Total number of documents in session
     */
    total_documents?: number;
    /**
     * Number of documents processed so far
     */
    processed_documents?: number;
    /**
     * When session was created
     */
    created_at?: string;
    /**
     * When session completed
     */
    completed_at?: (string | null);
    /**
     * Analysis results
     */
    results?: Array<DocumentAnalysisResult>;
};


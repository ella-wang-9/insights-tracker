/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * An entity extracted from the document.
 */
export type ExtractedEntity = {
    /**
     * The extracted text
     */
    entity_text: string;
    /**
     * Type of entity (e.g., 'PERSON', 'ORG', 'DATE')
     */
    entity_type: string;
    /**
     * Confidence score from 0 to 1
     */
    confidence: number;
    /**
     * Start position in text
     */
    start_pos?: (number | null);
    /**
     * End position in text
     */
    end_pos?: (number | null);
};


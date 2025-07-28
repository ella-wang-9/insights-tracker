/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CategoryDefinition } from './CategoryDefinition';
/**
 * A schema template for categorizing customer insights.
 */
export type SchemaTemplate = {
    /**
     * Unique identifier for the template
     */
    template_id?: (string | null);
    /**
     * Human-readable name for the template
     */
    template_name: string;
    /**
     * List of categories in this schema
     */
    categories: Array<CategoryDefinition>;
    /**
     * User who created this template
     */
    user_id?: (string | null);
    /**
     * Whether this is a default template
     */
    is_default?: boolean;
    /**
     * When the template was created
     */
    created_at?: (string | null);
    /**
     * When the template was last updated
     */
    updated_at?: (string | null);
};


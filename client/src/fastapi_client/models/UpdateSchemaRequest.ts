/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CategoryDefinition } from './CategoryDefinition';
/**
 * Request to update an existing schema template.
 */
export type UpdateSchemaRequest = {
    /**
     * New name for the template
     */
    template_name?: (string | null);
    /**
     * Updated categories
     */
    categories?: (Array<CategoryDefinition> | null);
};


/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CategoryDefinition } from './CategoryDefinition';
/**
 * Request to create a new schema template.
 */
export type CreateSchemaRequest = {
    /**
     * Name for the new template
     */
    template_name: string;
    /**
     * Categories to include in the schema
     */
    categories: Array<CategoryDefinition>;
};


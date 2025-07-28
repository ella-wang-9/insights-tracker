/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CategoryValueType } from './CategoryValueType';
/**
 * Definition of a single category in a schema.
 */
export type CategoryDefinition = {
    /**
     * Name of the category (e.g., 'Product', 'Industry')
     */
    name: string;
    /**
     * Optional description to guide AI inference
     */
    description?: (string | null);
    /**
     * Whether values are predefined or AI-inferred
     */
    value_type: CategoryValueType;
    /**
     * Predefined values (only for predefined type)
     */
    possible_values?: (Array<string> | null);
};


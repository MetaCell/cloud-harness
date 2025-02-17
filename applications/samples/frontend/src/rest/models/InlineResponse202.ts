/* tslint:disable */
/* eslint-disable */
/**
 * CloudHarness Sample API
 * CloudHarness Sample api
 *
 * The version of the OpenAPI document: 0.1.0
 * Contact: cloudharness@metacell.us
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import { mapValues } from '../runtime';
import type { InlineResponse202Task } from './InlineResponse202Task';
import {
    InlineResponse202TaskFromJSON,
    InlineResponse202TaskFromJSONTyped,
    InlineResponse202TaskToJSON,
} from './InlineResponse202Task';

/**
 * 
 * @export
 * @interface InlineResponse202
 */
export interface InlineResponse202 {
    /**
     * 
     * @type {InlineResponse202Task}
     * @memberof InlineResponse202
     */
    task?: InlineResponse202Task;
}

/**
 * Check if a given object implements the InlineResponse202 interface.
 */
export function instanceOfInlineResponse202(value: object): value is InlineResponse202 {
    return true;
}

export function InlineResponse202FromJSON(json: any): InlineResponse202 {
    return InlineResponse202FromJSONTyped(json, false);
}

export function InlineResponse202FromJSONTyped(json: any, ignoreDiscriminator: boolean): InlineResponse202 {
    if (json == null) {
        return json;
    }
    return {
        
        'task': json['task'] == null ? undefined : InlineResponse202TaskFromJSON(json['task']),
    };
}

export function InlineResponse202ToJSON(value?: InlineResponse202 | null): any {
    if (value == null) {
        return value;
    }
    return {
        
        'task': InlineResponse202TaskToJSON(value['task']),
    };
}


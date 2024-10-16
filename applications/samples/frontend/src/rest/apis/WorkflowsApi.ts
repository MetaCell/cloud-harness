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


import * as runtime from '../runtime';
import type {
  InlineResponse202,
} from '../models/index';
import {
    InlineResponse202FromJSON,
    InlineResponse202ToJSON,
} from '../models/index';

export interface SubmitSyncWithResultsRequest {
    a: number;
    b: number;
}

/**
 * 
 */
export class WorkflowsApi extends runtime.BaseAPI {

    /**
     * Send an asynchronous operation
     */
    async submitAsyncRaw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<InlineResponse202>> {
        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        const response = await this.request({
            path: `/operation_async`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => InlineResponse202FromJSON(jsonValue));
    }

    /**
     * Send an asynchronous operation
     */
    async submitAsync(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<InlineResponse202> {
        const response = await this.submitAsyncRaw(initOverrides);
        return await response.value();
    }

    /**
     * Send a synchronous operation
     * @deprecated
     */
    async submitSyncRaw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<object>> {
        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        const response = await this.request({
            path: `/operation_sync`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse<any>(response);
    }

    /**
     * Send a synchronous operation
     * @deprecated
     */
    async submitSync(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<object> {
        const response = await this.submitSyncRaw(initOverrides);
        return await response.value();
    }

    /**
     * Send a synchronous operation and get results using the event queue. Just a sum, but in the cloud
     * @deprecated
     */
    async submitSyncWithResultsRaw(requestParameters: SubmitSyncWithResultsRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<string>> {
        if (requestParameters['a'] == null) {
            throw new runtime.RequiredError(
                'a',
                'Required parameter "a" was null or undefined when calling submitSyncWithResults().'
            );
        }

        if (requestParameters['b'] == null) {
            throw new runtime.RequiredError(
                'b',
                'Required parameter "b" was null or undefined when calling submitSyncWithResults().'
            );
        }

        const queryParameters: any = {};

        if (requestParameters['a'] != null) {
            queryParameters['a'] = requestParameters['a'];
        }

        if (requestParameters['b'] != null) {
            queryParameters['b'] = requestParameters['b'];
        }

        const headerParameters: runtime.HTTPHeaders = {};

        const response = await this.request({
            path: `/operation_sync_results`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        if (this.isJsonMime(response.headers.get('content-type'))) {
            return new runtime.JSONApiResponse<string>(response);
        } else {
            return new runtime.TextApiResponse(response) as any;
        }
    }

    /**
     * Send a synchronous operation and get results using the event queue. Just a sum, but in the cloud
     * @deprecated
     */
    async submitSyncWithResults(requestParameters: SubmitSyncWithResultsRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<string> {
        const response = await this.submitSyncWithResultsRaw(requestParameters, initOverrides);
        return await response.value();
    }

}

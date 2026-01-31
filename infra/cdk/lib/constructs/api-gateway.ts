import * as cdk from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export interface ApiGatewayProps {
  /**
   * Lambda function to integrate with API Gateway
   */
  lambdaFunction: lambda.Function;

  /**
   * API name
   */
  apiName?: string;

  /**
   * API description
   */
  apiDescription?: string;

  /**
   * Stage name (default: dev)
   */
  stageName?: string;

  /**
   * Throttling rate limit (requests per second)
   */
  throttlingRateLimit?: number;

  /**
   * Throttling burst limit
   */
  throttlingBurstLimit?: number;
}

export class ApiGateway extends Construct {
  public readonly api: apigateway.LambdaRestApi;

  constructor(scope: Construct, id: string, props: ApiGatewayProps) {
    super(scope, id);

    const apiName = props.apiName ?? 'AI Semantic Search API';
    const apiDescription = props.apiDescription ?? 'Serverless semantic search API with RAG';
    const stageName = props.stageName ?? 'dev';
    const throttlingRateLimit = props.throttlingRateLimit ?? 100;
    const throttlingBurstLimit = props.throttlingBurstLimit ?? 200;

    // API Gateway REST API
    this.api = new apigateway.LambdaRestApi(this, 'RestApi', {
      restApiName: apiName,
      description: apiDescription,
      handler: props.lambdaFunction,
      proxy: true, // Forward all requests to Lambda
      deployOptions: {
        stageName: stageName,
        throttlingRateLimit: throttlingRateLimit, // Requests per second
        throttlingBurstLimit: throttlingBurstLimit, // Burst capacity
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: true,
        metricsEnabled: true,
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'Authorization', 'X-Api-Key'],
      },
      cloudWatchRole: true,
    });

    // Output
    new cdk.CfnOutput(this, 'ApiEndpoint', {
      value: this.api.url,
      description: 'API Gateway endpoint URL',
      exportName: 'SearchApiEndpoint',
    });

    new cdk.CfnOutput(this, 'ApiId', {
      value: this.api.restApiId,
      description: 'API Gateway REST API ID',
      exportName: 'SearchApiId',
    });
  }
}

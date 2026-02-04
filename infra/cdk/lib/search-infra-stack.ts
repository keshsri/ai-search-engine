import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';

import { DynamoDBTables } from './constructs/dynamodb-tables';
import { StorageBucket } from './constructs/storage-bucket';
import { SearchLambda } from './constructs/search-lambda';
import { ApiGateway } from './constructs/api-gateway';
import { Monitoring } from './constructs/monitoring';

export class SearchInfraStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const dynamoTables = new DynamoDBTables(this, 'DynamoDBTables', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const storageBucket = new StorageBucket(this, 'StorageBucket', {
      accountId: this.account,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      expirationDays: 15,
    });

    const searchLambda = new SearchLambda(this, 'SearchLambda', {
      documentsTable: dynamoTables.documentsTable,
      chunksTable: dynamoTables.chunksTable,
      conversationsTable: dynamoTables.conversationsTable,
      documentsBucket: storageBucket.bucket,
      memorySize: 3008,
      timeout: 300,
    });

    new ApiGateway(this, 'ApiGateway', {
      lambdaFunction: searchLambda.function,
      apiName: 'OmniSearch AI API',
      apiDescription: 'Intelligent search API combining documents and web search',
      stageName: 'dev',
      throttlingRateLimit: 10,
      throttlingBurstLimit: 20,
    });

    new Monitoring(this, 'Monitoring', {
      lambdaFunction: searchLambda.function,
      dynamoTable: dynamoTables.documentsTable,
      lambdaInvocationThreshold: 30000,
      dynamoReadThreshold: 6000000,
    });

    new cdk.CfnOutput(this, 'StackName', {
      value: this.stackName,
      description: 'CloudFormation stack name',
    });

    new cdk.CfnOutput(this, 'Region', {
      value: this.region,
      description: 'AWS region',
    });

    new cdk.CfnOutput(this, 'AccountId', {
      value: this.account,
      description: 'AWS account ID',
    });
  }
}

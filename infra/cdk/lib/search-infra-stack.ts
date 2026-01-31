import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';

// Import custom constructs
import { DynamoDBTables } from './constructs/dynamodb-tables';
import { StorageBucket } from './constructs/storage-bucket';
import { SearchLambda } from './constructs/search-lambda';
import { ApiGateway } from './constructs/api-gateway';
import { Monitoring } from './constructs/monitoring';

export class SearchInfraStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ========================================
    // DynamoDB Tables
    // ========================================
    const dynamoTables = new DynamoDBTables(this, 'DynamoDBTables', {
      removalPolicy: cdk.RemovalPolicy.DESTROY, // Safe for personal project
    });

    // ========================================
    // S3 Storage Bucket
    // ========================================
    const storageBucket = new StorageBucket(this, 'StorageBucket', {
      accountId: this.account,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // Safe for personal project
      expirationDays: 90, // Auto-delete files after 90 days
    });

    // ========================================
    // Lambda Function
    // ========================================
    const searchLambda = new SearchLambda(this, 'SearchLambda', {
      documentsTable: dynamoTables.documentsTable,
      chunksTable: dynamoTables.chunksTable,
      conversationsTable: dynamoTables.conversationsTable,
      documentsBucket: storageBucket.bucket,
      memorySize: 3008, // 3 GB for embedding model
      timeout: 300, // 5 minutes
    });

    // ========================================
    // API Gateway
    // ========================================
    const apiGateway = new ApiGateway(this, 'ApiGateway', {
      lambdaFunction: searchLambda.function,
      apiName: 'AI Semantic Search API',
      apiDescription: 'Serverless semantic search API with RAG',
      stageName: 'dev',
      throttlingRateLimit: 100, // 100 requests/second
      throttlingBurstLimit: 200, // 200 burst capacity
    });

    // ========================================
    // CloudWatch Monitoring & Alarms
    // ========================================
    const monitoring = new Monitoring(this, 'Monitoring', {
      lambdaFunction: searchLambda.function,
      dynamoTable: dynamoTables.documentsTable,
      lambdaInvocationThreshold: 30000, // Alert at 30K invocations/day
      dynamoReadThreshold: 6000000, // Alert at 6M reads/day
    });

    // ========================================
    // Stack-level Outputs
    // ========================================
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

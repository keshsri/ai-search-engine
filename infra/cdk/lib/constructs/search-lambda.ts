import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import * as path from 'path';

export interface SearchLambdaProps {
  documentsTable: dynamodb.Table;
  chunksTable: dynamodb.Table;
  conversationsTable: dynamodb.Table;
  documentsBucket: s3.Bucket;
  memorySize?: number;
  timeout?: number;
  logRetention?: logs.RetentionDays;
}

export class SearchLambda extends Construct {
  public readonly function: lambda.DockerImageFunction;

  constructor(scope: Construct, id: string, props: SearchLambdaProps) {
    super(scope, id);

    const memorySize = props.memorySize ?? 3008;
    const timeout = props.timeout ?? 300;
    const logRetention = props.logRetention ?? logs.RetentionDays.THREE_DAYS;

    this.function = new lambda.DockerImageFunction(this, 'Function', {
      functionName: 'ai-search-api',
      code: lambda.DockerImageCode.fromImageAsset(
        path.join(__dirname, '../../../../services/search_api'),
        {
          file: 'Dockerfile.lambda',
        }
      ),
      memorySize: memorySize,
      timeout: cdk.Duration.seconds(timeout),
      ephemeralStorageSize: cdk.Size.mebibytes(512),
      environment: {
        DYNAMODB_DOCUMENT_TABLE: props.documentsTable.tableName,
        CHUNKS_TABLE_NAME: props.chunksTable.tableName,
        CONVERSATIONS_TABLE_NAME: props.conversationsTable.tableName,
        
        DOCUMENTS_BUCKET: props.documentsBucket.bucketName,
        FAISS_INDEX_S3_KEY: 'faiss/index.faiss',
        FAISS_METADATA_S3_KEY: 'faiss/metadata.json',
        
        CHUNK_SIZE: '300',
        LOG_LEVEL: 'INFO',
        APP_NAME: 'AI Semantic Search API',
        
        API_GATEWAY_STAGE: 'dev',
        
        BEDROCK_MODEL_ID: 'amazon.nova-micro-v1:0',
      },
      logGroup: new logs.LogGroup(this, 'LogGroup', {
        logGroupName: `/aws/lambda/ai-search-api`,
        retention: logRetention,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    });

    props.documentsTable.grantReadWriteData(this.function);
    props.chunksTable.grantReadWriteData(this.function);
    props.conversationsTable.grantReadWriteData(this.function);
    props.documentsBucket.grantReadWrite(this.function);

    this.function.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
        'bedrock:InvokeModelWithResponseStream',
      ],
      resources: ['*'],
    }));

    new cdk.CfnOutput(this, 'FunctionName', {
      value: this.function.functionName,
      description: 'Lambda function name',
      exportName: 'SearchLambdaFunctionName',
    });

    new cdk.CfnOutput(this, 'FunctionArn', {
      value: this.function.functionArn,
      description: 'Lambda function ARN',
      exportName: 'SearchLambdaFunctionArn',
    });
  }
}

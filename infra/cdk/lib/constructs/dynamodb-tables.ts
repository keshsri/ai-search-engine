import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';

export interface DynamoDBTablesProps {
  removalPolicy?: cdk.RemovalPolicy;
}

export class DynamoDBTables extends Construct {
  public readonly documentsTable: dynamodb.Table;
  public readonly chunksTable: dynamodb.Table;
  public readonly conversationsTable: dynamodb.Table;

  constructor(scope: Construct, id: string, props?: DynamoDBTablesProps) {
    super(scope, id);

    const removalPolicy = props?.removalPolicy ?? cdk.RemovalPolicy.DESTROY;

    this.documentsTable = new dynamodb.Table(this, 'DocumentsTable', {
      tableName: 'ai-search-documents',
      partitionKey: {
        name: 'document_id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: removalPolicy,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: false,
      },
      timeToLiveAttribute: 'ttl',
    });

    this.chunksTable = new dynamodb.Table(this, 'ChunksTable', {
      tableName: 'document_chunks',
      partitionKey: {
        name: 'document_id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'chunk_id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: removalPolicy,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: false,
      },
      timeToLiveAttribute: 'ttl',
    });

    this.conversationsTable = new dynamodb.Table(this, 'ConversationsTable', {
      tableName: 'conversations',
      partitionKey: {
        name: 'conversation_id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: removalPolicy,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: false,
      },
      timeToLiveAttribute: 'ttl',
    });

    new cdk.CfnOutput(this, 'DocumentsTableName', {
      value: this.documentsTable.tableName,
      description: 'DynamoDB documents table name',
      exportName: 'DocumentsTableName',
    });

    new cdk.CfnOutput(this, 'ChunksTableName', {
      value: this.chunksTable.tableName,
      description: 'DynamoDB chunks table name',
      exportName: 'ChunksTableName',
    });

    new cdk.CfnOutput(this, 'ConversationsTableName', {
      value: this.conversationsTable.tableName,
      description: 'DynamoDB conversations table name',
      exportName: 'ConversationsTableName',
    });
  }
}

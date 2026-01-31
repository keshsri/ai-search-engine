import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';

export interface StorageBucketProps {
  /**
   * AWS account ID for unique bucket naming
   */
  accountId: string;

  /**
   * Removal policy for bucket
   */
  removalPolicy?: cdk.RemovalPolicy;

  /**
   * Number of days before auto-deleting old files
   */
  expirationDays?: number;
}

export class StorageBucket extends Construct {
  public readonly bucket: s3.Bucket;

  constructor(scope: Construct, id: string, props: StorageBucketProps) {
    super(scope, id);

    const removalPolicy = props.removalPolicy ?? cdk.RemovalPolicy.DESTROY;
    const expirationDays = props.expirationDays ?? 90;

    // S3 Bucket for document storage and FAISS index
    this.bucket = new s3.Bucket(this, 'DocumentsBucket', {
      bucketName: `ai-search-documents-${props.accountId}`,
      removalPolicy: removalPolicy,
      autoDeleteObjects: removalPolicy === cdk.RemovalPolicy.DESTROY, // Clean up on stack deletion
      versioned: false, // Disable versioning to save storage
      lifecycleRules: [
        {
          // Auto-delete old files to stay within free tier
          expiration: cdk.Duration.days(expirationDays),
        },
      ],
      cors: [
        {
          allowedMethods: [
            s3.HttpMethods.GET,
            s3.HttpMethods.PUT,
            s3.HttpMethods.POST,
          ],
          allowedOrigins: ['*'],
          allowedHeaders: ['*'],
        },
      ],
      encryption: s3.BucketEncryption.S3_MANAGED, // Free server-side encryption
    });

    // Output
    new cdk.CfnOutput(this, 'BucketName', {
      value: this.bucket.bucketName,
      description: 'S3 bucket for documents and FAISS index',
      exportName: 'DocumentsBucketName',
    });
  }
}

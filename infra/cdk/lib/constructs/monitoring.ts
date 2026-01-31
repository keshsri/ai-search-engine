import * as cdk from 'aws-cdk-lib';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';

export interface MonitoringProps {
  /**
   * Lambda function to monitor
   */
  lambdaFunction: lambda.Function;

  /**
   * DynamoDB table to monitor
   */
  dynamoTable: dynamodb.Table;

  /**
   * Lambda invocation threshold per day (default: 30,000)
   */
  lambdaInvocationThreshold?: number;

  /**
   * DynamoDB read capacity threshold per day (default: 6,000,000)
   */
  dynamoReadThreshold?: number;
}

export class Monitoring extends Construct {
  public readonly lambdaInvocationAlarm: cloudwatch.Alarm;
  public readonly dynamoReadAlarm: cloudwatch.Alarm;

  constructor(scope: Construct, id: string, props: MonitoringProps) {
    super(scope, id);

    const lambdaInvocationThreshold = props.lambdaInvocationThreshold ?? 30000;
    const dynamoReadThreshold = props.dynamoReadThreshold ?? 6000000;

    // Lambda Invocation Alarm
    // Free tier: 1M requests/month = ~33,333/day
    // Alert at 30K/day to leave buffer
    this.lambdaInvocationAlarm = new cloudwatch.Alarm(this, 'LambdaInvocationAlarm', {
      alarmName: 'ai-search-lambda-invocations',
      alarmDescription: 'Alert when Lambda invocations approach free tier limit (1M/month)',
      metric: props.lambdaFunction.metricInvocations({
        statistic: 'Sum',
        period: cdk.Duration.days(1),
      }),
      threshold: lambdaInvocationThreshold,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    // DynamoDB Read Capacity Alarm
    // Free tier: 200M requests/month = ~6.67M/day
    // Alert at 6M/day to leave buffer
    this.dynamoReadAlarm = new cloudwatch.Alarm(this, 'DynamoDBReadAlarm', {
      alarmName: 'ai-search-dynamodb-reads',
      alarmDescription: 'Alert when DynamoDB reads approach free tier limit (200M/month)',
      metric: props.dynamoTable.metricConsumedReadCapacityUnits({
        statistic: 'Sum',
        period: cdk.Duration.days(1),
      }),
      threshold: dynamoReadThreshold,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    // Lambda Error Rate Alarm
    const errorRateAlarm = new cloudwatch.Alarm(this, 'LambdaErrorRateAlarm', {
      alarmName: 'ai-search-lambda-errors',
      alarmDescription: 'Alert when Lambda error rate exceeds 5%',
      metric: props.lambdaFunction.metricErrors({
        statistic: 'Average',
        period: cdk.Duration.minutes(5),
      }),
      threshold: 0.05, // 5% error rate
      evaluationPeriods: 2,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    // Lambda Duration Alarm (cold start monitoring)
    const durationAlarm = new cloudwatch.Alarm(this, 'LambdaDurationAlarm', {
      alarmName: 'ai-search-lambda-duration',
      alarmDescription: 'Alert when Lambda duration exceeds 10 seconds (cold start issues)',
      metric: props.lambdaFunction.metricDuration({
        statistic: 'Average',
        period: cdk.Duration.minutes(5),
      }),
      threshold: 10000, // 10 seconds in milliseconds
      evaluationPeriods: 2,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    // Outputs
    new cdk.CfnOutput(this, 'LambdaInvocationAlarmName', {
      value: this.lambdaInvocationAlarm.alarmName,
      description: 'Lambda invocation alarm name',
    });

    new cdk.CfnOutput(this, 'DynamoReadAlarmName', {
      value: this.dynamoReadAlarm.alarmName,
      description: 'DynamoDB read alarm name',
    });
  }
}

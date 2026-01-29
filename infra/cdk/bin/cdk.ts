#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib/core';
import { SearchInfraStack } from '../lib/search-infra-stack';

const app = new cdk.App();

new SearchInfraStack(app, 'SearchInfraStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION
  },
});

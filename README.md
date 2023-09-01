# Azure Storage CloudFormation Resource Provider

[AWS CloudFormation registry][1] lets you manage extensions, both public and private, such as resources, modules, hooks that are available for use in your AWS account. The registry makes it easier to discover and provision extensions in your AWS CloudFormation templates in the same manner you use AWS-provided resources. 

This **proof of concept** public extension provisions the Azure storage account along with a Blob container.

NOTE: Currently this AWS CloudFormation extension is only available in **us-east-1** region.

## Prerequisites
* [AWS Account][2]
* [AWS CLI][3]
* [Azure Account][4]
* Azure Credentials - Follow **Build a Secure Foundation** step from this [AWS Workshop][5].

## Getting Started

1. Sign in to the [AWS Management Console][6] with your account and select **us-east-1** as the region.

2. Create the IAM execution role for CloudFormation to assume when invoking the extension in your account and region.
    1. Launch the AWS CloudFormation [template][7] to create the stack.
    2. Use the defaults by continue clicking Next. Click Submit on the review page.
    3. After successful creation, go to the **Outputs** tab and save the **ExecutionRoleArn** to clipboard. 

3. Activate extension.
    1. From the [CloudFormation console][8] navigation pane, under **Registry**, select **Public extensions**.
    2. Choose **Resource types** as your extension type.
    3. Choose **Third party** as your Publisher.
    4. Search by **Extension name prefix** of value **POC** (please make sure you are connected to **us-east-1**).

    ![Alt text](https://static.us-east-1.prod.workshops.aws/public/6097a5f1-6a34-4843-bdc9-da6c349c6d42/static/cfn-poc-extension.png)

    5. Select the extension, then select **Activate**.
    6. For the **Execution Role ARN**, enter the saved ARN from earlier.
    7. Select **Activate extension**.

    ![Alt text](https://static.us-east-1.prod.workshops.aws/public/6097a5f1-6a34-4843-bdc9-da6c349c6d42/static/cfn-poc-extension-activate.png)

Once the extension is successfully activated, CloudFormation displays the details page for that extension.

## Supported regions

The sample extension is currently ONLY available in **us-east-1**.

## Example

### Provision a new Azure Storage account and a Blob Container. Extension creates a new Resource Group.

```yaml
---
AWSTemplateFormatVersion: "2010-09-09"
Parameters:
  AzureSubscriptionId:
    Type: String
    Description: Subscription ID of the Azure Account.
  AzureClientId:
    Type: String
    Description: App ID CloudFormation will use to access Azure. Prerequisite - setup a dedicated application service principal to access Azure Blob Storage.
  AzureTenantId:
    Type: String
    Description: Directory ID CloudFormation will use to access Azure.
  AzureClientSecret:
    Type: String
    Description: Client credentials CloudFormation will use to authenticate to Azure and access services.
    NoEcho: true
Resources:
  AzureBlobStorage:
    Type: POC::Azure::BlobStorage
    Properties:
      AzureSubscriptionId: !Ref AzureSubscriptionId
      AzureClientId: !Ref AzureClientId
      AzureTenantId: !Ref AzureTenantId
      AzureClientSecret: !Ref AzureClientSecret
Outputs:
  AzureBlobStorageAccount:
    Value: !Ref 'AzureBlobStorage'

```

### Add Registry Resource to AWS CDK app

You can use the [CfnResource][9] construct to include a resource from the AWS CloudFormation Public Registry in your application. This construct is in the CDK's `aws-cdk-lib` module. 

Please refer to this [Sample CDK Application][10]. 

[1]: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/registry.html
[2]: https://aws.amazon.com/account/
[3]: https://aws.amazon.com/cli/
[4]: https://portal.azure.com/#home
[5]: https://catalog.us-east-1.prod.workshops.aws/workshops/361cb020-df0e-4b41-956e-8233dcd85f43/en-US/secure-foundation
[6]: https://aws.amazon.com/console/
[7]: https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=poc-azure-blobstorage-role&templateURL=https://ws-assets-prod-iad-r-iad-ed304a55c2ca1aee.s3.us-east-1.amazonaws.com/361cb020-df0e-4b41-956e-8233dcd85f43/resource-role.yaml
[8]: https://console.aws.amazon.com/cloudformation/
[9]: https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.CfnResource.html
[10]: https://github.com/aws-samples/multicloud-resources-aws-cdk
# Azure Storage CloudFormation Resource Provider

AWS CloudFormation registry[1] lets you manage extensions, both public and private, such as resources, modules, hooks that are available for use in your AWS account. The registry makes it easier to discover and provision extensions in your AWS CloudFormation templates in the same manner you use AWS-provided resources. 

This public extension provisions the Azure storage account along with a Blob container.

NOTE: Currently the AWS CloudFormation extension is only available in us-east-1 region.

## Prerequisites
* [AWS Account][2]
* [AWS CLI][3]
* [Azure Account][4]
* Azure Credentials - Follow Step 1 from [this blog][5].

## AWS Management Console

To get started:

1. Sign in to the [AWS Management Console][6] with your account and and select us-east-1 as the region.

2. Create the IAM execution role for CloudFormation to assume when invoking the extension in your account and region.
    1. Download the template [resource-role.yaml][7] and save it locally.
    2. Open the [AWS CloudFormation console][8].
    3. Choose **Create Stack** and upload the above template file.
    4. Call the stack name **poc-azure-blobstorage-role** and create the stack.
    5. After successful creation, go to the **Outputs** tab and save the **ExecutionRoleArn** to clipboard. 

3. Activate extension.
    1. Open the [AWS CloudFormation console][8].
    2. From the **CloudFormation** navigation pane, under **Registry**, select **Public extensions**.
    3. Choose **Resource types** as your extension type.
    4. Choose **Third party** as your Publisher.
    5. Search by **Extension name prefix** i.e. POC.
    6. Select the extension, then select **Activate**.
    7. For the **Execution Role ARN**, enter the saved ARN from earlier.
    8. Select **Activate extension**.

Once the extension is successfully activated, CloudFormation displays the details page for that extension.

For more information about available commands and workflows, see the official [AWS documentation][25].

## Supported regions

The sample extension is currently ONLY available in **us-east-1**.

## Example

### Provision a new Azure Storage account and a Blob Container. Extension creates a new Resource Group

```yaml
---
AWSTemplateFormatVersion: "2010-09-09"
Parameters:
  AzureSubscriptionId:
    Type: String
    Description: Subscription ID of the Azure Account
  AzureClientId:
    Type: String
    Description: App ID CloudFormation will use to access Azure. Prerequisite - setup a dedicated application service principal to Azure Blob Storage
  AzureTenantId:
    Type: String
    Description: Directory ID CloudFormation will use to access Azure
  AzureClientSecret:
    Type: String
    Description: Client credentials CloudFormation will use to authenticate to Azure and access services
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

### Add resource from AWS CloudFormation public registry to the AWS CDK app

Please refer to Step 3 of [this blog][5].

[1]: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/registry.html
[2]: https://aws.amazon.com/account/
[3]: https://aws.amazon.com/cli/
[4]: https://portal.azure.com/#home
[5]: https://amazon.awsapps.com/workdocs/index.html#/document/5e31c98cfa6ac8e028dc4bcbf3bdce56269411c43c45f41b367b29c1cd1eb9d2
[6]: https://aws.amazon.com/console/
[7]: https://github.com/aws-samples/aws-cloudformation-azure-storage-resource-provider/blob/main/resource-role.yaml
[8]: https://console.aws.amazon.com/cloudformation/
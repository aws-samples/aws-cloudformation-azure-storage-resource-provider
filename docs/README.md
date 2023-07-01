# POC::Azure::BlobStorage

An example resource that creates an Azure Storage account along with a Blob container.

## Syntax

To declare this entity in your AWS CloudFormation template, use the following syntax:

### JSON

<pre>
{
    "Type" : "POC::Azure::BlobStorage",
    "Properties" : {
        "<a href="#azuresubscriptionid" title="AzureSubscriptionId">AzureSubscriptionId</a>" : <i>String</i>,
        "<a href="#azureclientid" title="AzureClientId">AzureClientId</a>" : <i>String</i>,
        "<a href="#azuretenantid" title="AzureTenantId">AzureTenantId</a>" : <i>String</i>,
        "<a href="#azureclientsecret" title="AzureClientSecret">AzureClientSecret</a>" : <i>String</i>,
    }
}
</pre>

### YAML

<pre>
Type: POC::Azure::BlobStorage
Properties:
    <a href="#azuresubscriptionid" title="AzureSubscriptionId">AzureSubscriptionId</a>: <i>String</i>
    <a href="#azureclientid" title="AzureClientId">AzureClientId</a>: <i>String</i>
    <a href="#azuretenantid" title="AzureTenantId">AzureTenantId</a>: <i>String</i>
    <a href="#azureclientsecret" title="AzureClientSecret">AzureClientSecret</a>: <i>String</i>
</pre>

## Properties

#### AzureSubscriptionId

Subscription ID of the Azure Account.

_Required_: Yes

_Type_: String

_Update requires_: [No interruption](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-update-behaviors.html#update-no-interrupt)

#### AzureClientId

App ID CloudFormation will use to access Azure.

_Required_: Yes

_Type_: String

_Update requires_: [No interruption](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-update-behaviors.html#update-no-interrupt)

#### AzureTenantId

Directory ID CloudFormation will use to access Azure.

_Required_: Yes

_Type_: String

_Update requires_: [No interruption](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-update-behaviors.html#update-no-interrupt)

#### AzureClientSecret

Client credentials CloudFormation will use to authenticate to Azure and access services.

_Required_: Yes

_Type_: String

_Update requires_: [No interruption](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-update-behaviors.html#update-no-interrupt)

## Return Values

### Ref

When you pass the logical ID of this resource to the intrinsic `Ref` function, Ref returns the AzureBlobContainerUrl.

### Fn::GetAtt

The `Fn::GetAtt` intrinsic function returns a value for a specified attribute of this type. The following are the available attributes and sample return values.

For more information about using the `Fn::GetAtt` intrinsic function, see [Fn::GetAtt](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-getatt.html).

#### AzureBlobStorageAccountName

Name of the Blob Storage account created by CloudFormation.

#### AzureBlobContainerUrl

Url of the Blob container created by CloudFormation.

#### AzureResourceGroup

Name of the Resource Group created by CloudFormation.


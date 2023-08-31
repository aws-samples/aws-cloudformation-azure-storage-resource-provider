#STEP by STEP process on how to register a public extension.

#STEP 1 - ONLY needed when publishing for the first time.
#Register your account as a publisher of public extensions in the CloudFormation registry. 
#Public extensions are available for use by all CloudFormation users. 
#This publisher ID applies to your account in all Amazon Web Services Regions.
#Take note of the PublisherID output, you will need it for Step 4.
aws cloudformation register-publisher --region us-east-1 --accept-terms-and-conditions --connection-arn 'arn:aws:codestar-connections:us-east-1:xxxxxxxxxx:connection/xxxxxxxxxx'


#STEP 2 - Register the latest version of your extension privately.
cfn generate && cfn submit --set-default --region us-east-1


#STEP 3 - Test the (privately) registered extension to make sure it meets all necessary 
#requirements for being published publicly in the CloudFormation registry.
#Take note of the log-delivery-bucket parameter. This is the bucket where the test results are stored.
#Create the bucket in us-east-1 before executing below command.
#The user calling TestType must be able to access items in the specified S3 bucket. 
#Specifically, the user needs the following permissions - GetObject, PutObject
aws cloudformation test-type --arn arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:type/resource/POC-Azure-BlobStorage/xxxxxxxx --log-delivery-bucket 'azure-blob-storage-test-results'


#STEP 4 - test-type is an asynchronous operation. Use describe-type to check the 
#status of the operation.
aws cloudformation describe-type --arn arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:type/resource/POC-Azure-BlobStorage/xxxxxxxx --publisher-id xxxxxxxxxxxxxxxxxxxxxxxx


#STEP 5 - Publish the extension publicly.
aws cloudformation publish-type --type RESOURCE --type-name POC::Azure::BlobStorage


#Deregister an existing extension (public or privates).
#Note: The version ID is required for deregistration. Verify from console.
aws cloudformation deregister-type --type RESOURCE --type-name POC::Azure::BlobStorage  --version-id xxxxxxxx
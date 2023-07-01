import requests  #type: ignore
import adal  #type: ignore
import random
import logging
import traceback
import time
import datetime

from .exceptions import ResourceNotFoundException

from typing import (
    Any,
    Dict,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
)

from cloudformation_cli_python_lib import (  # type: ignore
    Action,
    HandlerErrorCode,
    OperationStatus,
    ProgressEvent,
    Resource,
    SessionProxy,
    exceptions,
    identifier_utils,
)

from .models import ResourceHandlerRequest, ResourceModel

# Use this logger to forward log messages to CloudWatch Logs.
LOG = logging.getLogger(__name__)

# Set logging level
# (https://docs.python.org/3/library/logging.html#levels);
# consider using logging.DEBUG for development and testing only.
LOG.setLevel(logging.DEBUG)
# LOG.setLevel(logging.DEBUG)

TYPE_NAME = "POC::Azure::BlobStorage"

resource = Resource(TYPE_NAME, ResourceModel)
test_entrypoint = resource.test_entrypoint

# Given the Azure resource creation could take than a minute, we need to implement a stabilization logic.
# The below variable will specify how long to wait in seconds to call the given handler again as part of the stabilization logic.
CALLBACK_DELAY_SECONDS = 30

# Define a context for the callback logic.  The value for the 'status'
# key in the dictionary below is consumed in is_callback() and in
# _callback_helper(), that are invoked from a given handler.
CALLBACK_STATUS_IN_PROGRESS = {
    "status": OperationStatus.IN_PROGRESS,
}

@resource.handler(Action.CREATE)
def create_handler(
    session: Optional[SessionProxy],
    request: ResourceHandlerRequest,
    callback_context: MutableMapping[str, Any],
) -> ProgressEvent:
    """Define the CREATE handler."""
    LOG.debug("*CREATE handler*")

    model = request.desiredResourceState
    progress: ProgressEvent = ProgressEvent(
        status=OperationStatus.IN_PROGRESS,
        resourceModel=model,
    )
    LOG.debug(f"Progress status: {progress.status}")

     # Check whether or not this is a new invocation of this handler.
    if _is_callback(
        callback_context,
    ):
        return _callback_helper(
            session,
            request,
            callback_context,
            model,
        )
    # If no callback context is present, then this is a new invocation.
    else:
        LOG.debug("No callback context present")

    try:

        # Constants we need in multiple places: the resource group name and the region
        # in which we provision resources. You can change these values however you want.
        # TODO: Turn them into CF Parameters

        # Azure Resource Group Details
        RESOURCE_GROUP_NAME = "Multicloud-Storage-rg"
        LOCATION = "australiasoutheast"
        
        # Azure Storage Account Details
        STORAGE_ACCOUNT_NAME = f"s3replicatedstorage{random.randint(1,100000):05}"
        SKU = 'Standard_LRS'
        KIND = 'StorageV2'

        # Azure Blob Container Details
        CONTAINER_NAME = 'blob-container-01'

        if model:

            # Authenticate to Azure using the Service Principal
            token = get_azure_token(model) 

            # Creating Resource Group
            headers = {'Authorization': 'Bearer ' + token['accessToken']}
            payload = {'location': LOCATION}
            url = 'https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}?api-version=2022-01-01'
            url = url.format(subscriptionId=model.AzureSubscriptionId, resourceGroupName=RESOURCE_GROUP_NAME)
            response = requests.put(url, headers=headers, json=payload)
        
            # Creating Storage Account
            payload = {
                'location': LOCATION,
                'sku': {
                    'name': SKU
                },
                'kind': KIND
            }       
            
            url = 'https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Storage/storageAccounts/{accountName}?api-version=2021-08-01'
            url = url.format(subscriptionId=model.AzureSubscriptionId, resourceGroupName=RESOURCE_GROUP_NAME, accountName=STORAGE_ACCOUNT_NAME)
            
            # Storage Account creation in Azure is an async operation.
            # Response code 202 indicates the request has been Accepted
            response = requests.put(url, headers=headers, json=payload)

            # Async operation has started
            if response.status_code == 202:

                # Get the URL for the operation status
                status_url = response.headers['Location']
                retry_after = response.headers['Retry-After']
            
                # Lets sleep first
                time.sleep(int(retry_after))

                # Now check the status of the operation
                while True:
                    response = requests.get(status_url, headers=headers)

                    # Check the status code
                    # 202 indicates it's still running
                    # 200 indicates it has completed
                    # Anything else, throw an exception
                                        
                    if response.status_code == 200:
                        LOG.info("Storage account creation succeeded!")
                        break
                    elif response.status_code == 202:
                        LOG.info(f"Storage account not yet provisioned")
                        # Wait before checking again
                        time.sleep(10)
                    else:
                        LOG.info("Storage account creation failed.")
                        # TODO: Handle the error
                        break

                # Every returned model must include the primary identifier, that in this case is the StorageAccountName.
                # Retrieving the primary identifier and setting it in the model.
                model.AzureBlobStorageAccountName = STORAGE_ACCOUNT_NAME
                model.AzureResourceGroup = RESOURCE_GROUP_NAME

                # Creating Blob Container
                url = 'https://{accountName}.blob.core.windows.net/{containerName}?restype=container'
                url = url.format(accountName=STORAGE_ACCOUNT_NAME, containerName=CONTAINER_NAME)

                # Get a new Azure token for performing Storage Account operations
                storage_token = get_azure_token_for_storage_account(model)
                headers = azure_storage_request_header(storage_token)
                
                response = requests.put(url, headers=headers)
                model.AzureBlobContainerUrl = url.split('?')[0]

                LOG.info(f"Blob Container Url: {model.AzureBlobContainerUrl}")
    
    except Exception as e:
        return _progress_event_failed(
            handler_error_code=HandlerErrorCode.InternalFailure,
            error_message=str(e),
            traceback_content=traceback.format_exc(),
        )
    
    return _progress_event_callback(
        model=model,
    )


@resource.handler(Action.DELETE)
def delete_handler(
    session: Optional[SessionProxy],
    request: ResourceHandlerRequest,
    callback_context: MutableMapping[str, Any],
) -> ProgressEvent:
    """Define the DELETE handler."""
    LOG.debug("*DELETE handler*")

    model = request.desiredResourceState

    progress: ProgressEvent = ProgressEvent(
        status=OperationStatus.IN_PROGRESS,
        resourceModel=None,
    )
    LOG.debug(f"Progress status: {progress.status}")

    try:

        # Call the Read handler to look for the resource, and return a
        # NotFound handler error code if the resource is not found.
        rh = read_handler(
            session,
            request,
            callback_context,
        )

        if rh.errorCode:
            if rh.errorCode == HandlerErrorCode.NotFound or rh.errorCode == HandlerErrorCode.InternalFailure:
                return _progress_event_failed(
                    handler_error_code=HandlerErrorCode.NotFound,
                    error_message=str(rh.message),
                    traceback_content=None,
                )
            
        if model:

            # Delete the Blob Storage
            delete_azure_storage_account(model)

    except ResourceNotFoundException as rnfe:
        return _progress_event_failed(
            handler_error_code=HandlerErrorCode.NotFound,
            error_message=str(rnfe),
            traceback_content=traceback.format_exc(),
        )

    except Exception as e:
        return _progress_event_failed(
            handler_error_code=HandlerErrorCode.InternalFailure,
            error_message=str(e),
            traceback_content=traceback.format_exc(),
        )
    
    return _progress_event_success(
        model=None, 
        is_delete_handler=True
    )


@resource.handler(Action.READ)
def read_handler(
    session: Optional[SessionProxy],
    request: ResourceHandlerRequest,
    callback_context: MutableMapping[str, Any],
) -> ProgressEvent:
    """Define the READ handler."""
    LOG.debug("*READ handler*")

    model = request.desiredResourceState

    progress: ProgressEvent = ProgressEvent(
        status=OperationStatus.IN_PROGRESS,
        resourceModel=model,
    )
    LOG.debug(f"Progress status: {progress.status}")

    LOG.info(f"Model: {model}")

    try:
        model_blobcontainerurl = ""
        model_storageaccountname = ""
        if model and model.AzureBlobContainerUrl:
            model_blobcontainerurl = model.AzureBlobContainerUrl
            model_storageaccountname = model.AzureBlobStorageAccountName

        response = get_azure_storage_account(model)

        if response.status_code == 200 and model:

            model.AzureBlobContainerUrl = model_blobcontainerurl
            model.AzureBlobStorageAccountName = model_storageaccountname
            
            model.AzureResourceGroup = model.AzureResourceGroup
            model.AzureSubscriptionId = model.AzureSubscriptionId
            model.AzureTenantId = model.AzureTenantId
            model.AzureClientId = model.AzureClientId
            model.AzureClientSecret = model.AzureClientSecret

    except ResourceNotFoundException as rnfe:
        return _progress_event_failed(
            handler_error_code=HandlerErrorCode.NotFound,
            error_message=str(rnfe),
            traceback_content=traceback.format_exc(),
        )

    except Exception as e:
        return _progress_event_failed(
            handler_error_code=HandlerErrorCode.InternalFailure,
            error_message=str(e),
            traceback_content=traceback.format_exc(),
        )
    
    return _progress_event_success(
        model=model,
    )


def _progress_event_callback(
    model: Optional[ResourceModel],
) -> ProgressEvent:
    """Return a ProgressEvent indicating a callback should occur next."""
    LOG.debug("_progress_event_callback()")

    return ProgressEvent(
        status=OperationStatus.IN_PROGRESS,
        resourceModel=model,
        callbackContext=CALLBACK_STATUS_IN_PROGRESS,
        callbackDelaySeconds=CALLBACK_DELAY_SECONDS,
    )


def _progress_event_success(
    model: Optional[ResourceModel] = None,
    models: Any = None,
    is_delete_handler: bool = False,
    is_list_handler: bool = False,
) -> ProgressEvent:
    """Return a ProgressEvent indicating a success."""
    LOG.debug("_progress_event_success()")

    if (
        not model
        and not models
        and not is_delete_handler
        and not is_list_handler
    ):
        raise ValueError(
            "Model, or models, or is_delete_handler, or is_list_handler unset",
        )
    # Otherwise, specify 'is_delete_handler' or 'is_list_handler', not both.
    elif is_delete_handler and is_list_handler:
        raise ValueError(
            "Specify either is_delete_handler or is_list_handler, not both",
        )
    # In the case of the Delete handler, just return the status.
    elif is_delete_handler:
        return ProgressEvent(
            status=OperationStatus.SUCCESS,
        )
    # In the case of the List handler, return the status and 'resourceModels'.
    elif is_list_handler:
        return ProgressEvent(
            status=OperationStatus.SUCCESS,
            resourceModels=models,
        )
    else:
        return ProgressEvent(
            status=OperationStatus.SUCCESS,
            resourceModel=model,
        )
    

def _progress_event_failed(
    handler_error_code: HandlerErrorCode,
    error_message: str,
    traceback_content: Any = None,
) -> ProgressEvent:
    """Log an error, and return a ProgressEvent indicating a failure."""
    LOG.debug("_progress_event_failed()")

    # Choose a logging level depending on the handler error code.
    log_entry = f"""Error message: {error_message},
    traceback content: {traceback_content}"""

    if handler_error_code == HandlerErrorCode.InternalFailure:
        LOG.critical(log_entry)
    elif handler_error_code == HandlerErrorCode.NotFound:
        LOG.error(log_entry)
    return ProgressEvent.failed(
        handler_error_code,
        f"Error: {error_message}",
    )
    

def _is_callback(
    callback_context: MutableMapping[str, Any],
) -> bool:
    """Logic to determine whether or not a handler invocation is new."""
    LOG.debug("_is_callback()")

    # If there is a callback context status set, then assume this is a
    # handler invocation (e.g., Create handler) for a previous request
    # that is still in progress.
    if callback_context.get("status") == CALLBACK_STATUS_IN_PROGRESS["status"]:
        return True
    else:
        return False
    
    
def _callback_helper(
    session: Optional[SessionProxy],
    request: ResourceHandlerRequest,
    callback_context: MutableMapping[str, Any],
    model: Optional[ResourceModel],
    is_delete_handler: bool = False,
) -> ProgressEvent:
    """Define a callback logic used for resource stabilization."""
    LOG.debug("_callback_helper()")

    # Call the Read handler to determine status.
    rh = read_handler(
        session,
        request,
        callback_context,
    )
    LOG.debug(f"Callback: Read handler status: {rh.status}")

    # Return success if the Read handler returns success.
    if rh.status == OperationStatus.SUCCESS:
        return _progress_event_success(
            model=model,
        )
    elif rh.errorCode:
        LOG.debug(f"Callback: Read handler error code: {rh.errorCode}")
        if rh.errorCode == HandlerErrorCode.NotFound and is_delete_handler:
            LOG.debug("NotFound error in Delete handler: returning success")

            # Return a success status if the resource is not found
            # (thus, assuming it has been deleted).  The Delete
            # handler's response object must not contain a model:
            # hence, the logic driven by is_delete_handler set to True
            # below will not specify a model for ProgressEvent.
            return _progress_event_success(
                is_delete_handler=True,
            )
        elif rh.errorCode == HandlerErrorCode.NotFound:
            return _progress_event_failed(
                handler_error_code=rh.errorCode,
                error_message=rh.message,
                traceback_content=None,
            )
    # Otherwise, call this handler again by using a callback logic.
    else:
        return _progress_event_callback(
            model=model,
        )
    
# Azure Helper Methods
def get_azure_storage_account(model: ResourceModel):
    
    # Get a new token
    token = get_azure_token(model)

    if token:

        headers = {'Authorization': 'Bearer ' + token['accessToken']}
        url = f"https://management.azure.com/subscriptions/{model.AzureSubscriptionId}/resourceGroups/{model.AzureResourceGroup}/providers/Microsoft.Storage/storageAccounts/{model.AzureBlobStorageAccountName}?api-version=2021-04-01"

        response = requests.get(url, headers=headers)

        # Check the response code for Not Found
        if response.status_code == 200:
            LOG.info(f"Storage Account {model.AzureBlobStorageAccountName} exists!")
        elif response.status_code == 404:
            LOG.warning(f"Storage account {model.AzureBlobStorageAccountName} DOES NOT exist")
            raise ResourceNotFoundException(f"Storage account {model.AzureBlobStorageAccountName} DOES NOT exist")    
        else:
            raise Exception(f"ERROR: {response.status_code} - {response.content}")      
        
        return response
    
    
def delete_azure_storage_account(model: ResourceModel):

    # Get a new token
    token = get_azure_token(model)

    if token:

        headers = {'Authorization': 'Bearer ' + token['accessToken']}
        url = f"https://management.azure.com/subscriptions/{model.AzureSubscriptionId}/resourceGroups/{model.AzureResourceGroup}/providers/Microsoft.Storage/storageAccounts/{model.AzureBlobStorageAccountName}?api-version=2022-09-01"

        response = requests.delete(url, headers=headers)

        # Check the response code for Not Found
        if response.status_code == 200:
            LOG.info(f"Storage Account DELETE requested either Accepted or Completed!")
        elif response.status_code == 204:
            LOG.warning(f"Storage account {model.AzureBlobStorageAccountName} DOES NOT exist")
            raise ResourceNotFoundException(f"Storage account {model.AzureBlobStorageAccountName} DOES NOT exist")  
        else:
            raise Exception(f"ERROR: {response.status_code} - {response.content}")        
        
        return response
    

def get_azure_token(model: ResourceModel):

    # Authentication with Azure AD
    AUTHORITY_HOST_URL = 'https://login.microsoftonline.com'
    AUTHORITY_URL = AUTHORITY_HOST_URL + '/' + model.AzureTenantId
    RESOURCE_URL = 'https://management.azure.com'
    context = adal.AuthenticationContext(AUTHORITY_URL)

    token = context.acquire_token_with_client_credentials(RESOURCE_URL, model.AzureClientId, model.AzureClientSecret)
    return token


def get_azure_token_for_storage_account(model: ResourceModel, 
                                        resource_url = 'https://storage.azure.com/'):
    
    # Construct the access token request
    token_url = f'https://login.microsoftonline.com/{model.AzureTenantId}/oauth2/token'
    token_request_data = {
        'grant_type': 'client_credentials',
        'client_id': model.AzureClientId,
        'client_secret': model.AzureClientSecret,
        'resource': resource_url
    }

    response = requests.post(token_url, data=token_request_data)

    response_json = response.json()
    return response_json['access_token']

def azure_storage_request_header(token: str):

    headers = {
                    'x-ms-version': '2019-02-02',
                    'x-ms-date': datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT'),
                    'Authorization': f'Bearer {token}'
                }
    
    return headers
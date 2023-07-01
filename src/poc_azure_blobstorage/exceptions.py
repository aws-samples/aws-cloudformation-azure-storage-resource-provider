# define Python user-defined exceptions
class ResourceNotFoundException(Exception):
    "When the requested Azure resource is not found"
    pass
InternalServerErrorMessage = "Error occured during operation. We're currently checking why this happend."
unprocessableEntityErrorMessage="Unprocessable Entity. Error during payload Validation."
httpErrorMessage="Error occured during operation. Please try again later."
serviceUnavailableErrorMessage="Error occured during operation. Please try again later.",
operationForbiddenErrorMessage= "Operation forbidden",
notFoundErrorMessage="No support ticket found.",
unauthorizedErrorMessage = "Unauthorized access."
badRequestErrorMessage = "Bad request. Check your input parameters."

errorTypes = {
    "HTTP_ERROR": 'HTTP_ERROR',
    "HTTP_CONNECTION_ERROR": 'HTTP_CONNECTION_ERROR',
    "INTERNAL_SERVER_ERROR": 'INTERNAL_SERVER_ERROR',
    "UNPROCESSABLE_ENTITY": 'UNPROCESSABLE_ENTITY',
    "VALIDATION_FAILED": "VALIDATION_FAILED",
    "OPERATION_FORBIDDEN": 'OPERATION_FORBIDDEN',
    "NOT_FOUND_ERROR": 'NOT_FOUND_ERROR',
    "UNAUTHORIZED_ACCESS": "UNAUTHORIZED_ACCESS",
    "BAD_REQUEST": "BAD_REQUEST",
    "SERVICE_UNAVAILABLE": "SERVICE_UNAVAILABLE"
}

statusCodes = {
    "200":200,
    "201":201,
    "400":400,
    "401":401,
    "422":422,
    "403":403,
    "404":404,
    "500":500,
    "503": 503
}
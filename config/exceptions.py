from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Adds a stable `code` and `errors` shape for validation errors.
    """
    response = exception_handler(exc, context)
    if response is None:
        return response

    payload = {"detail": response.data} if not isinstance(response.data, dict) else response.data
    if isinstance(payload, dict) and "detail" in payload and len(payload) == 1:
        body = {"success": False, "code": response.status_code, "message": payload["detail"]}
    else:
        body = {
            "success": False,
            "code": response.status_code,
            "errors": payload,
        }
    response.data = body
    return response

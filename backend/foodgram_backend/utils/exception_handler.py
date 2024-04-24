from rest_framework.views import exception_handler


def custom_exception_hendler(exc, context):
    '''Кастомный хендлер ошибок'''
    handlers = {
        'Http404': http_error,
        'PermissionDenied': permission_error,
    }
    response = exception_handler(exc, context)
    exception_class = exc.__class__.__name__
    if exception_class in handlers:
        return handlers[exception_class](exc, context, response)
    return response


def http_error(exc, context, response):
    '''Обработка ошибки 404'''
    response.data = {"detail": "Страница не найдена."}
    return response


def permission_error(exc, context, response):
    '''Обработка ошибки 403'''
    response.data = {
        "detail": "У вас недостаточно прав для выполнения данного действия."
    }
    return response

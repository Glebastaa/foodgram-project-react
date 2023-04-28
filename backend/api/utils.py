from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response:
        if response.status_code == 400:
            new_data = {}
            for field, errors in response.data.items():
                if field != 'non_field_errors':
                    if field == 'password':
                        new_errors = []
                        for _ in [errors]:
                            if exc.detail['password'][0] == (
                                'This password is too common.'
                            ):
                                new_errors.append('Пароль слишком простой')
                            elif exc.detail['password'][1] == (
                                'This password is too common.'
                            ):
                                new_errors.append(
                                    'Пароль должен содержать '
                                    'минимум 8 символов'
                                )
                            new_data[field] = new_errors
                        response.data = new_data
        if response.status_code == 401:
            response.data['detail'] = 'Учетные данные не были предоставлены.'
        if response.status_code == 403:
            response.data[
                'detail'
            ] = 'У вас недостаточно прав для выполнения данного действия.'
        if response.status_code == 404:
            response.data['detail'] = 'Страница не найдена.'
    return response

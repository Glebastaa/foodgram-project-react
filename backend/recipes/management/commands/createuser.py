import os

from django.core.management import BaseCommand

from users.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Создание пользователя")
        username = os.getenv(
            'SUPERUSER_NAME',
            default='admin'
        )
        password = os.getenv(
            'SUPERUSER_PASSWORD',
            default='28admin31337'
        )
        email = os.getenv(
            'SUPERUSER_EMAIL',
            default='admin@admin.ru'
        )
        first_name = os.getenv(
            'SUPERUSER_FNAME',
            default='Админ'
        )
        last_name = os.getenv(
            'SUPERUSER_FNAME',
            default='Админов'
        )

        if username and password and email:
            user, created = User.objects.get_or_create(
                username=username,
                email=email,
            )
            if created:
                user.set_password(password)
                user.is_superuser = True
                user.is_active = True
                user.is_staff = True
                user.first_name = first_name
                user.last_name = last_name
                user.save()
                print("Пользователь создан")
            else:
                print("Пользователь уже был в базе")

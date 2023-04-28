from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    username = models.CharField(
        'Логин',
        max_length=30,
        unique=True,
        blank=False,
    )

    email = models.EmailField(
        'E-mail пользователя',
        unique=True,
        max_length=40,
        blank=False,
    )

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        ordering = ['-username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователей'

    @staticmethod
    def get_user(id_):
        try:
            return User.objects.get(pk=id_)
        except User.DoesNotExist:
            return None

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Инициализация модели Follow."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Автор',
    )

    def __str__(self):
        return f'{self.user.username} - {self.author.username}'

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_user_author'
            ),
        ]

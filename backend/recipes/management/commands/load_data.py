import json

from django.core.management import BaseCommand
from recipes.models import Ingredients, Tags


class Command(BaseCommand):
    def handle(self, *args, **options):
        if Ingredients.objects.exists():
            print("Ингредиенты уже импортированы")
            return None
        print("Загрузка ingredients.json")
        with open(
            "./data/ingredients.json",
            "r", encoding="utf-8"
        ) as json_data:
            data = json.loads(json_data.read())

            ingredients = [
                Ingredients(
                    name=item.get("name"),
                    measurement_unit=item.get("measurement_unit"),
                )
                for item in data
            ]
            Ingredients.objects.bulk_create(ingredients)

        if Tags.objects.exists():
            return print("Теги уже импортированы")
        print("Загрузка tags.json")
        with open(
            "./data/tags.json",
            "r", encoding="utf-8"
        ) as json_data:
            data = json.loads(json_data.read())
            tags = [
                Tags(
                    name=item.get("name"),
                    color=item.get("color"),
                    slug=item.get("slug"),
                )
                for item in data
            ]
            Tags.objects.bulk_create(tags)
            return "Данные успешно импортированы"

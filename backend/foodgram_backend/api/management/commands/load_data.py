import csv

from django.core.management.base import BaseCommand

from recipes.models import Tag, Ingredient


data = {
    Tag: 'data/tags.csv',
    Ingredient: 'data/ingredients.csv'
}


class Command(BaseCommand):
    """Команда для добавления информации в БД."""

    def handle(self, *args, **options):
        for model in data.keys():
            model_name = model.__name__
            print(f'Началась загрузка модели {model_name}.')
            try:
                with open(data[model], encoding='utf-8') as file:
                    for row in csv.reader(file):
                        if model == Tag:
                            name, color, slug = row
                            Tag.objects.get_or_create(
                                name=name, color=color, slug=slug
                            )
                        else:
                            name, measurement_unit = row
                            Ingredient.objects.get_or_create(
                                name=name, measurement_unit=measurement_unit
                            )
            except FileNotFoundError:
                print(f"Запрашиваемый файл {data[model]} не найден")

            print(f'Загрузка модели {model_name} завершена.')

import csv

from django.core.management.base import BaseCommand

from api.models import Tag, Ingredient


data = {
    Tag: 'data/tags.csv',
    Ingredient: 'data/ingredients.csv'
}


class Command(BaseCommand):
    """Команда для добавления информации в БД."""

    def handle(self, *args, **options):
        for model in data.keys():
            with open(data[model], encoding='utf-8') as file:
                for row in csv.reader(file):
                    if model == Tag:
                        Tag.objects.get_or_create(
                            name=row[0], color=row[1], slug=row[2]
                        )
                    else:
                        Ingredient.objects.get_or_create(
                            name=row[0], measurement_unit=row[1]
                        )

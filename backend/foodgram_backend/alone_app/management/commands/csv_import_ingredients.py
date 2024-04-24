import csv

from django.core.management.base import BaseCommand

from alone_app.models import Ingredient


class Command(BaseCommand):
    """Команда для добавления файла с ингредиентами в БД."""

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **options):
        with open(options['csv_file'], encoding='utf-8') as file:
            for row in csv.reader(file):
                Ingredient.objects.create(name=row[0], measurement_unit=row[1])

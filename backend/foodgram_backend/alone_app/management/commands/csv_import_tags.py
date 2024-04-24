import csv

from django.core.management.base import BaseCommand

from alone_app.models import Tag


class Command(BaseCommand):
    """Команда для добавления файла с Тегами в БД."""

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **options):
        with open(options['csv_file'], encoding='utf-8') as file:
            for row in csv.reader(file):
                Tag.objects.create(name=row[0], color=row[1], slug=row[2])

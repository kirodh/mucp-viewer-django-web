import csv
from django.core.management.base import BaseCommand
from support.models import GrowthForm, TreatmentMethod, Species, Herbicide, ClearingNorm, ClearingNormSet,  Category, NumericPriorityBand, TextPriorityValue


class Command(BaseCommand):
    help = 'Load default data for the support app'

    def handle(self, *args, **kwargs):
        # Your custom logic here
        Category.objects.all().delete()
        NumericPriorityBand.objects.all().delete()
        TextPriorityValue.objects.all().delete()
        ClearingNorm.objects.all().delete()
        ClearingNormSet.objects.all().delete()
        TreatmentMethod.objects.all().delete()
        Herbicide.objects.all().delete()
        Species.objects.all().delete()
        GrowthForm.objects.all().delete()


        self.stdout.write(self.style.SUCCESS('Default data deleted successfully.'))

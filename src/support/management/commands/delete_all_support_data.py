import csv
from django.core.management.base import BaseCommand
from support.models import GrowthForm, TreatmentMethod, Species, Herbicide, ClearingNorm, ClearingNormSet,  Category, NumericPriorityBand, TextPriorityValue


class Command(BaseCommand):
    help = 'Load default data for the support app'

    def handle(self, *args, **kwargs):
        # Your custom logic here
        # Category.objects.all().delete()
        # NumericPriorityBand.objects.all().delete()
        # TextPriorityValue.objects.all().delete()
        # ClearingNorm.objects.all().delete()
        # ClearingNormSet.objects.all().delete()
        # TreatmentMethod.objects.all().delete()
        # Herbicide.objects.all().delete()
        # Species.objects.all().delete()
        # GrowthForm.objects.all().delete()

        Category.objects.filter(user__isnull=True).delete()
        NumericPriorityBand.objects.filter(user__isnull=True).delete()
        TextPriorityValue.objects.filter(user__isnull=True).delete()
        ClearingNorm.objects.filter(user__isnull=True).delete()
        ClearingNormSet.objects.filter(user__isnull=True).delete()
        TreatmentMethod.objects.filter(user__isnull=True).delete()
        Herbicide.objects.filter(user__isnull=True).delete()
        Species.objects.filter(user__isnull=True).delete()
        GrowthForm.objects.filter(user__isnull=True).delete()

        self.stdout.write(self.style.SUCCESS('Default data deleted successfully.'))

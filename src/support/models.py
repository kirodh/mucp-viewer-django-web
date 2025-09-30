"""
MUCP TOOL
Author: Kirodh Boodhraj
"""
# models.py
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

# growth form model
class GrowthForm(models.Model):
    growth_form = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='growth_form')

    def __str__(self):
        return self.growth_form

    class Meta:
        unique_together = ('growth_form', 'user')  # prevents duplicate names per user
        ordering = ['growth_form']

# treatment method model
class TreatmentMethod(models.Model):
    treatment_method = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='treatment_methods')

    def __str__(self):
        return self.treatment_method

    class Meta:
        unique_together = ('treatment_method', 'user')  # prevents duplicate names per user
        ordering = ['treatment_method']


# species model
class Species(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)  # null = default data

    species_name = models.CharField(max_length=200)
    genus = models.CharField(max_length=100)
    english_name = models.CharField(max_length=100, blank=True, null=True)
    afrikaans_name = models.CharField(max_length=100, blank=True, null=True)

    growth_form = models.ForeignKey('GrowthForm', on_delete=models.PROTECT)

    # Provinces
    WC = models.BooleanField(default=False)
    NC = models.BooleanField(default=False)
    KZN = models.BooleanField(default=False)
    GTG = models.BooleanField(default=False)
    MPL = models.BooleanField(default=False)
    FS = models.BooleanField(default=False)
    EC = models.BooleanField(default=False)
    LMP = models.BooleanField(default=False)
    NW = models.BooleanField(default=False)

    # Treatment Data
    initial_reduction = models.FloatField(null=True, blank=True)
    follow_up_reduction = models.FloatField(null=True, blank=True)
    treatment_frequency = models.IntegerField(null=True, blank=True)
    densification = models.IntegerField(null=True, blank=True)
    flow_optimal = models.FloatField(null=True, blank=True)
    flow_sub_optimal = models.FloatField(null=True, blank=True)
    flow_young = models.FloatField(null=True, blank=True)
    flow_seedling = models.FloatField(null=True, blank=True)
    flow_coppice = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.species_name

# herbicide model
class Herbicide(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)  # null = default data

    herbicide = models.CharField(max_length=100)
    cost_per_litre = models.FloatField()
    litres_per_hectare = models.FloatField()
    active_ingredient = models.CharField(max_length=255)
    registration_status = models.CharField(max_length=100)

    def __str__(self):
        return self.herbicide

# clearing norm set model
class ClearingNormSet(models.Model):
    """
    Groups clearing norms together (e.g. APO Default, APO Norm, Custom Norms)
    """
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)  # null = default data

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'user'], name='unique_name_per_user')
        ]

# clearing norm model
class ClearingNorm(models.Model):
    PROCESS_CHOICES = [
        ("Initial", "initial"),
        ("Follow-up", "follow-up"),
    ]

    SIZE_CLASS_CHOICES = [
        ("All", "all"),
        ("Seedling", "seedling"),
        ("Young", "young"),
        ("Adult", "adult"),
    ]

    TERRAIN_CHOICES = [
        ("Landscape", "landscape"),
        ("Riparian", "riparian"),
    ]

    density = models.FloatField()
    process = models.CharField(max_length=20, choices=PROCESS_CHOICES)
    growth_form = models.ForeignKey('GrowthForm', on_delete=models.CASCADE)
    size_class = models.CharField(max_length=20, choices=SIZE_CLASS_CHOICES)
    treatment_method = models.ForeignKey('TreatmentMethod', on_delete=models.CASCADE)
    terrain = models.CharField(max_length=20, choices=TERRAIN_CHOICES)
    ppd = models.FloatField()

    clearing_norm_set = models.ForeignKey(
        ClearingNormSet,
        on_delete=models.CASCADE,
        related_name="norms"
    )

    def __str__(self):
        return f"{self.process} - {self.growth_form} - {self.size_class} ({self.terrain})"



# choice options
CATEGORY_TYPE_CHOICES = [
    ('numeric', 'Numeric'),
    ('text', 'Text'),
]

DEFAULT_NUMERIC_CATEGORIES = [
    "Aggression", "Diversity", "Density", "Elevation", "Erosion", "Flood", "Forage",
    "Fuel", "Invasion", "Products", "Quality", "Rain", "Riparian", "River",
    "Runoff", "Seepage", "Situation", "Slope", "Soil", "Stress", "Tourism",
    "Treat", "Veld Age", "Zone"
]

DEFAULT_TEXT_CATEGORIES = ["Owner", "Status"]

# category model
class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, help_text="Null for default categories")
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPE_CHOICES)
    is_default = models.BooleanField(default=False)

    weight = models.FloatField(
        default=0.0,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(1.0)
        ],
        help_text="A value between 0 and 1 inclusive"
    )

    class Meta:
        unique_together = [
            ('user', 'name'),
            # to prevent duplicate custom names per user
        ]

    def clean(self):
        # Normalize name to lowercase (also works with validation checks)
        if self.name:
            self.name = self.name.lower()

        # prevent duplicates for default categories
        if self.is_default:
            if Category.objects.filter(name=self.name, is_default=True).exclude(pk=self.pk).exists():
                raise ValidationError(f"Default category '{self.name}' already exists.")


        # Enforce float value safety
        if self.weight is None:
            self.weight = 0.0
        else:
            self.weight = round(self.weight, 3)

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.lower()
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.category_type}){' [Default]' if self.is_default else ''}"

# numeric priority band model
class NumericPriorityBand(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="numeric_bands")
    range_low = models.FloatField()
    range_high = models.FloatField()
    priority = models.PositiveIntegerField()

    class Meta:
        ordering = ['range_low']
        unique_together = [('category', 'range_low', 'range_high')]

    def clean(self):
        # Ensure low < high
        if self.range_low >= self.range_high:
            raise ValidationError({
                'range_high': _("Range high must be greater than range low.")
            })



    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name}: {self.range_low} - {self.range_high} = Priority {self.priority}"

# text priority value model
class TextPriorityValue(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="text_values")
    text_value = models.CharField(max_length=200)
    priority = models.PositiveIntegerField()

    class Meta:
        unique_together = [('category', 'text_value')]
        ordering = ['text_value']

    def __str__(self):
        return f"{self.category.name}: '{self.text_value}' = Priority {self.priority}"


# costing model
class CostingModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, verbose_name="Costing Model Name")
    initial_team_size = models.PositiveIntegerField()
    initial_cost_per_day = models.FloatField()
    followup_team_size = models.PositiveIntegerField()
    followup_cost_per_day = models.FloatField()
    vehicle_cost_per_day = models.FloatField()
    fuel_cost_per_hour = models.FloatField()
    maintenance_level = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'name'], name='unique_model_name_per_user')
        ]

    @property
    def total_cost_per_day(self):
        """
        Base costs + sum of *this user's* daily cost items for this model.
        Defaults to base cost only if no daily cost items exist.
        """

        # If no daily cost items, extra cost = 0
        daily_items_cost = sum(
            item.daily_item_cost for item in self.daily_cost_items.all()
        ) if self.daily_cost_items.exists() else 0

        # return base_cost + daily_items_cost
        return daily_items_cost

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('costingmodel_list')


# daily cost model
class DailyCostItem(models.Model):
    costing_model = models.ForeignKey(
        CostingModel,
        related_name='daily_cost_items',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # ensures per-user data
    daily_cost_item = models.CharField(max_length=200)
    daily_item_cost = models.FloatField()

    def __str__(self):
        return f"{self.daily_cost_item} ({self.daily_item_cost})"

    def get_absolute_url(self):
        return reverse('costingmodel_update', args=[self.costing_model.id])





"""
MUCP TOOL
Author: Kirodh Boodhraj
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from support.models import CostingModel

# Planning model
class Planning(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="planning")

    # Foreign keys to your existing models
    project = models.ForeignKey("project.Project", on_delete=models.CASCADE)
    clearing_norm_model = models.ForeignKey("support.ClearingNormSet", on_delete=models.CASCADE)

    # Planning budget amounts
    budget_plan_1 = models.FloatField(validators=[MinValueValidator(0.0)])
    budget_plan_2 = models.FloatField(validators=[MinValueValidator(0.0)])
    budget_plan_3 = models.FloatField(validators=[MinValueValidator(0.0)])
    budget_plan_4 = models.FloatField(validators=[MinValueValidator(0.0)])

    # Percent escalation (1–100)
    escalation_plan_1 = models.FloatField(validators=[MinValueValidator(1.0), MaxValueValidator(100.0)])
    escalation_plan_2 = models.FloatField(validators=[MinValueValidator(1.0), MaxValueValidator(100.0)])
    escalation_plan_3 = models.FloatField(validators=[MinValueValidator(1.0), MaxValueValidator(100.0)])
    escalation_plan_4 = models.FloatField(validators=[MinValueValidator(1.0), MaxValueValidator(100.0)])

    standard_working_day = models.FloatField(
        default=8.0,
        validators=[MinValueValidator(1.0), MaxValueValidator(24.0)]
    )

    standard_working_year_days = models.PositiveIntegerField(
        default=220,
        validators=[MinValueValidator(1), MaxValueValidator(365)]
    )

    # Start year
    start_year = models.PositiveIntegerField(
        validators=[MinValueValidator(1900)]
    )

    # Planning years to run
    years_to_run = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )

    # Currency choices
    CURRENCY_CHOICES = [
        ("ZAR", "South African Rand"),
        ("USD", "US Dollar"),
        ("EUR", "Euro"),
        ("GBP", "British Pound"),
        ("JPY", "Japanese Yen"),
    ]
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="ZAR")

    # Save results toggle
    save_results = models.BooleanField(default=False)

    # Date created
    created_at = models.DateTimeField(auto_now_add=True)


    @property
    def has_complete_costing_mapping(self):
        # Returns True if there is at least one costing mapping
        return self.costing_mappings.exists()

    def save(self, *args, **kwargs):
        # Round all float fields to 2 decimal places
        for field in [
            "budget_plan_1", "budget_plan_2", "budget_plan_3", "budget_plan_4",
            "escalation_plan_1", "escalation_plan_2", "escalation_plan_3", "escalation_plan_4"
        ]:
            value = getattr(self, field, None)
            if value is not None:
                setattr(self, field, round(value, 2))

        if self.standard_working_day is not None:
            self.standard_working_day = round(self.standard_working_day, 2)


        super().save(*args, **kwargs)



    def __str__(self):
        return f"Planning for {self.project} ({self.start_year})"


# choose the prioritization categories for the plan model
class PlanningCategory(models.Model):
    planning = models.ForeignKey(Planning, on_delete=models.CASCADE, related_name="planning_categories")
    category = models.ForeignKey("support.Category", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("planning", "category")  # prevents duplicates

    def __str__(self):
        return f"{self.category} for {self.planning}"

# define cost mapping per planning model
class PlanningCostingMapping(models.Model):
    planning = models.ForeignKey("Planning", on_delete=models.CASCADE, related_name="costing_mappings")
    costing_value = models.CharField(max_length=100)  # from compartment shapefile
    costing_model = models.ForeignKey(CostingModel, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("planning", "costing_value")

    def __str__(self):
        return f"{self.planning} - {self.costing_value} → {self.costing_model}"

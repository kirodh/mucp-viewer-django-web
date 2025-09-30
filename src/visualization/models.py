"""
MUCP TOOL
Author: Kirodh Boodhraj
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from planning.models import Planning

# Budget model
class BudgetScenario(models.Model):
    """Represents one of the 5 budgets (optimal, budget_1, budget_2, etc)."""
    planning = models.ForeignKey(Planning, on_delete=models.CASCADE, related_name="budgets")

    SCENARIO_CHOICES = [
        ("optimal", "Optimal"),
        ("budget_1", "Budget 1"),
        ("budget_2", "Budget 2"),
        ("budget_3", "Budget 3"),
        ("budget_4", "Budget 4"),
    ]
    name = models.CharField(max_length=20, choices=SCENARIO_CHOICES)

    def __str__(self):
        return f"{self.get_name_display()} ({self.planning})"


# yearly timestep model
class YearlyResult(models.Model):
    """Each budget has results per year."""
    budget = models.ForeignKey(BudgetScenario, on_delete=models.CASCADE, related_name="yearly_results")
    year = models.PositiveIntegerField()

    class Meta:
        unique_together = ("budget", "year")

    def __str__(self):
        return f"{self.year} - {self.budget}"

# data line per row in simulation model
class SimulationRow(models.Model):
    """One row in the simulation output for a given year & budget."""
    yearly_result = models.ForeignKey(YearlyResult, on_delete=models.CASCADE, related_name="rows")

    nbal_id = models.CharField(max_length=50, null=True, blank=True)
    miu_id = models.CharField(max_length=50, null=True, blank=True)
    compt_id = models.CharField(max_length=50, null=True, blank=True)
    priority = models.FloatField(null=True, blank=True)
    person_days = models.FloatField()
    cost = models.FloatField(null=True, blank=True)
    density = models.FloatField()
    flow = models.FloatField()
    cleared_now = models.BooleanField(default=False)
    cleared_fully = models.BooleanField(default=False)


    def __str__(self):
        return f"Row {self.link_back_id} ({self.yearly_result})"

# propagated budget model
class SimulationBudgetYear(models.Model):
    """
    Stores the propagated budget values per year for a planning run.
    Example: {2025: {'plan_1': 1.0, 'plan_2': 1.0, 'plan_3': 1.0, 'plan_4': 1.0}}
    """
    planning = models.ForeignKey(
        "planning.Planning",
        on_delete=models.CASCADE,
        related_name="budget_years"
    )

    year = models.PositiveIntegerField(validators=[MinValueValidator(1900)])

    plan_1 = models.FloatField(validators=[MinValueValidator(0.0)])
    plan_2 = models.FloatField(validators=[MinValueValidator(0.0)])
    plan_3 = models.FloatField(validators=[MinValueValidator(0.0)])
    plan_4 = models.FloatField(validators=[MinValueValidator(0.0)])

    class Meta:
        unique_together = ("planning", "year")

    def save(self, *args, **kwargs):
        # Round to 2 decimal places before saving
        if self.plan_1 is not None:
            self.plan_1 = round(self.plan_1, 2)
        if self.plan_2 is not None:
            self.plan_2 = round(self.plan_2, 2)
        if self.plan_3 is not None:
            self.plan_3 = round(self.plan_3, 2)
        if self.plan_4 is not None:
            self.plan_4 = round(self.plan_4, 2)
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Budget {self.year} for Planning {self.planning_id}"

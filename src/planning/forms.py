"""
MUCP TOOL
Author: Kirodh Boodhraj
"""
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import Planning, PlanningCategory, PlanningCostingMapping
from support.models import Category, CostingModel
from project.models import Project

# planning form
class PlanningForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Planning
        fields = [
            "project", "clearing_norm_model",
            "budget_plan_1", "budget_plan_2", "budget_plan_3", "budget_plan_4",
            "escalation_plan_1", "escalation_plan_2", "escalation_plan_3", "escalation_plan_4",
            "standard_working_day", "standard_working_year_days", "start_year", "years_to_run", "currency", "save_results",
            "categories",  # include here so form renders it
        ]
        widgets = {
            "project": forms.Select(attrs={"class": "form-select"}),
            "costing_model": forms.Select(attrs={"class": "form-select"}),
            "currency": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user:
            # Limit projects to those belonging to the user
            self.fields["project"].queryset = Project.objects.filter(user=user)

            # Get user-created category names
            user_cat_names = Category.objects.filter(user=user).values_list("name", flat=True)

            # Start with all categories
            qs = Category.objects.all()

            # Exclude default categories that have the same name as a user-created one
            qs = qs.exclude(is_default=True, name__in=user_cat_names)

            # Include user-created categories and remaining defaults
            qs = qs.filter(Q(is_default=True) | Q(user=user))

            self.fields["categories"].queryset = qs

    def clean_standard_working_day(self):
        hours = self.cleaned_data["standard_working_day"]
        if hours < 1 or hours > 24:
            raise ValidationError("Working day hours must be between 1 and 24.")
        return hours

    def clean_years_to_run(self):
        years = self.cleaned_data["years_to_run"]
        if years < 1 or years > 50:
            raise ValidationError("Years to run must be between 1 and 50.")
        return years

    def clean_start_year(self):
        year = self.cleaned_data["start_year"]
        if year < 1900:
            raise ValidationError("Start year cannot be earlier than 1900.")
        return year


    def clean(self):
        cleaned_data = super().clean()
        # Example: ensure escalation percentages are 0-100
        for i in range(1, 5):
            escalation = cleaned_data.get(f"escalation_plan_{i}")
            if escalation is not None and (escalation < 0 or escalation > 100):
                self.add_error(f"escalation_plan_{i}", "Escalation must be between 0 and 100%.")
        return cleaned_data

    def clean_categories(self):
        categories = self.cleaned_data.get("categories")
        if categories.count() > 6:
            raise ValidationError("You can select a maximum of 6 categories.")
        return categories

    def save(self, commit=True):
        # Save the planning instance
        planning = super().save(commit=commit)

        # Handle categories link
        categories = self.cleaned_data.get("categories")
        if commit:
            # Remove old links first (if editing)
            PlanningCategory.objects.filter(planning=planning).delete()
            # Create new links
            for category in categories:
                PlanningCategory.objects.create(planning=planning, category=category)


        return planning


# cost mapping form
class CostingAssignmentForm(forms.Form):
    def __init__(self, *args, **kwargs):
        costing_values = kwargs.pop("costing_values", [])
        initial_map = kwargs.pop("initial_map", {})  # handle it here
        super().__init__(*args, **kwargs)

        for val in costing_values:
            self.fields[f"costing_{val}"] = forms.ModelChoiceField(
                queryset=CostingModel.objects.all(),
                required=True,
                label=f"Assign model for costing value '{val}'",
                initial=initial_map.get(val)  # pre-populate if available
            )
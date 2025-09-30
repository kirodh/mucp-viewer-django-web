"""
MUCP TOOL
Author: Kirodh Boodhraj
"""
# forms.py
from django import forms
from .models import GrowthForm, TreatmentMethod, Species, Herbicide, ClearingNorm, ClearingNormSet, CostingModel, DailyCostItem, Category, TextPriorityValue, NumericPriorityBand
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

# growth form form
class GrowthFormForm(forms.ModelForm):
    class Meta:
        model = GrowthForm
        fields = ['growth_form']

    def clean_growth_form(self):
        value = self.cleaned_data['growth_form']
        return value.lower().strip()

# treatment method form
class TreatmentMethodForm(forms.ModelForm):
    class Meta:
        model = TreatmentMethod
        fields = ['treatment_method']

    def clean_treatment_method(self):
        value = self.cleaned_data['treatment_method']
        return value.lower().strip()

# species form
class SpeciesForm(forms.ModelForm):
    class Meta:
        model = Species
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(SpeciesForm, self).__init__(*args, **kwargs)

        required_fields = [
            'initial_reduction',
            'follow_up_reduction',
            'treatment_frequency',
            'densification',
            'flow_optimal',
            'flow_sub_optimal',
            'flow_young',
            'flow_seedling',
            'flow_coppice',
        ]
        for field_name in required_fields:
            self.fields[field_name].required = True

        if user:
            self.fields['growth_form'].queryset = GrowthForm.objects.filter(models.Q(user=None) | models.Q(user=user)).order_by('growth_form')


    def clean_species(self):
        value = self.cleaned_data['species_name']
        return value.lower().strip()

    def clean_treatment_frequency(self):
        value = self.cleaned_data.get('treatment_frequency')
        allowed = [3, 4, 6, 12, 18, 24]
        if value not in allowed:
            raise forms.ValidationError(
                f"Invalid treatment frequency. Allowed values: {', '.join(map(str, allowed))} months."
            )
        return value


# herbicide form
class HerbicideForm(forms.ModelForm):
    class Meta:
        model = Herbicide
        exclude = ['user']
        # fields = ['herbicide']

# clearing norms form
class ClearingNormForm(forms.ModelForm):
    class Meta:
        model = ClearingNorm
        exclude = ['user', 'clearing_norm_set']

# clearing norm set form
class ClearingNormSetForm(forms.ModelForm):
    class Meta:
        model = ClearingNormSet
        exclude = ['user']


# category form
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'category_type', 'weight']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        # Add constraints to the weight field in the form
        self.fields['weight'].widget = forms.NumberInput(attrs={
            'min': '0', 'max': '1', 'step': '0.01'
        })
        self.fields['weight'].required = True

        if self.instance and self.instance.is_default:
            for field in self.fields:
                self.fields[field].disabled = True

    def clean_name(self):
        name = self.cleaned_data['name']
        name = name.lower().strip() # make lowercase
        qs = Category.objects.filter(user=self.user, name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("You already have a category with this name.")
        # Also prevent overriding same default twice:
        if Category.objects.filter(is_default=True, name=name).exists():
            # Allow override once
            if not self.instance.pk and Category.objects.filter(user=self.user, name=name).exists():
                raise ValidationError("You already override this default category.")
        return name

    def clean_weight(self):
        weight = self.cleaned_data.get('weight', Decimal('0.00'))
        if weight < Decimal('0.00') or weight > Decimal('1.00'):
            raise ValidationError("Weight must be between 0 and 1 inclusive.")
        return weight

    def clean_category_name(self):
        value = self.cleaned_data['name']
        return value.lower().strip()


    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.user = self.user
        obj.is_default = False
        if commit:
            obj.save()
        return obj

# numerical priority type form
class NumericPriorityBandForm(forms.ModelForm):
    class Meta:
        model = NumericPriorityBand
        fields = ['range_low', 'range_high', 'priority']

    def __init__(self, *args, **kwargs):
        # Pass in category from the view
        self.category = kwargs.pop('category', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        range_low = cleaned_data.get('range_low')
        range_high = cleaned_data.get('range_high')

        # Only validate if we have both values
        if range_low is not None and range_high is not None:
            # Check ascending order
            if range_low > range_high:
                self.add_error('range_high', _("Range high must be greater than range low."))

            # Check for overlaps only if category provided and no ordering errors
            if self.category and not self.errors:
                overlapping_bands = NumericPriorityBand.objects.filter(category=self.category)
                if self.instance.pk:
                    overlapping_bands = overlapping_bands.exclude(pk=self.instance.pk)

                for band in overlapping_bands:
                    if not (range_high < band.range_low or range_low > band.range_high):
                        raise ValidationError(
                            _("This range overlaps with existing range "
                              f"{band.range_low}–{band.range_high} (Priority {band.priority})")
                        )

        return cleaned_data

# text priority type form
class TextPriorityValueForm(forms.ModelForm):
    class Meta:
        model = TextPriorityValue
        fields = ['text_value', 'priority']

    def clean_text_value(self):
        value = self.cleaned_data['text_value']
        return value.lower().strip()


# costing model form
class CostingModelForm(forms.ModelForm):
    class Meta:
        model = CostingModel
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set defaults
        self.fields['initial_team_size'].initial = 1
        self.fields['initial_cost_per_day'].initial = 1
        self.fields['followup_team_size'].initial = 1
        self.fields['vehicle_cost_per_day'].initial = 1

    def clean_initial_team_size(self):
        value = self.cleaned_data['initial_team_size']
        if value <= 0:
            raise forms.ValidationError("Initial team size must be greater than 0.")
        return value

    def clean_initial_cost_per_day(self):
        value = self.cleaned_data['initial_cost_per_day']
        if value <= 0:
            raise forms.ValidationError("Initial cost per day must be greater than 0.")
        return value

    def clean_followup_team_size(self):
        value = self.cleaned_data['followup_team_size']
        if value <= 0:
            raise forms.ValidationError("Follow-up team size must be greater than 0.")
        return value

    def clean_vehicle_cost_per_day(self):
        value = self.cleaned_data['vehicle_cost_per_day']
        if value <= 0:
            raise forms.ValidationError("Vehicle cost per day must be greater than 0.")
        return value

# daily costing item form
class DailyCostItemForm(forms.ModelForm):
    class Meta:
        model = DailyCostItem
        exclude = ['user', 'costing_model']





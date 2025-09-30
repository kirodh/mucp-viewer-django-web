"""
MUCP TOOL
Author: Kirodh Boodhraj
"""
# project/forms.py
import os
from django import forms
from .models import Project
from django.core.exceptions import ValidationError


# project form
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        exclude = ['user', 'created_at']

    def clean(self):
        cleaned_data = super().clean()

        # Define file groups and required extensions
        shapefile_groups = {
            "Compartments": ['compartment_shp', 'compartment_shx', 'compartment_prj', 'compartment_dbf'],
            "GIS Mapping": ['gis_mapping_shp', 'gis_mapping_shx', 'gis_mapping_prj', 'gis_mapping_dbf'],
            "MIU": ['miu_shp', 'miu_shx', 'miu_prj', 'miu_dbf'],
            "NBAL": ['nbal_shp', 'nbal_shx', 'nbal_prj', 'nbal_dbf']
        }

        group_base_names = {}

        for group_name, fields in shapefile_groups.items():
            base_names = set()
            for field_name in fields:
                file = cleaned_data.get(field_name)
                if not file:
                    raise ValidationError(f"{group_name}: missing required file {field_name}")
                name_without_ext = os.path.splitext(file.name)[0]
                base_names.add(name_without_ext)

            # Check all four files in group have same base name
            if len(base_names) != 1:
                raise ValidationError(
                    f"{group_name}: all files must have the same base name, e.g. miu.shp, miu.shx, miu.prj, miu.dbf"
                )

            # Store base name to check for collisions between groups
            group_base_names[group_name] = base_names.pop()

        # Optional: enforce unique base names across groups
        seen_names = set()
        for group_name, base_name in group_base_names.items():
            if base_name in seen_names:
                raise ValidationError(
                    f"Base name '{base_name}' is used in multiple groups. Each group must have a unique base name.")
            seen_names.add(base_name)

        # Validate CSV/Excel files
        csv_file = cleaned_data.get('compartment_priorities_csv')
        if csv_file and not csv_file.name.lower().endswith('.csv'):
            self.add_error('compartment_priorities_csv', "Must be a .csv file")

        miu_excel = cleaned_data.get('miu_linked_species_excel')
        if miu_excel and not miu_excel.name.lower().endswith(('.xls', '.xlsx')):
            self.add_error('miu_linked_species_excel', "Must be an Excel file (.xls or .xlsx)")

        nbal_excel = cleaned_data.get('nbal_linked_species_excel')
        if nbal_excel and not nbal_excel.name.lower().endswith(('.xls', '.xlsx')):
            self.add_error('nbal_linked_species_excel', "Must be an Excel file (.xls or .xlsx)")

        return cleaned_data


"""
MUCP TOOL
Author: Kirodh Boodhraj
"""
# project/models.py
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ValidationError
import os

# Helper functions:
def project_directory_path(instance, filename):
    # Store files under media/projects/user_<id>/<project_name>/<filename>
    # Base path comes from settings
    return os.path.join(
        'projects',
        f'user_{instance.user.id}',
        instance.name,
        filename
    )

# Project model
class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    compartment_priorities_csv = models.FileField(upload_to=project_directory_path, blank=True, null=True)
    miu_linked_species_excel = models.FileField(upload_to=project_directory_path, blank=True, null=True)
    nbal_linked_species_excel = models.FileField(upload_to=project_directory_path, blank=True, null=True)

    # Compartments shapefile parts
    compartment_shp = models.FileField(upload_to=project_directory_path)
    compartment_shx = models.FileField(upload_to=project_directory_path)
    compartment_prj = models.FileField(upload_to=project_directory_path)
    compartment_dbf = models.FileField(upload_to=project_directory_path)

    # GIS mapping shapefile parts
    gis_mapping_shp = models.FileField(upload_to=project_directory_path)
    gis_mapping_shx = models.FileField(upload_to=project_directory_path)
    gis_mapping_prj = models.FileField(upload_to=project_directory_path)
    gis_mapping_dbf = models.FileField(upload_to=project_directory_path)

    # MIU shapefile parts
    miu_shp = models.FileField(upload_to=project_directory_path)
    miu_shx = models.FileField(upload_to=project_directory_path)
    miu_prj = models.FileField(upload_to=project_directory_path)
    miu_dbf = models.FileField(upload_to=project_directory_path)

    # NBAL shapefile parts
    nbal_shp = models.FileField(upload_to=project_directory_path)
    nbal_shx = models.FileField(upload_to=project_directory_path)
    nbal_prj = models.FileField(upload_to=project_directory_path)
    nbal_dbf = models.FileField(upload_to=project_directory_path)

    def clean(self):
        """Ensure all shapefile parts are present for each category."""
        required_groups = [
            ("Compartments", [self.compartment_shp, self.compartment_shx, self.compartment_prj, self.compartment_dbf]),
            ("GIS Mapping", [self.gis_mapping_shp, self.gis_mapping_shx, self.gis_mapping_prj, self.gis_mapping_dbf]),
            ("MIU", [self.miu_shp, self.miu_shx, self.miu_prj, self.miu_dbf]),
            ("NBAL", [self.nbal_shp, self.nbal_shx, self.nbal_prj, self.nbal_dbf]),
        ]

        for category, files in required_groups:
            if any(f is None for f in files):
                raise ValidationError(f"All files for {category} must be uploaded: .shp, .shx, .prj, .dbf")

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    class Meta:
        unique_together = ('user', 'name')
        ordering = ['-created_at']




"""
MUCP TOOL
Author: Kirodh Boodhraj
"""
# project/views.py
import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
import pandas as pd
import geopandas as gpd
import shutil
import json
from django.utils.safestring import mark_safe
from shapely.geometry import mapping
from django.http import JsonResponse, HttpResponseServerError

from .models import (
    Project
)
from .forms import ProjectForm

# project home view
def project_view(request):
    return render(request, 'project/project.html')


# project list view
@login_required
def project_list(request):
    projects = Project.objects.filter(user=request.user)
    return render(request, 'project/project_list.html', {'projects': projects})


# project create view
@login_required
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                project = form.save(commit=False)
                project.user = request.user
                project.save()
            except Exception as e:
                form.add_error(None, f"This project name already exists. {e}")
            else:
                return redirect('project:project_list')
    else:
        form = ProjectForm()

    return render(request, 'project/project_form.html', {'form': form})


# project details view
@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)

    # Load CSVs
    csv_df = pd.read_csv(project.compartment_priorities_csv.path)

    # Load Excel files
    miu_df = pd.read_excel(project.miu_linked_species_excel.path)
    nbal_df = pd.read_excel(project.nbal_linked_species_excel.path)

    # Load shapefiles (only attributes table)
    compartments_df = gpd.read_file(project.compartment_shp.path).drop(columns='geometry', errors='ignore')
    miu_shp_df = gpd.read_file(project.miu_shp.path).drop(columns='geometry', errors='ignore')
    nbal_shp_df = gpd.read_file(project.nbal_shp.path).drop(columns='geometry', errors='ignore')
    gis_mapping_df = gpd.read_file(project.gis_mapping_shp.path) #.drop(columns='geometry', errors='ignore')
    # Convert all column names to lowercase
    gis_mapping_df.columns = gis_mapping_df.columns.str.lower() # for consistency

    ### Convert geometries to GeoJSON for Leaflet
     # first clean
    if gis_mapping_df.crs != "EPSG:4326":
        gis_mapping_df = gis_mapping_df.to_crs(epsg=4326)

    # simplify geometry a bit
    bounds = gis_mapping_df.total_bounds  # [minx, miny, maxx, maxy]
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    extent = max(width, height)

    # e.g. simplify to ~1/5000 of map width
    tolerance = extent / 5000
    gis_mapping_df["geometry"] = gis_mapping_df["geometry"].buffer(0)  # fixes minor invalid polygons
    gis_mapping_df["geometry"] = gis_mapping_df["geometry"].simplify(tolerance=tolerance, preserve_topology=True)


    # Convert to GeoJSON-like dict
    features = []
    for _, row in gis_mapping_df.iterrows():
        # Combine the three fields into a single string for the name
        name_str = f"Compartment: {row['compt_id']}, MIU: {row['miu_id']}, NBAL: {row['nbal_id']}"
        features.append({
            "type": "Feature",
            "properties": {"name": name_str},
            # "geometry": json.loads(row["geometry"].to_json())
            "geometry": mapping(row["geometry"])
        })

    polygon_geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    # # Example GeoJSON (could be from shapefile processing)
    # polygon_geojson = {
    #     "type": "FeatureCollection",
    #     "features": [
    #         {
    #             "type": "Feature",
    #             "properties": {"name": "Polygon 1"},
    #             "geometry": {
    #                 "type": "Polygon",
    #                 "coordinates": [
    #                     [
    #                         [19.2, -33.9],
    #                         [19.21, -33.9],
    #                         [19.21, -33.91],
    #                         [19.2, -33.91],
    #                         [19.2, -33.9]
    #                     ]
    #                 ]
    #             }
    #         },
    #         {
    #             "type": "Feature",
    #             "properties": {"name": "Polygon 2"},
    #             "geometry": {
    #                 "type": "Polygon",
    #                 "coordinates": [
    #                     [
    #                         [19.22, -33.88],
    #                         [19.23, -33.88],
    #                         [19.23, -33.89],
    #                         [19.22, -33.89],
    #                         [19.22, -33.88]
    #                     ]
    #                 ]
    #             }
    #         },
    #         {
    #             "type": "Feature",
    #             "properties": {"name": "Polygon 3"},
    #             "geometry": {
    #                 "type": "Polygon",
    #                 "coordinates": [
    #                     [
    #                         [19.18, -33.92],
    #                         [19.19, -33.92],
    #                         [19.19, -33.93],
    #                         [19.18, -33.93],
    #                         [19.18, -33.92]
    #                     ]
    #                 ]
    #             }
    #         }
    #     ]
    # }

    # geometry to json end

    # Drop the geometry columns for efficiency
    gis_mapping_df = gis_mapping_df.drop(columns='geometry', errors='ignore')

    context = {
        'project': project,
        'csv_table': csv_df.to_html(classes='table table-striped', index=False),
        'miu_table': miu_df.to_html(classes='table table-striped', index=False),
        'nbal_table': nbal_df.to_html(classes='table table-striped', index=False),
        'compartments_table': compartments_df.to_html(classes='table table-striped', index=False),
        'miu_shp_table': miu_shp_df.to_html(classes='table table-striped', index=False),
        'nbal_shp_table': nbal_shp_df.to_html(classes='table table-striped', index=False),
        'gis_mapping_table': gis_mapping_df.to_html(classes='table table-striped', index=False),
        # GeoJSON for map
        'gis_mapping_geojson': json.dumps(polygon_geojson),
    }

    return render(request, 'project/project_detail.html', context)


# project delete view
@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)

    if request.method == 'POST':

        # Remove project folder if it exists and is empty
        try:
            # Assuming project_directory_path saves all files under the same folder per project
            project_folder = os.path.dirname(project.compartment_priorities_csv.path) if project.compartment_priorities_csv else None
            if project_folder and os.path.isdir(project_folder):
                shutil.rmtree(project_folder)
        except Exception:
            pass  # ignore if missing or not empty

        # Finally delete project record
        project.delete()

        return redirect('project:project_list')

    return render(request, 'project/project_confirm_delete.html', {'project': project})


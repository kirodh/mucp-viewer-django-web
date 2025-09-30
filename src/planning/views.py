"""
MUCP TOOL
Author: Kirodh Boodhraj
"""
import os
import geopandas as gpd
import pandas as pd
import random
import json
import math

from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.conf import settings
from django.utils.safestring import mark_safe

from .forms import PlanningForm, CostingAssignmentForm

from mucp_algorithms import data_reader, support_data_reader
from mucp_algorithms.algorithms.compartment_cost import calculate_budgets as mucp_calculate_budgets


from support.models import GrowthForm, TreatmentMethod, Species, Category
from planning.models import Planning, PlanningCostingMapping
from visualization.models import BudgetScenario, YearlyResult, SimulationRow, SimulationBudgetYear

# for plotting
def plot_me(costing, budgets):
    import matplotlib.pyplot as plt

    """
    Generate comparison plots for cost, flow, person days, and density across budgets and plans.
    Saves plots as PNG files instead of showing them interactively.
    """
    chart_data = {"cost": {}, "flow": {}, "person_days": {}, "density": {}}

    # Collect data
    for year, plans in budgets.items():
        chart_data["cost"][year] = {}
        chart_data["flow"][year] = {}
        chart_data["person_days"][year] = {}
        chart_data["density"][year] = {}

        for idx, plan in enumerate(["optimal", "plan_1", "plan_2", "plan_3", "plan_4"]):
            if year not in costing[idx]:
                continue
            df = costing[idx][year]

            # Drop NaN safely
            cost_vals = df["cost"].dropna()
            flow_vals = df["flow"].dropna()
            person_days_vals = df["person_days"].dropna()
            density_vals = df["density"].dropna()

            chart_data["cost"][year][plan] = cost_vals.sum() if not cost_vals.empty else 0
            chart_data["flow"][year][plan] = flow_vals.sum() if not flow_vals.empty else 0
            chart_data["person_days"][year][plan] = person_days_vals.sum() if not person_days_vals.empty else 0
            chart_data["density"][year][plan] = density_vals.mean() if not density_vals.empty else 0

    # Convert to DataFrames for easier plotting
    cost_df = pd.DataFrame(chart_data["cost"]).T
    flow_df = pd.DataFrame(chart_data["flow"]).T
    person_days_df = pd.DataFrame(chart_data["person_days"]).T
    density_df = pd.DataFrame(chart_data["density"]).T

    # Plotting helper
    def plot_and_save(df, title, ylabel, filename):
        plt.figure(figsize=(10, 6))
        df.plot(marker="o")
        plt.title(title)
        plt.ylabel(ylabel)
        plt.xlabel("Year")
        plt.legend(title="Plan")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(filename)
        plt.close()

    # Generate and save all plots
    plot_and_save(cost_df, "Yearly Cost Comparison", "Total Cost", "cost_plot.png")
    plot_and_save(flow_df, "Yearly Flow Comparison", "Total Flow", "flow_plot.png")
    plot_and_save(person_days_df, "Yearly Person Days Comparison", "Total Person Days", "person_days_plot.png")
    plot_and_save(density_df, "Yearly Density Comparison (Mean)", "Mean Density", "density_plot.png")

    return cost_df, flow_df, person_days_df, density_df



# helper functions:
def is_data_valid(validation_result: dict) -> bool:
    """Check if validation result has no errors or warnings."""
    return not validation_result.get("errors")

# Ensure absolute path
def get_absolute_media_path(relative_path: str) -> str:
    return os.path.join(settings.MEDIA_ROOT, relative_path)

def planning_view(request):
    return render(request, 'planning/planning.html')


# create planning view
@login_required
def planning_create(request):
    if request.method == "POST":
        # form = PlanningForm(request.POST)
        form = PlanningForm(request.POST, user=request.user)  # pass user
        if form.is_valid():
            planning = form.save(commit=False)
            planning.user = request.user
            planning.save()

            form.save(commit=True)  # This will now run your category logic

            messages.success(request, "Planning created successfully.")
            return redirect("planning:planning_list")
        else:
            # Print errors in console for debugging
            messages.error(request, str(form.errors.as_json()))  # JSON format for readability
    else:
        form = PlanningForm(user=request.user)  # pass user here too
    return render(request, "planning/planning_form.html", {"form": form})


# planning list view
@login_required
def planning_list(request):
    plannings_qs = Planning.objects.filter(
        user=request.user  # only show current user's plannings
    ).select_related(
        "project", "clearing_norm_model"
    ).prefetch_related(
        "planning_categories__category"
    ).order_by("-created_at")

    # Pagination: 20 per page
    paginator = Paginator(plannings_qs, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    return render(request, "planning/planning_list.html", {
        "page_obj": page_obj,
        "plannings": page_obj.object_list
    })

# planning details view
@login_required
def planning_detail(request, pk):
    planning = get_object_or_404(Planning, pk=pk)

    context = {
        "planning": planning,
        "has_complete_mapping": planning.has_complete_costing_mapping,
    }
    return render(request, "planning/planning_detail.html", context)


# planning delete view
@login_required
def planning_delete(request, pk):
    planning = get_object_or_404(Planning, pk=pk)
    if request.method == "POST":
        planning.delete()
        messages.success(request, "Planning deleted successfully.")
        return redirect("planning:planning_list")
    return render(request, "planning/planning_confirm_delete.html", {"planning": planning})


# planning validation view
@login_required
def planning_validation(request, pk):
    planning = get_object_or_404(Planning, pk=pk)
    project = planning.project

    ## check if there already exist budgets for the planning
    # If this planning already has results → redirect straight away
    if (
            planning.budget_years.exists()
            or planning.budgets.exists()
    ):
        return redirect("visualization:visualization_view")


    # -----------------------------
    # 0. Validate file existence and readability
    # -----------------------------
    ## User files
    # GIS MAPPING
    gis_mapping_path = get_absolute_media_path(str(project.gis_mapping_shp))
    gis_mapping_validations = data_reader.read_gis_mapping_shapefile(gis_mapping_path, validate=True, headers_required = ["nbal_id", "miu_id", "compt_id","area"], headers_other = ["geometry"])
    if is_data_valid(gis_mapping_validations):
        gis_mapping_data = data_reader.read_gis_mapping_shapefile(gis_mapping_path, validate=False, headers_required=["nbal_id", "miu_id", "compt_id", "area"], headers_other=["geometry"])
    else:
        gis_mapping_data = gpd.GeoDataFrame(columns=["nbal_id", "miu_id", "compt_id", "area", "geometry"], geometry="geometry", crs="EPSG:4326")

    # MIU
    miu_path = get_absolute_media_path(str(project.miu_shp))
    miu_validations = data_reader.read_miu_shapefile(miu_path, gis_mapping_data["miu_id"].tolist(), validate=True, headers_required = ["miu_id", "area", "riparian_c"], headers_other = ["geometry"])
    if is_data_valid(miu_validations):
        miu_data = data_reader.read_miu_shapefile(miu_path, gis_mapping_data["miu_id"].tolist(), validate=False, headers_required=["miu_id", "area", "riparian_c"], headers_other=["geometry"])
    else:
        miu_data = gpd.GeoDataFrame(columns=["miu_id", "area", "riparian_c", "geometry"], geometry="geometry", crs="EPSG:4326")

    # NBAL
    nbal_path = get_absolute_media_path(str(project.nbal_shp))
    nbal_validations = data_reader.read_nbal_shapefile(nbal_path, gis_mapping_data["nbal_id"].tolist(), validate=True, headers_required = ["nbal_id", "area", "stage"], headers_other = ["geometry", "contractid", "first_date", "last_date"])
    if is_data_valid(nbal_validations):
        nbal_data = data_reader.read_nbal_shapefile(nbal_path, gis_mapping_data["nbal_id"].tolist(), validate=False, headers_required=["nbal_id", "area", "stage"], headers_other=["geometry", "contractid", "first_date", "last_date"])
    else:
        nbal_data = gpd.GeoDataFrame(columns=["nbal_id", "area", "stage", "geometry"], geometry="geometry", crs="EPSG:4326")

    # COMPARTMENT
    compartment_path = get_absolute_media_path(str(project.compartment_shp))
    compartment_validations = data_reader.read_compartment_shapefile(compartment_path, gis_mapping_data["compt_id"].tolist(), validate=True, headers_required = ["compt_id", "area_ha", "slope","walk_time","drive_time","costing","grow_con"], headers_other = ["geometry", "terrain"])
    if is_data_valid(compartment_validations):
        compartment_data = data_reader.read_compartment_shapefile(compartment_path, gis_mapping_data["compt_id"].tolist(), validate=False, headers_required=["compt_id", "area_ha", "slope", "walk_time", "drive_time", "costing", "grow_con"], headers_other=["geometry", "terrain"])
    else:
        compartment_data = gpd.GeoDataFrame(columns=["compt_id", "area_ha", "slope", "walk_time", "drive_time", "costing", "grow_con", "geometry"], geometry="geometry", crs="EPSG:4326")

    # MIU LINKED SPECIES
    miu_linked_species_path = get_absolute_media_path(str(project.miu_linked_species_excel))
    miu_linked_species_validations = data_reader.read_miu_linked_species_excel(miu_linked_species_path, validate=True, headers_required=["miu_id", "species", "idenscode", "age"])
    if is_data_valid(miu_linked_species_validations):
        miu_linked_species_data = data_reader.read_miu_linked_species_excel(miu_linked_species_path, validate=False, headers_required=["miu_id", "species", "idenscode", "age"])
    else:
        miu_linked_species_data = pd.DataFrame(columns=["miu_id", "species", "idenscode", "age"])

    # NBAL LINKED SPECIES
    nbal_linked_species_path = get_absolute_media_path(str(project.nbal_linked_species_excel))
    nbal_linked_species_validations = data_reader.read_nbal_linked_species_excel(nbal_linked_species_path, validate=True, headers_required=["nbal_id", "species", "idenscode", "age"])
    if is_data_valid(nbal_linked_species_validations):
        nbal_linked_species_data = data_reader.read_nbal_linked_species_excel(nbal_linked_species_path, validate=False, headers_required=["nbal_id", "species", "idenscode", "age"])
    else:
        nbal_linked_species_data = pd.DataFrame(columns=["nbal_id", "species", "idenscode", "age"])

    # COMPARTMENT PRIORITIES
    compartment_priorities_path = get_absolute_media_path(str(project.compartment_priorities_csv))
    compartment_priorities_validations = data_reader.read_compartment_priorities_csv(compartment_priorities_path, validate=True, headers_required=["compt_id"])
    if is_data_valid(compartment_priorities_validations):
        compartment_priorities_data = data_reader.read_compartment_priorities_csv(compartment_priorities_path, validate=False, headers_required=["compt_id"])
    else:
        compartment_priorities_data = pd.DataFrame(columns=["compt_id"])

    # # -----------------------------
    # # 2. Get and validate user support data
    # # -----------------------------
    ## User support data from viewer
    # get the support data
    #--- growth form
    growth_forms = GrowthForm.objects.filter(
        Q(user=request.user) | Q(user__isnull=True)
    ).values_list("growth_form", flat=True).distinct()
    growth_forms = list(growth_forms)

    #--- treatment method
    treatment_method = TreatmentMethod.objects.filter(
        Q(user=request.user) | Q(user__isnull=True)
    ).values_list("treatment_method", flat=True).distinct()
    treatment_method = list(treatment_method)

    #--- species
    # 1. User species
    user_species_qs = Species.objects.filter(user=request.user).select_related("growth_form").prefetch_related("treatment_methods")

    # 2. Default species not overridden by user
    default_species_qs = Species.objects.filter(
        user__isnull=True
    ).exclude(
        species_name__in=user_species_qs.values_list("species_name", flat=True)
    ).select_related("growth_form").prefetch_related("treatment_methods")

    # 3. Merge
    species_qs = user_species_qs.union(default_species_qs)

    species = pd.DataFrame.from_records(species_qs.values())

    # 1) Rename the FK column
    species.rename(columns={"growth_form_id": "growth_form"}, inplace=True)

    # 2) Build an ID->name lookup from the ORM
    gf_lookup = dict(GrowthForm.objects.values_list("id", "growth_form"))

    # 3) Replace IDs with the actual growth_form text using a lambda
    species["growth_form"] = species["growth_form"].apply(
        lambda v: gf_lookup.get(int(v)) if pd.notna(v) and str(v).strip() != "" else None
    )


    #--- herbicides (not in algorithms yet)

    #--- clearing norms
    # clearing_norms_models = planning.clearing_norm_model.norms.all()
    # Example: flatten related fields
    qs = planning.clearing_norm_model.norms.all().values(
        "id",
        "clearing_norm_set",
        "growth_form__growth_form",  # FK to GrowthForm
        "treatment_method__treatment_method",  # FK to TreatmentMethod
        "density",
        "ppd",
        "terrain",
        "size_class",
        "process",
    )

    # Convert to DataFrame
    clearing_norms = pd.DataFrame.from_records(qs)
    clearing_norms.rename(columns={"growth_form__growth_form": "growth_form","treatment_method__treatment_method": "treatment_method"}, inplace=True)



    #--- prioritization model
    categories_qs = Category.objects.filter(
        planningcategory__planning=planning
    ).prefetch_related("numeric_bands", "text_values")
    # flatten so we dont use django queries in the data reader, makes for uniform data structures
    categories = []
    for cat in categories_qs:
        if cat.category_type == "numeric":
            categories.append({
                "name": cat.name,
                "weight": cat.weight,
                "type": "numeric",
                "ranges": [(b.range_low, b.range_high, b.priority) for b in cat.numeric_bands.all()],
            })
        elif cat.category_type == "text":
            categories.append({
                "name": cat.name,
                "weight": cat.weight,
                "type": "text",
                "allowed": [{"value": v.text_value, "priority": v.priority} for v in cat.text_values.all()],
            })


    # open and validate all the support data here
    # growth form validate (use list (growth_form) above for data)
    growth_forms_validations = support_data_reader.read_growth_form(growth_forms,clearing_norms["growth_form"].tolist(), species["growth_form"].tolist(), validate=True)

    # treatment method validate (use list (treatment_method) above for data)
    treatment_methods_validations = support_data_reader.read_treatment_methods(treatment_method,clearing_norms["treatment_method"].tolist(), validate=True)

    # species validate and data
    species_validations = support_data_reader.read_species(species,miu_linked_species_data["species"].tolist(), nbal_linked_species_data["species"].tolist(), validate=True)
    if is_data_valid(species_validations):
        species = support_data_reader.read_species(species,miu_linked_species_data["species"].tolist(), nbal_linked_species_data["species"].tolist(), validate=False)


    # clearing norms validate and data
    clearing_norms_validations = support_data_reader.read_clearing_norms(clearing_norms, miu_linked_species_data["age"].tolist(), nbal_linked_species_data["age"].tolist(), species["growth_form"].tolist(), validate=True)
    if is_data_valid(clearing_norms_validations):
        clearing_norms_df = support_data_reader.read_clearing_norms(clearing_norms, miu_linked_species_data["age"].tolist(), nbal_linked_species_data["age"].tolist(), species["growth_form"].tolist(), validate=False)

    prioritization_model_validations = support_data_reader.read_prioritization_categories(compartment_priorities_data, categories, validate=True, headers_required=["compt_id"])
    if is_data_valid(prioritization_model_validations):
        prioritization_model_data = support_data_reader.read_prioritization_categories(compartment_priorities_data, categories, validate=False, headers_required=["compt_id"])
    else:
        prioritization_model_data = None


    # --- costing model (after the form)
    existing_mappings = PlanningCostingMapping.objects.filter(planning=planning)
    # mappings that are for the cost model to the options in the compartment shp
    costing_model_mappings = {m.costing_value: m.costing_model for m in existing_mappings}
    # use the following with the mucp engine as it doesnt understand the query objects but only names
    costing_model_mappings_mucp_use = {int(m.costing_value): m.costing_model.name for m in existing_mappings}
    # int needed because it used it as string so the cost didnt go through to the algorithms and merge properly into the master df, all nans basically

    # Build records for DataFrame
    records = []
    for pk, obj in costing_model_mappings.items():
        records.append({
            # "id": obj.id,
            "Costing Model Name": obj.name,
            "Initial Team Size": obj.initial_team_size,
            "Initial Cost/Day": obj.initial_cost_per_day,
            "Follow-up Team Size": obj.followup_team_size,
            "Follow-up Cost/Day": obj.followup_cost_per_day,
            "Vehicle Cost/Day": obj.vehicle_cost_per_day,
            "Fuel Cost/Hour": obj.fuel_cost_per_hour,
            "Maintenance Level": obj.maintenance_level,
            "Cost/Day": obj.total_cost_per_day,  # uses your property
        })

    costing_before_validation = pd.DataFrame(records)
    costing_validations = support_data_reader.read_costing_model(costing_before_validation, required_headers = ["Costing Model Name","Initial Team Size","Initial Cost/Day", "Follow-up Team Size","Follow-up Cost/Day","Vehicle Cost/Day", "Fuel Cost/Hour","Maintenance Level","Cost/Day"],validate = True)
    if is_data_valid(costing_validations):
        costing_data = support_data_reader.read_costing_model(costing_before_validation, required_headers = ["Costing Model Name","Initial Team Size","Initial Cost/Day", "Follow-up Team Size","Follow-up Cost/Day","Vehicle Cost/Day", "Fuel Cost/Hour","Maintenance Level","Cost/Day"],validate = False)
    else:
        costing_data = None

    planning_validations = support_data_reader.read_planning_variables(planning.budget_plan_1, planning.budget_plan_2, planning.budget_plan_3, planning.budget_plan_4, planning.escalation_plan_1, planning.escalation_plan_2, planning.escalation_plan_3, planning.escalation_plan_4,planning.standard_working_day, planning.standard_working_year_days, planning.start_year, planning.years_to_run, planning.currency, planning.save_results,validate = True)
    if is_data_valid(planning_validations):
        planning_budget_plan_1, planning_budget_plan_2, planning_budget_plan_3, planning_budget_plan_4, planning_escalation_plan_1, planning_escalation_plan_2, planning_escalation_plan_3, planning_escalation_plan_4, planning_standard_working_day, planning_standard_working_year_days, planning_start_year, planning_years_to_run, planning_currency, planning_save_results = support_data_reader.read_planning_variables(planning.budget_plan_1, planning.budget_plan_2, planning.budget_plan_3, planning.budget_plan_4, planning.escalation_plan_1, planning.escalation_plan_2, planning.escalation_plan_3, planning.escalation_plan_4, planning.standard_working_day, planning.standard_working_year_days, planning.start_year, planning.years_to_run, planning.currency, planning.save_results, validate = False)
    else:
        planning_budget_plan_1 = None
        planning_budget_plan_2 = None
        planning_budget_plan_3 = None
        planning_budget_plan_4 = None
        planning_escalation_plan_1 = None
        planning_escalation_plan_2 = None
        planning_escalation_plan_3 = None
        planning_escalation_plan_4 = None
        planning_standard_working_day = None
        planning_standard_working_year_days = None
        planning_start_year = None
        planning_years_to_run = None
        planning_currency = None
        planning_save_results = None


    # print("gis_mapping_data:")
    # print(gis_mapping_data)
    # print(gis_mapping_data.columns)
    # print(gis_mapping_data.iloc[0])
    # print("\n")
    # print("miu_data:")
    # print(miu_data)
    # print(miu_data.columns)
    # print(miu_data.iloc[0])
    # print("\n")
    # print("nbal_data:")
    # print(nbal_data)
    # print(nbal_data.columns)
    # print(nbal_data.iloc[0])
    # print("\n")
    # print("compartment_data:")
    # print(compartment_data)
    # print(compartment_data.columns)
    # print(compartment_data.iloc[0])
    # print("\n")
    # print("miu_linked_species_data:")
    # print(miu_linked_species_data)
    # print(miu_linked_species_data.columns)
    # print(miu_linked_species_data.iloc[0])
    # print("\n")
    # print("nbal_linked_species_data:")
    # print(nbal_linked_species_data)
    # print(nbal_linked_species_data.columns)
    # print(nbal_linked_species_data.iloc[0])
    # print("\n")
    # print("compartment_priorities_data:")
    # print(compartment_priorities_data)
    # print(compartment_priorities_data.columns)
    # print(compartment_priorities_data.iloc[0])
    # print("\n")
    # print("growth_forms:")
    # print(growth_forms)
    # print("\n")
    # print("treatment_method:")
    # print(treatment_method)
    # print("\n")
    # print("clearing_norms:")
    # print(clearing_norms)
    # print(clearing_norms.columns)
    # print(clearing_norms.iloc[0])
    # print("\n")
    # print("species:")
    # print(species)
    # print(species.columns)
    # print(species.iloc[0])
    # print("\n")
    # print("clearing_norms_df:")
    # print(clearing_norms_df)
    # print("\n")
    # print("prioritization_model_data:")
    # print(prioritization_model_data)
    # print(prioritization_model_data.columns)
    # print(prioritization_model_data.iloc[0])
    # print("\n")
    # print("costing_data:")
    # print(costing_data)
    # print(costing_data.columns)
    # print(costing_data.iloc[0])
    # print("\n")
    # print("planning_budget_plan_1:")
    # print(planning_budget_plan_1)
    # print("\n")
    # print("planning_budget_plan_2:")
    # print(planning_budget_plan_2)
    # print("\n")
    # print("planning_budget_plan_3:")
    # print(planning_budget_plan_3)
    # print("\n")
    # print("planning_budget_plan_4:")
    # print(planning_budget_plan_4)
    # print("\n")
    # print("planning_escalation_plan_1:")
    # print(planning_escalation_plan_1)
    # print("\n")
    # print("planning_escalation_plan_2:")
    # print(planning_escalation_plan_2)
    # print("\n")
    # print("planning_escalation_plan_3:")
    # print(planning_escalation_plan_3)
    # print("\n")
    # print("planning_escalation_plan_4:")
    # print(planning_escalation_plan_4)
    # print("\n")
    # print("planning_standard_working_day:")
    # print(planning_standard_working_day)
    # print("\n")
    # print("planning_standard_working_year_days:")
    # print(planning_standard_working_year_days)
    # print("\n")
    # print("planning_start_year:")
    # print(planning_start_year)
    # print("\n")
    # print("planning_years_to_run:")
    # print(planning_years_to_run)
    # print("\n")
    # print("planning_currency:")
    # print(planning_currency)
    # print("\n")
    # print("planning_save_results:")
    # print(planning_save_results)
    # print("\n")
    # print("costing_model_mappings:")
    # print(costing_model_mappings)
    # print(costing_model_mappings_mucp_use) # use this for mucp tool
    # print("\n")
    # print("categories:")
    # print(categories)
    # print("\n")


    # # -----------------------------
    # # 4. Check if simulation should run
    # # -----------------------------
    simulation_status = None

    if request.method == "POST" and request.POST.get("run_simulation") == "1":
        try:
            results, budgets = mucp_calculate_budgets(gis_mapping_data,miu_data, nbal_data, compartment_data, miu_linked_species_data, nbal_linked_species_data,compartment_priorities_data, growth_forms, treatment_method, clearing_norms_df, species, costing_data, planning_budget_plan_1, planning_budget_plan_2, planning_budget_plan_3, planning_budget_plan_4, planning_escalation_plan_1, planning_escalation_plan_2, planning_escalation_plan_3, planning_escalation_plan_4, planning_standard_working_day, planning_standard_working_year_days, planning_start_year, planning_years_to_run, planning_currency, planning_save_results, costing_model_mappings_mucp_use, categories, prioritization_model_data)
            # print("Simulation ran!")
            # print("budgets")
            # print(budgets)
            # print("results")
            # print(results)
            # plot_me(results, budgets)
            # print(results[0][2025].dtypes)
            # print(results[0][2025].iloc[0])

            if planning_save_results:
                with transaction.atomic():
                    # --- Save yearly propagated budgets ---
                    for year, budget_values in budgets.items():
                        SimulationBudgetYear.objects.update_or_create(
                            planning=planning,
                            year=year,
                            defaults={
                                "plan_1": budget_values.get("plan_1", 0),
                                "plan_2": budget_values.get("plan_2", 0),
                                "plan_3": budget_values.get("plan_3", 0),
                                "plan_4": budget_values.get("plan_4", 0),
                            },
                        )

                    # --- Save yearly simulation rows ---
                    SCENARIO_ORDER = ["optimal", "budget_1", "budget_2", "budget_3", "budget_4"]

                    for scenario_idx, scenario_data in enumerate(results):
                        scenario_name = SCENARIO_ORDER[scenario_idx]  # map list index to scenario name

                        for year, year_rows in scenario_data.items():
                            # BudgetScenario + YearlyResult are lightweight, fine with get_or_create
                            budget_scenario, _ = BudgetScenario.objects.get_or_create(
                                planning=planning,
                                name=scenario_name,
                            )
                            yearly_result, _ = YearlyResult.objects.get_or_create(
                                budget=budget_scenario,
                                year=year,
                            )

                            # --- Collect SimulationRows ---
                            row_objects = []
                            for row in year_rows.itertuples(index=False):
                                # print(row.compt_id,row.miu_id,row.nbal_id)
                                row_objects.append(
                                    SimulationRow(
                                        yearly_result=yearly_result,
                                        person_days=row.person_days,
                                        cost=None if pd.isna(row.cost) else row.cost, # production
                                        # cost=random.randint(0, 1000), # test
                                        density=row.density,
                                        flow=row.flow,
                                        priority=getattr(row, "priority", None),
                                        cleared_now=bool(getattr(row, "cleared_now", False)),
                                        cleared_fully=bool(getattr(row, "cleared_fully", False)),
                                        nbal_id=row.nbal_id,
                                        miu_id=row.miu_id,
                                        compt_id=row.compt_id,
                                    )
                                )

                            # --- Bulk insert in one query ---
                            SimulationRow.objects.bulk_create(row_objects, batch_size=1000)

                return redirect("visualization:visualization_selector")
            else:

                def prepare_chart_data_from_dfs(results):
                    """
                    Aggregate results from DataFrames for plotting:
                    - density: average, skip zeros and NaNs
                    - flow: sum, skip NaNs
                    - person_days: sum, skip NaNs
                    - cost: sum, NaN -> 0
                    """
                    chart_data = {
                        "density": {},
                        "flow": {},
                        "person_days": {},
                        "cost": {}
                    }

                    # Collect all years and plans
                    years = sorted({year for result in results for year in result.keys()})
                    plans = ["optimal", "plan_1", "plan_2", "plan_3", "plan_4"]

                    # Initialize chart data
                    for metric in chart_data.keys():
                        chart_data[metric] = {year: {plan: 0 for plan in plans} for year in years}

                    # Iterate over plans and years
                    for plan_index, result in enumerate(results):  # each result: {year: df}
                        plan = plans[plan_index]

                        for year, df in result.items():  # df = DataFrame
                            if df.empty:
                                continue

                            # Density: average of non-zero, non-NaN
                            density_vals = df["density"][(df["density"] != 0) & (df["density"].notna())]
                            chart_data["density"][year][plan] = density_vals.mean() if not density_vals.empty else 0

                            # Flow: sum, skip NaN
                            chart_data["flow"][year][plan] = df["flow"].sum(skipna=True)

                            # Person days: sum, skip NaN
                            chart_data["person_days"][year][plan] = df["person_days"].sum(skipna=True)

                            # Cost: sum, replace NaN with 0
                            chart_data["cost"][year][plan] = df["cost"].fillna(0).sum()

                    return chart_data, years, plans

                # results_serialized = serialize_results(results)
                chart_data, years, plans = prepare_chart_data_from_dfs(results)

                return render(request, "visualization/view_not_saved.html", {
                    "planning": planning,
                    "currency": planning_currency,
                    "chart_data_json": mark_safe(json.dumps(chart_data)),
                    "years_json": mark_safe(json.dumps(years)),
                    "plans_json": mark_safe(json.dumps(plans)),
                })

        except Exception as e:
            # Log to console for debugging
            # print("Error in view:", e)

            # Show a message to the user on the page
            messages.error(request, f"An error occurred while generating the results: {e}")



    context = {
        "planning": planning,
        # validations for user files
        "miu_errors": miu_validations["errors"],
        "miu_warnings": miu_validations["warnings"],
        "nbal_errors": nbal_validations["errors"],
        "nbal_warnings": nbal_validations["warnings"],
        "compartment_errors": compartment_validations["errors"],
        "compartment_warnings": compartment_validations["warnings"],
        "gis_mapping_errors": gis_mapping_validations["errors"],
        "gis_mapping_warnings": gis_mapping_validations["warnings"],
        "miu_linked_species_errors": miu_linked_species_validations["errors"],
        "miu_linked_species_warnings": miu_linked_species_validations["warnings"],
        "nbal_linked_species_errors": nbal_linked_species_validations["errors"],
        "nbal_linked_species_warnings": nbal_linked_species_validations["warnings"],
        "compartment_priorities_errors": compartment_priorities_validations["errors"],
        "compartment_priorities_warnings": compartment_priorities_validations["warnings"],
        # validations for support data
        "growth_forms_errors": growth_forms_validations["errors"],
        "growth_forms_warnings": growth_forms_validations["warnings"],
        "treatment_methods_errors": treatment_methods_validations["errors"],
        "treatment_methods_warnings": treatment_methods_validations["warnings"],
        "species_errors": species_validations["errors"],
        "species_warnings": species_validations["warnings"],
        "clearing_norms_errors": clearing_norms_validations["errors"],
        "clearing_norms_warnings": clearing_norms_validations["warnings"],
        "prioritization_model_errors": prioritization_model_validations["errors"],
        "prioritization_model_warnings": prioritization_model_validations["warnings"],
        "costing_errors": costing_validations["errors"],
        "costing_warnings": costing_validations["warnings"],
        "planning_errors": planning_validations["errors"],
        "planning_warnings": planning_validations["warnings"],
        # simulation
        "simulation_status": simulation_status
    }
    return render(request, "planning/planning_validation.html", context)


# cost mapping to planning view
@login_required
def define_costing_mapping(request, pk):
    planning = get_object_or_404(Planning, id=pk)

    # Get the unique values required for this planning
    try:
        # GIS MAPPING
        gis_mapping_path = get_absolute_media_path(str(planning.project.gis_mapping_shp))
        gis_mapping_validations = data_reader.read_gis_mapping_shapefile(gis_mapping_path, validate=True, headers_required=["nbal_id", "miu_id", "compt_id", "area"], headers_other=["geometry"])
        if is_data_valid(gis_mapping_validations):
            gis_mapping_data = data_reader.read_gis_mapping_shapefile(gis_mapping_path, validate=False, headers_required=["nbal_id", "miu_id", "compt_id", "area"], headers_other=["geometry"])
        else:
            gis_mapping_data = gpd.GeoDataFrame(columns=["nbal_id", "miu_id", "compt_id", "area", "geometry"], geometry="geometry", crs="EPSG:4326")

        # COMPARTMENT
        compartment_path = get_absolute_media_path(str(planning.project.compartment_shp))
        compartment_validations = data_reader.read_compartment_shapefile(compartment_path, gis_mapping_data["compt_id"].tolist(), validate=True, headers_required = ["compt_id", "area_ha", "slope","walk_time","drive_time","costing","grow_con"], headers_other = ["geometry", "terrain"])

        if is_data_valid(compartment_validations):
            compartment_data = data_reader.read_compartment_shapefile(compartment_path, gis_mapping_data["compt_id"].tolist(), validate=False, headers_required=["compt_id", "area_ha", "slope", "walk_time", "drive_time", "costing", "grow_con"], headers_other=["geometry", "terrain"])
        unique_costing_values = compartment_data["costing"].dropna().unique().tolist()
    except Exception as e:
        unique_costing_values = []
        messages.error(request, "Error: "+str(e))

    # Pre-populate with existing mappings
    existing_map = {
        cm.costing_value: cm.costing_model_id
        for cm in planning.costing_mappings.all()
    }

    if request.method == "POST":
        form = CostingAssignmentForm(
            request.POST,
            costing_values=unique_costing_values,
            initial=existing_map
        )
        if form.is_valid():
            # Save/update mappings
            for val in unique_costing_values:
                costing_model = form.cleaned_data[f"costing_{val}"]
                PlanningCostingMapping.objects.update_or_create(
                    planning=planning,
                    costing_value=val,
                    defaults={"costing_model": costing_model},
                )
            return redirect("planning:planning_detail", pk=planning.id)

    else:
        form = CostingAssignmentForm(
            costing_values=unique_costing_values,
            initial={
                f"costing_{val}": existing_map.get(val)
                for val in unique_costing_values
            }
        )

    return render(
        request,
        "planning/define_costing_mapping.html",
        {"form": form, "planning": planning},
    )
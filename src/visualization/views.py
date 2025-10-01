"""
MUCP TOOL
Author: Kirodh Boodhraj
"""
import os
import matplotlib
matplotlib.use("Agg")  # Use non-GUI backend
import io
import json
import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping
from fpdf import FPDF
import matplotlib.pyplot as plt

from django.contrib.staticfiles import finders
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string

from planning.models import Planning
from .models import BudgetScenario, YearlyResult, SimulationRow, SimulationBudgetYear



# visualization home view
def visualization_home(request):
    return render(request, 'visualization/visualization.html')


# --- Step 1: Selector page ---
# visualization selector view
@login_required
def visualization_selector(request):
    plannings = Planning.objects.filter(user=request.user, save_results=True).order_by('-created_at')  # latest first
    return render(request, "visualization/selector.html", {"plannings": plannings})


# --- Step 2: Main visualization view ---
# visualization results view
@login_required
def visualization_view(request, planning_id):
    planning = get_object_or_404(Planning, id=planning_id, user=request.user)

    # Pass available years + budgets for this planning
    budgets = BudgetScenario.objects.filter(planning=planning).values_list("name", flat=True).distinct()
    years = YearlyResult.objects.filter(budget__planning=planning).values_list("year", flat=True).distinct()

    return render(request, "visualization/view.html", {
        "planning": planning,
        "budgets": budgets,
        "years": sorted(years),
        "currency": planning.currency,  # pass currency
    })

# map data view
@login_required
def map_data(request, planning_id):
    planning = get_object_or_404(Planning, id=planning_id, user=request.user)
    project = planning.project  # <-- this gets the related Project instance

    # helper functions:
    def normalize(v):
        return str(v).lower().strip() if v not in (None, "", "nan") else None

    try:
        # --- FILTERS from request ---
        year = request.GET.get("year")
        budget_name = request.GET.get("budget")
    except Exception as e:
        pass

    # find budget + yearly result
    budget = BudgetScenario.objects.filter(planning=planning, name=budget_name).first()
    yearly_result = None
    if budget and year:
        yearly_result = YearlyResult.objects.filter(budget=budget, year=year).first()

    # preload simulation rows into dict for fast lookup
    sim_lookup = {}
    if yearly_result:
        rows = SimulationRow.objects.filter(yearly_result=yearly_result).values(
            "compt_id", "miu_id", "nbal_id",
            "priority", "person_days", "cost", "density", "flow",
            "cleared_now", "cleared_fully"
        )
        for r in rows:
            key = (normalize(r["compt_id"]), normalize(r["miu_id"]), normalize(r["nbal_id"]))
            # print(key)
            # key = (r["compt_id"], r["miu_id"], r["nbal_id"])
            sim_lookup[key] = r


    # --- SHAPEFILE ---
    # shapefile data:
    gis_mapping_df = gpd.read_file(project.gis_mapping_shp.path)  # .drop(columns='geometry', errors='ignore')
    # Convert all column names to lowercase
    gis_mapping_df.columns = gis_mapping_df.columns.str.lower()  # for consistency
    # Convert all string data in the DataFrame to lowercase
    for col in gis_mapping_df.select_dtypes(include=['object']).columns:
        gis_mapping_df[col] = gis_mapping_df[col].str.lower()

    if gis_mapping_df.crs != "EPSG:4326":
        gis_mapping_df = gis_mapping_df.to_crs(epsg=4326)

    # simplify geometry a bit
    bounds = gis_mapping_df.total_bounds  # [minx, miny, maxx, maxy]
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    extent = max(width, height)

    # e.g. simplify to ~1/5000 of map width
    tolerance = extent / 5000
    gis_mapping_df["geometry"] = gis_mapping_df["geometry"].buffer(0)
    gis_mapping_df["geometry"] = gis_mapping_df["geometry"].simplify(tolerance=tolerance, preserve_topology=True)


    ### Convert geometries to GeoJSON for Leaflet
    # first clean
    if gis_mapping_df.crs != "EPSG:4326":
        gis_mapping_df = gis_mapping_df.to_crs(epsg=4326)

    gis_mapping_df["geometry"] = gis_mapping_df["geometry"].buffer(0)  # fixes minor invalid polygons

    # Convert to GeoJSON-like dict
    features = []
    for _, row in gis_mapping_df.iterrows():
        comp = normalize(row.get("compt_id"))
        miu = normalize(row.get("miu_id"))
        nbal = normalize(row.get("nbal_id"))

        # progressively try more general keys
        sim_data = (
                sim_lookup.get((comp, miu, nbal)) or
                sim_lookup.get((comp, miu, None)) or
                sim_lookup.get((comp, None, None))
        )

        properties = {
            "compartment": row.get("compt_id"),
            "miu": row.get("miu_id"),
            "nbal": row.get("nbal_id"),
        }

        if sim_data:
            properties.update({
                "priority": sim_data["priority"],
                "person_days": sim_data["person_days"],
                "cost": sim_data["cost"],
                "density": sim_data["density"],
                "flow": sim_data["flow"],
                "cleared_now": sim_data["cleared_now"],
                "cleared_fully": sim_data["cleared_fully"],
            })
        else:
            properties.update({"note": "No simulation data"})

        features.append({
            "type": "Feature",
            "properties": properties,
            "geometry": mapping(row["geometry"])
        })

        # key = (normalize(row.get("compt_id")),
        #        normalize(row.get("miu_id")),
        #        normalize(row.get("nbal_id")))
        # # key = (str(row.get("compt_id") or ""), str(row.get("miu_id") or ""), str(row.get("nbal_id") or ""))
        # sim_data = sim_lookup.get(key)
        # # fallback if no match found
        # properties = {
        #     "compartment": row.get("compt_id"),
        #     "miu": row.get("miu_id"),
        #     "nbal": row.get("nbal_id"),
        # }
        # if sim_data:
        #     properties.update({
        #         "priority": sim_data["priority"],
        #         "person_days": sim_data["person_days"],
        #         "cost": sim_data["cost"],
        #         "density": sim_data["density"],
        #         "flow": sim_data["flow"],
        #         "cleared_now": sim_data["cleared_now"],
        #         "cleared_fully": sim_data["cleared_fully"],
        #     })
        # else:
        #     properties.update({"note": "No simulation data"})
        #
        # features.append({
        #     "type": "Feature",
        #     "properties": properties,
        #     "geometry": mapping(row["geometry"])
        # })

    polygon_geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    # print(json.dumps(polygon_geojson, indent=4))

    return JsonResponse({
        'gis_mapping_geojson': polygon_geojson,
    })


# --- Step 3: Main visualization data ---
# Step 3: Main visualization data
# visualization data view
@login_required
def visualization_data(request, planning_id):
    planning = get_object_or_404(Planning, id=planning_id, user=request.user)

    year = request.GET.get("year")
    budget = request.GET.get("budget")
    level = request.GET.get("level", "compartment")

    if not year or not budget:
        return JsonResponse({"error": "Year and budget are required"}, status=400)

    budget_scenario = get_object_or_404(BudgetScenario, planning=planning, name=budget)
    yearly_result = get_object_or_404(YearlyResult, budget=budget_scenario, year=year)
    rows = SimulationRow.objects.filter(yearly_result=yearly_result).values()
    df = pd.DataFrame(list(rows))


    # grouped data for table
    if level == "compartment":
        grouped = df.groupby("compt_id").agg({"priority": "sum", "person_days": "sum","cost": "sum","density": "mean","flow": "sum","cleared_now": "max"}).reset_index()
    elif level == "miu":
        grouped = df.groupby(["compt_id", "miu_id"]).agg({"priority": "sum", "person_days": "sum","cost": "sum","density": "mean","flow": "sum","cleared_now": "max"}).reset_index()
    else:
        grouped = df.groupby(["compt_id", "miu_id", "nbal_id"]).agg({"priority": "sum", "person_days": "sum","cost": "sum","density": "mean","flow": "sum","cleared_now": "max"}).reset_index()

    # 🔹 Round only numeric columns we care about
    round_cols = ["priority", "person_days", "cost", "density", "flow"]
    for col in round_cols:
        if col in grouped.columns:
            grouped[col] = grouped[col].round(2)


    # Get SimulationBudgetYear totals for this year
    budget_year = SimulationBudgetYear.objects.filter(planning=planning, year=year).first()
    budget_totals = {}
    if budget_year:
        for i, b in enumerate(["plan_1", "plan_2", "plan_3", "plan_4"]):
            budget_totals[b] = float(getattr(budget_year, b))

    # 🔹 Always load the optimal budget separately
    optimal_scenario = get_object_or_404(BudgetScenario, planning=planning, name="optimal")
    optimal_yearly = get_object_or_404(YearlyResult, budget=optimal_scenario, year=year)
    optimal_rows = SimulationRow.objects.filter(yearly_result=optimal_yearly).values()
    optimal_df = pd.DataFrame(list(optimal_rows))

    # ✅ Compute optimal plan total cost for this year
    optimal_budget = float(optimal_df["cost"].sum()) if not optimal_df.empty else 0.0


    return JsonResponse({
        "table": grouped.to_dict(orient="records"),
        "budget_totals": budget_totals,
        "currency": planning.currency,
        "optimal_budget": optimal_budget
    }, safe=False)


# --- Step 4: API for timeseries graphs ---
# visualization timeseries view
@login_required
def visualization_timeseries(request, planning_id):
    planning = get_object_or_404(Planning, id=planning_id, user=request.user)

    data = {}
    for budget in BudgetScenario.SCENARIO_CHOICES:
        budget_name = budget[0]
        # print(budget_name)
        scenario = BudgetScenario.objects.filter(planning=planning, name=budget_name).first()
        if not scenario:
            continue
        results = YearlyResult.objects.filter(budget=scenario).order_by("year")


        yearly_data = []
        for yr in results:
            df = pd.DataFrame(list(yr.rows.all().values()))

            # Only consider density values > 0 and not NaN
            density_avg = df.loc[(df["density"] > 0) & (df["density"].notna()), "density"].mean()

            # If all rows are 0 or NaN, set to 0
            if pd.isna(density_avg):
                density_avg = 0

            yearly_data.append({
                "year": yr.year,
                "density": density_avg,
                "flow": df["flow"].sum(),
                "person_days": df["person_days"].sum(),
                "cost": df["cost"].sum(),
            })

        data[budget_name] = yearly_data
        # print(data)

    return JsonResponse(data, safe=False)

# for pdf's
# visualization pdf view
@login_required
def visualization_pdf(request, planning_id, year, budget):
    # helper functions:
    # --- Plot charts with matplotlib (match Chart.js style) ---
    def plot_line(metric, ylabel, title):
        plt.figure(figsize=(6, 4))
        for i, (budget_name, series) in enumerate(data.items()):
            years = [d["year"] for d in series]
            vals = [d[metric] for d in series]
            if budget_name == "optimal":
                plt.plot(years, vals, "k--*", label="Optimal")  # black dashed with stars
            else:
                plt.plot(years, vals, marker="o", label=budget_name)
        plt.title(title)
        plt.xlabel("Year")
        plt.ylabel(ylabel)
        plt.legend()
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150)
        buf.seek(0)
        plt.close()
        return buf

    def plot_bar_with_optimal(metric, ylabel, title):
        plt.figure(figsize=(7, 4))
        years = sorted(set(y for s in data.values() for y in [d["year"] for d in s]))
        width = 0.2
        x = range(len(years))

        # plot bars for each budget except optimal
        offset = - (len(budgets) - 1) * width / 2
        all_vals = []  # track all values to set y-limits nicely

        for i, (budget_name, series) in enumerate(data.items()):
            if budget_name == "optimal":
                continue
            vals = [next((d[metric] for d in series if d["year"] == yr), 0) for yr in years]
            all_vals.extend(vals)
            plt.bar([xi + offset + i * width for xi in x], vals, width, label=budget_name)

        # overlay optimal as line
        if "optimal" in data:
            vals = [next((d[metric] for d in data["optimal"] if d["year"] == yr), 0) for yr in years]
            all_vals.extend(vals)
            plt.plot(x, vals, "k--*", label="Optimal", linewidth=2, markersize=6)

        # x-axis formatting
        plt.xticks(x, years, rotation=45, ha="right")

        # y-axis zoom: only if we have non-zero values
        if all_vals:
            ymin = min(all_vals)
            ymax = max(all_vals)
            if ymax > 0:  # avoid zero division
                plt.ylim(max(0, ymin * 0.95), ymax * 1.05)

        plt.title(title)
        plt.xlabel("Year")
        plt.ylabel(ylabel)
        plt.legend()
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150)
        buf.seek(0)
        plt.close()
        return buf

    # actual code
    planning = get_object_or_404(Planning, id=planning_id, user=request.user)

    # get static files:
    mountain_img = finders.find("home/mountain.jpg")
    csir_logo = finders.find("collaborators/csirlogo.png")
    wfw_logo = finders.find("collaborators/workingforwaterlogo.jpg")

    # --- Get planning data etc. ---
    budget_scenario = get_object_or_404(BudgetScenario, planning=planning, name=budget)
    yearly_result = get_object_or_404(YearlyResult, budget=budget_scenario, year=year)
    rows = SimulationRow.objects.filter(yearly_result=yearly_result).values()
    df = pd.DataFrame(list(rows))

    level_data = {
        "Compartment": df.groupby("compt_id").agg({"person_days":"sum","cost":"sum","density":"mean","flow":"sum"}).reset_index(),
        "MIU": df.groupby(["compt_id","miu_id"]).agg({"person_days":"sum","cost":"sum","density":"mean","flow":"sum"}).reset_index(),
        "NBAL": df.groupby(["compt_id","miu_id","nbal_id"]).agg({
            "person_days":"sum","cost":"sum","density":"mean","flow":"sum",
            "cleared_now":"max","cleared_fully":"max"
        }).reset_index()
    }

    budget_years = SimulationBudgetYear.objects.filter(planning=planning).order_by("year")

    # planning and categories
    costing_mappings = planning.costing_mappings.select_related("costing_model")
    categories_all = planning.planning_categories.select_related("category")


    # Grpahs pre processing
    # --- load yearly results across budgets (same as visualization_timeseries) ---
    data = {}
    budgets = [b[0] for b in BudgetScenario.SCENARIO_CHOICES]  # names only
    for budget_name in budgets:
        scenario = BudgetScenario.objects.filter(planning=planning, name=budget_name).first()
        if not scenario:
            continue
        results = YearlyResult.objects.filter(budget=scenario).order_by("year")

        yearly_data = []
        for yr in results:
            df = pd.DataFrame(list(yr.rows.all().values()))
            yearly_data.append({
                "year": yr.year,
                "density": df["density"].mean() if not df.empty else 0,
                "flow": df["flow"].sum() if not df.empty else 0,
                "person_days": df["person_days"].sum() if not df.empty else 0,
                "cost": df["cost"].sum() if not df.empty else 0,
            })
        data[budget_name] = yearly_data

    # also include "optimal" if exists
    opt_scenario = BudgetScenario.objects.filter(planning=planning, name="optimal").first()
    if opt_scenario:
        opt_results = YearlyResult.objects.filter(budget=opt_scenario).order_by("year")
        data["optimal"] = []
        for yr in opt_results:
            df = pd.DataFrame(list(yr.rows.all().values()))
            data["optimal"].append({
                "year": yr.year,
                "density": df["density"].mean() if not df.empty else 0,
                "flow": df["flow"].sum() if not df.empty else 0,
                "person_days": df["person_days"].sum() if not df.empty else 0,
                "cost": df["cost"].sum() if not df.empty else 0,
            })

    # override the default class by adding a footer with page numbers
    class PDF(FPDF):
        def footer(self):
            # Page numbers in the footer
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f"Page {self.page_no()} / {{nb}}", align="C")

        def table_row(self, col_widths, row_data, alignments, line_height=8):
            """
            Render a row with wrapped text, auto-adjusting row height
            so nothing overlaps.
            """
            # Calculate row height based on the max number of wrapped lines
            line_counts = []
            for i, text in enumerate(row_data):
                # Count wrapped lines for each cell
                line_counts.append(self.multi_cell_line_count(col_widths[i], line_height, str(text)))
            max_lines = max(line_counts) if line_counts else 1
            row_height = line_height * max_lines

            # Check for page break
            if self.get_y() + row_height > self.page_break_trigger:
                self.add_page(self.cur_orientation)

            # Draw each cell
            x_start = self.get_x()
            y_start = self.get_y()
            for i, text in enumerate(row_data):
                self.multi_cell(col_widths[i], line_height, str(text), border=1, align=alignments[i],
                                max_line_height=line_height)
                x_start += col_widths[i]
                self.set_xy(x_start, y_start)
            self.ln(row_height)

        def multi_cell_line_count(self, w, h, txt):
            """
            Estimate how many lines of text will wrap inside a multicell
            """
            if not txt:
                return 1
            return len(self.multi_cell(w, h, txt, split_only=True))

    # --- Cover Page ---

    # --- Initialize PDF with custom footer---
    pdf = PDF()
    # add page numbers
    pdf.alias_nb_pages()
    # start a new page
    pdf.add_page()

    # Set CSIR corporate colours (blue background)
    pdf.set_fill_color(0, 51, 102)  # CSIR dark blue
    pdf.rect(0, 0, 210, 297, 'F')  # Fill whole page

    # Add mountain background (full-width image)
    if mountain_img:
        pdf.image(mountain_img, x=0, y=50, w=210)

    # MUCP Heading
    pdf.set_text_color(200, 200, 200)  # White text
    pdf.set_font("Arial", "B", 28)
    pdf.ln(2)
    pdf.cell(0, 10, "Management Unit Control Plan", ln=True, align="C")
    pdf.cell(0, 10, "Automated Report", ln=True, align="C")

    # Sub-heading
    pdf.set_font("Arial", "", 16)
    pdf.cell(0, 10, "MUCP Tool", ln=True, align="C")
    pdf.ln(120)

    # Collaborators + contact
    if csir_logo:
        # Draw white rectangle behind the logo
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(x=30, y=200, w=40, h=20, style='F')
        pdf.image(csir_logo, x=30, y=200, w=40)
    if wfw_logo:
        pdf.image(wfw_logo, x=140, y=200, w=40)

    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.ln(70)
    pdf.cell(0, 10, "Developed by Council for Scientific and Industrial Research (CSIR) & Working For Water (WFW DFFE)", ln=True, align="C")
    pdf.cell(0, 10, "www.csir.co.za | https://www.dws.gov.za/wfw/", ln=True, align="C")
    pdf.cell(0, 10, "Contact: awannenburgh@dffe.gov.za", ln=True, align="C")

    # --- other pages ---

    # --- Contents ---
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Contents:", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    toc_items = [
        "Section 1: Planning Information",
        "Section 2: Cost and Category Models",
        "Section 3: Propagated Budgets",
        "Section 4: Model Output Charts and Graphs",
        "Section 5: Compartment, MIU and NBAL results"
    ]

    for item in toc_items:
        pdf.cell(0, 8, f"- {item}", ln=True, align="L")

    # --- Section 1: Planning Info ---
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Section 1: Planning Information", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.ln(3)

    pdf.cell(0, 8, f"Project Name: {planning.project.name}", ln=True)
    pdf.cell(0, 8, f"Created at: {planning.created_at} UTC [+2 hours for SAST]", ln=True)
    pdf.cell(0, 8, f"Start Year: {planning.start_year}", ln=True)
    pdf.cell(0, 8, f"Years to Run: {planning.years_to_run}", ln=True)
    pdf.cell(0, 8, f"Currency: {planning.currency}", ln=True)
    pdf.cell(0, 8, f"Working Day Hours: {planning.standard_working_day}", ln=True)
    pdf.cell(0, 8, f"Working Year Days: {planning.standard_working_year_days}", ln=True)
    pdf.cell(0, 8, f"Clearing Norm Model: {planning.clearing_norm_model}", ln=True)
    pdf.cell(0, 8, f"MUCP Tool User: {planning.user}", ln=True)
    pdf.ln(3)

    # Budgets & Escalation
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Budgets & Escalation", ln=True)
    pdf.set_font("Arial", "", 12)
    for i in range(1, 5):
        pdf.cell(0, 8, f"Budget {i}: {planning.currency} {getattr(planning, f'budget_plan_{i}'):,.2f}, "
                       f"Escalation {getattr(planning, f'escalation_plan_{i}')}%", ln=True)
    pdf.ln(3)

    # Categories
    categories = [pc.category.name for pc in planning.planning_categories.all()]
    if categories:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Prioritization Categories:", ln=True)
        pdf.set_font("Arial", "", 12)
        for c in categories:
            pdf.cell(0, 8, f"- {c}", ln=True)
        pdf.ln(3)

    # Costing Mappings
    mappings = planning.costing_mappings.all()
    if mappings:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Costing Mappings:", ln=True)
        pdf.set_font("Arial", "", 12)
        for cm in mappings:
            pdf.cell(0, 8, f"{cm.costing_value} -> {cm.costing_model.name}", ln=True)

    # --- Section 2: Landscape ---
    pdf.add_page(orientation="L")  # switch to landscape
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Section 2: Cost and Category Models", ln=True, align="C")
    pdf.ln(3)

    # --- Costing Models Table ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Costing Models in Current Planning", ln=True)
    pdf.set_font("Arial", "", 9)

    col_widths = [40, 30, 25, 25, 25, 25, 25, 25]
    headers = ["Mapping Value", "Model", "Init Team", "Init Cost/day",
               "Followup Team", "Followup Cost/day", "Vehicle Cost/day", "Fuel Cost/hr"]
    alignments = ["C", "C", "C", "R", "C", "R", "R", "R"]

    pdf.table_row(col_widths, headers, ["C"] * len(headers), line_height=6)

    for mapping in costing_mappings:
        cm = mapping.costing_model
        pdf.table_row(col_widths, [
            mapping.costing_value,
            cm.name,
            cm.initial_team_size,
            f"{cm.initial_cost_per_day:,.2f}",
            cm.followup_team_size,
            f"{cm.followup_cost_per_day:,.2f}",
            f"{cm.vehicle_cost_per_day:,.2f}",
            f"{cm.fuel_cost_per_hour:,.2f}",
        ], alignments, line_height=6)

        if cm.daily_cost_items.exists():
            for item in cm.daily_cost_items.all():
                pdf.table_row(col_widths, [
                    "", f"Extra: {item.daily_cost_item}", "", f"{item.daily_item_cost:,.2f}", "", "", "", ""
                ], alignments, line_height=6)

    pdf.ln(10)

    # --- Categories Table ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Prioritization Categories", ln=True)
    pdf.set_font("Arial", "", 9)

    col_widths = [40, 30, 25, 50, 25]
    headers = ["Category", "Type", "Weight", "Range/Value", "Priority"]
    alignments = ["C", "C", "R", "C", "C"]

    pdf.table_row(col_widths, headers, ["C"] * len(headers), line_height=6)

    for pc in categories_all:
        cat = pc.category
        if cat.category_type == "numeric":
            bands = cat.numeric_bands.all()
            if not bands:
                pdf.table_row(col_widths, [cat.name, cat.category_type, f"{cat.weight:.2f}", "—", "—"], alignments,
                              line_height=6)
            for i, band in enumerate(bands):
                pdf.table_row(col_widths, [
                    cat.name if i == 0 else "",
                    cat.category_type if i == 0 else "",
                    f"{cat.weight:.2f}" if i == 0 else "",
                    f"{band.range_low}-{band.range_high}",
                    band.priority
                ], alignments, line_height=6)
        else:
            values = cat.text_values.all()
            if not values:
                pdf.table_row(col_widths, [cat.name, cat.category_type, f"{cat.weight:.2f}", "—", "—"], alignments,
                              line_height=6)
            for i, val in enumerate(values):
                pdf.table_row(col_widths, [
                    cat.name if i == 0 else "",
                    cat.category_type if i == 0 else "",
                    f"{cat.weight:.2f}" if i == 0 else "",
                    val.text_value,
                    val.priority
                ], alignments, line_height=6)

    pdf.ln(10)

    # --- Section 3: Propagated budgets ---
    pdf.add_page(orientation="P")  # switch back to portrait
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Section 3: Propagated Budgets", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.ln(3)

    pdf.set_auto_page_break(auto=True, margin=15)

    # --- Budget Years Table ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Budgets over Years", ln=True)
    pdf.set_font("Arial", "", 12)

    # Table header
    col_widths = [20, 35, 35, 35, 35]
    headers = ["Year", f"Budget 1 ({planning.currency})", f"Budget 2 ({planning.currency})", f"Budget 3 ({planning.currency})", f"Budget 4 ({planning.currency})"]
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, h, border=1, align="C")
    pdf.ln()

    for by in budget_years:
        pdf.cell(col_widths[0], 8, str(by.year), border=1, align="C")
        pdf.cell(col_widths[1], 8, f"{by.plan_1:,.2f}", border=1, align="R")
        pdf.cell(col_widths[2], 8, f"{by.plan_2:,.2f}", border=1, align="R")
        pdf.cell(col_widths[3], 8, f"{by.plan_3:,.2f}", border=1, align="R")
        pdf.cell(col_widths[4], 8, f"{by.plan_4:,.2f}", border=1, align="R")
        pdf.ln()

    pdf.ln(5)

    # Section 4: Graphs
    # --- Charts ---
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Section 4: Model Output Charts and Graphs", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.ln(3)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"The following graphs indicate the results of your planning:", ln=True)
    pdf.cell(0, 8, f"- Density (in %)", ln=True)
    pdf.cell(0, 8, f"- Person Days (in Person Day units)", ln=True)
    pdf.cell(0, 8, f"- Costing (in {planning.currency})", ln=True)
    pdf.cell(0, 8, f"- Flow (in m^3/s)", ln=True)
    pdf.ln(5)


    charts = [
        ("density", "%", "Annual Density Reduction (%)", plot_line),
        ("person_days", "Person Days", "Person Days", plot_line),
        ("cost", f"{planning.currency}", "Annual Cost", plot_bar_with_optimal),
        ("flow", "m³/s", "Annual Flow Reduction (m³/s)", plot_line),
    ]

    for metric, ylabel, title, plot_fn in charts:
        img_buf = plot_fn(metric, ylabel, title)
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, title, ln=True, align="C")
        pdf.image(img_buf, x=20, y=40, w=170)  # center chart


    # Section 5:
    pdf.add_page(orientation="L") # note its landscape now
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Section 5: Compartment, MIU and NBAL Results", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.ln(3)

    # --- Planning Info ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Planning Details", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Name: {planning.project.name}", ln=True)
    pdf.cell(0, 8, f"Year: {year}", ln=True)
    pdf.cell(0, 8, f"Budget: {budget}", ln=True)
    pdf.ln(5)

    # --- Level Data Tables ---
    for level, data in level_data.items():
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"{level} Results", ln=True)
        pdf.set_font("Arial", "", 10)

        # Table header
        for col in data.columns:
            pdf.cell(30, 8, str(col), border=1, align="C")
        pdf.ln()

        # Table rows
        for row in data.itertuples(index=False):
            for val in row:
                if isinstance(val, (int, float)):
                    pdf.cell(30, 8, f"{val:,.2f}", border=1, align="C")
                else:
                    pdf.cell(30, 8, str(val), border=1, align="C")
            pdf.ln()
        pdf.ln(5)
        pdf.add_page(orientation="L")


    # --- Final Page: End of Report ---
    # pdf.add_page()  # Portrait by default
    pdf.set_fill_color(0, 51, 102)  # CSIR dark blue
    # Fill the entire current page dynamically
    pdf.rect(0, 0, pdf.w, pdf.h, 'F')



    pdf.set_text_color(255, 255, 255)  # White text
    pdf.set_font("Arial", "B", 28)
    pdf.ln(50)
    pdf.cell(0, 20, "Management Unit Control Plan", ln=True, align="C")
    pdf.cell(0, 20, "Automated Report", ln=True, align="C")

    pdf.set_font("Arial", "B", 20)
    pdf.ln(20)
    pdf.cell(0, 15, "End of Report", ln=True, align="C")


    # --- Return PDF response ---
    # pdf_bytes = pdf.output(dest='S')  # returns bytes
    pdf_bytes = bytes(pdf.output(dest='S'))  # <-- convert bytearray to bytes
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename=MUCP_Report_{planning.id}_{year}_{budget}_{planning.user}.pdf'


    return response




"""
MUCP TOOL
Author: Kirodh Boodhraj
"""
# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden

from django.contrib.auth.decorators import login_required
from django.db import models

from django.contrib import messages
from django.core.paginator import Paginator

from .models import GrowthForm, TreatmentMethod, Species, Herbicide, ClearingNormSet, ClearingNorm, CostingModel, DailyCostItem, TextPriorityValue, NumericPriorityBand, Category
from .forms import GrowthFormForm, TreatmentMethodForm, SpeciesForm, HerbicideForm, ClearingNormForm,ClearingNormSetForm, DailyCostItemForm, CostingModelForm, NumericPriorityBandForm, TextPriorityValueForm, CategoryForm


# support home view
def support_view(request):
    return render(request, 'support/support.html')


#############################
## Growth Forms
#############################

# growth form list view
@login_required
def growth_form_list(request):
    forms = GrowthForm.objects.filter(
        models.Q(user=request.user) | models.Q(user=None)
    ).order_by('growth_form')
    return render(request, 'support/growth_form_list.html', {'forms': forms})

# growth form create view
@login_required
def growth_form_create(request):
    if request.method == 'POST':
        form = GrowthFormForm(request.POST)
        try:
            if form.is_valid():
                growth_form = form.save(commit=False)
                growth_form.user = request.user
                growth_form.save()
                return redirect('support:growth_form_list')
        except Exception as e:
            form.add_error(None, "This growth form already exists.")
    else:
        form = GrowthFormForm()
    return render(request, 'support/growth_form_form.html', {'form': form, 'action': 'Create'})

# growth form update view
@login_required
def growth_form_update(request, pk):
    growth_form = get_object_or_404(GrowthForm, pk=pk, user=request.user)
    if request.method == 'POST':
        form = GrowthFormForm(request.POST, instance=growth_form)
        if form.is_valid():
            form.save()
            return redirect('support:growth_form_list')
    else:
        form = GrowthFormForm(instance=growth_form)
    return render(request, 'support/growth_form_form.html', {'form': form, 'action': 'Update'})

# growth form delete view
@login_required
def growth_form_delete(request, pk):
    growth_form = get_object_or_404(GrowthForm, pk=pk, user=request.user)
    if request.method == 'POST':
        growth_form.delete()
        return redirect('support:growth_form_list')
    return render(request, 'support/growth_form_confirm_delete.html', {'object': growth_form})


#############################
## Treatment methods
#############################

# treatment method list view
@login_required
def treatment_method_list(request):
    forms = TreatmentMethod.objects.filter(
        models.Q(user=request.user) | models.Q(user=None)
    ).order_by('treatment_method')
    return render(request, 'support/treatment_method_list.html', {'forms': forms})

# treatment method create view
@login_required
def treatment_method_create(request):
    if request.method == 'POST':
        form = TreatmentMethodForm(request.POST)
        try:
            if form.is_valid():
                treatment_method = form.save(commit=False)
                treatment_method.user = request.user
                treatment_method.save()
                return redirect('support:treatment_method_list')
        except Exception as e:
            form.add_error(None, "This treatment method already exists.")
    else:
        form = TreatmentMethodForm()
    return render(request, 'support/treatment_method_form.html', {'form': form, 'action': 'Create'})

# treatment method update view
@login_required
def treatment_method_update(request, pk):
    treatment_method = get_object_or_404(TreatmentMethod, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TreatmentMethodForm(request.POST, instance=treatment_method)
        if form.is_valid():
            form.save()
            return redirect('support:treatment_method_list')
    else:
        form = TreatmentMethodForm(instance=treatment_method)
    return render(request, 'support/treatment_method_form.html', {'form': form, 'action': 'Update'})

# treatment method delete view
@login_required
def treatment_method_delete(request, pk):
    treatment_method = get_object_or_404(TreatmentMethod, pk=pk, user=request.user)
    if request.method == 'POST':
        treatment_method.delete()
        return redirect('support:treatment_method_list')
    return render(request, 'support/treatment_method_confirm_delete.html', {'object': treatment_method})


#############################
## Species
#############################

# species list view
@login_required
def species_list(request):
    search_query = request.GET.get('q', '')

    default_species = Species.objects.filter(user=None).order_by('species_name')
    user_species = Species.objects.filter(user=request.user).order_by('species_name')

    if search_query:
        default_species = default_species.filter(
            models.Q(species_name__icontains=search_query) |
            models.Q(english_name__icontains=search_query) |
            models.Q(afrikaans_name__icontains=search_query)
        )
        user_species = user_species.filter(
            models.Q(species_name__icontains=search_query) |
            models.Q(english_name__icontains=search_query) |
            models.Q(afrikaans_name__icontains=search_query)
        )

    paginator_default = Paginator(default_species, 10)
    paginator_user = Paginator(user_species, 10)

    page_number_default = request.GET.get('default_page')
    page_number_user = request.GET.get('user_page')

    default_page = paginator_default.get_page(page_number_default)
    user_page = paginator_user.get_page(page_number_user)

    return render(request, 'support/species_list.html', {
        'default_page': default_page,
        'user_page': user_page,
        'search_query': search_query
    })

# species details view
@login_required
def species_detail(request, pk):
    species = get_object_or_404(Species, pk=pk)
    return render(request, 'support/species_detail.html', {'species': species})

# species create view
@login_required
def species_create(request):
    if request.method == 'POST':
        form = SpeciesForm(request.POST, user=request.user)
        if form.is_valid():
            species = form.save(commit=False)
            species.user = request.user
            species.save()
            return redirect('support:species_list')
    else:
        form = SpeciesForm(user=request.user)
    return render(request, 'support/species_form.html', {'form': form, 'action': 'Create'})

# species update view
@login_required
def species_edit(request, pk):
    species = get_object_or_404(Species, pk=pk, user=request.user)
    form = SpeciesForm(request.POST or None, instance=species)
    if form.is_valid():
        form.save()
        return redirect('support:species_list')
    return render(request, 'support/species_form.html', {'form': form, 'action': 'Edit'})

# species delete view
@login_required
def species_delete(request, pk):
    species = get_object_or_404(Species, pk=pk, user=request.user)
    if request.method == 'POST':
        species.delete()
        return redirect('support:species_list')
    return render(request, 'support/species_confirm_delete.html', {'object': species})


#############################
## Herbicides
#############################

# herbicide list view
@login_required
def herbicide_list(request):
    search_query = request.GET.get('q', '')

    user_herbicides_qs = Herbicide.objects.filter(user=request.user).order_by('herbicide')
    default_herbicides_qs = Herbicide.objects.filter(user=None).order_by('herbicide')

    if search_query:
        user_herbicides_qs = user_herbicides_qs.filter(herbicide__icontains=search_query)
        default_herbicides_qs = default_herbicides_qs.filter(herbicide__icontains=search_query)

    user_paginator = Paginator(user_herbicides_qs.order_by('herbicide'), 10)
    default_paginator = Paginator(default_herbicides_qs.order_by('herbicide'), 10)

    user_page_number = request.GET.get('user_page')
    default_page_number = request.GET.get('default_page')

    user_page_obj = user_paginator.get_page(user_page_number)
    default_page_obj = default_paginator.get_page(default_page_number)

    return render(request, 'support/herbicide_list.html', {
        'user_page': user_page_obj,
        'default_page': default_page_obj,
        'search_query': search_query,
    })

# herbicide create view
@login_required
def herbicide_create(request):
    if request.method == 'POST':
        form = HerbicideForm(request.POST)
        try:
            if form.is_valid():
                herbicide = form.save(commit=False)
                herbicide.user = request.user
                herbicide.save()
                return redirect('support:herbicide_list')
        except Exception as e:
            form.add_error(None, f"This herbicide already exists. {e}")
    else:
        form = HerbicideForm()
    return render(request, 'support/herbicide_form.html', {'form': form, 'action': 'Create'})

# herbicide update view
@login_required
def herbicide_update(request, pk):
    herbicide = get_object_or_404(Herbicide, pk=pk, user=request.user)
    if request.method == 'POST':
        form = HerbicideForm(request.POST, instance=herbicide)
        if form.is_valid():
            form.save()
            return redirect('support:herbicide_list')
    else:
        form = HerbicideForm(instance=herbicide)
    return render(request, 'support/herbicide_form.html', {'form': form, 'action': 'Update'})

# herbicide delete view
@login_required
def herbicide_delete(request, pk):
    herbicide = get_object_or_404(Herbicide, pk=pk, user=request.user)
    if request.method == 'POST':
        herbicide.delete()
        return redirect('support:herbicide_list')
    return render(request, 'support/herbicide_confirm_delete.html', {'object': herbicide})


#############################
## Clearing norms
#############################
# -------------------------
# LIST VIEW
# -------------------------
# clearing norms list view
@login_required
def clearing_norm_list(request):
    search_query = request.GET.get('q', '')

    # Default set(s) created by the system (no user assigned)
    default_sets = ClearingNormSet.objects.filter(user=None).order_by('name')

    # User-created sets
    user_sets = ClearingNormSet.objects.filter(user=request.user).order_by('name')

    # Handle search filtering at the norm level
    def get_filtered_norms(norms_queryset):
        if search_query:
            norms_queryset = norms_queryset.filter(
                models.Q(process__icontains=search_query) |
                models.Q(size_class__icontains=search_query) |
                models.Q(terrain__icontains=search_query) |
                models.Q(treatment_method__treatment_method__icontains=search_query) |
                models.Q(growth_form__growth_form__icontains=search_query)
            )
        return norms_queryset

    # Pagination for each set's norms
    paginated_default_sets = []
    for norm_set in default_sets:
        norms = get_filtered_norms(norm_set.norms.all().order_by('process'))
        paginator = Paginator(norms, 10)
        page_number = request.GET.get(f'default_set_{norm_set.id}_page')
        page_obj = paginator.get_page(page_number)
        paginated_default_sets.append((norm_set, page_obj))

    paginated_user_sets = []
    for norm_set in user_sets:
        norms = get_filtered_norms(norm_set.norms.all().order_by('process'))
        paginator = Paginator(norms, 10)
        page_number = request.GET.get(f'user_set_{norm_set.id}_page')
        page_obj = paginator.get_page(page_number)
        paginated_user_sets.append((norm_set, page_obj))

    return render(request, 'support/clearing_norm_list.html', {
        'search_query': search_query,
        'paginated_default_sets': paginated_default_sets,
        'paginated_user_sets': paginated_user_sets
    })


# -------------------------
# CREATE / EDIT CLEARING NORM
# -------------------------
# clearing norms create view
@login_required
def clearing_norm_create(request):
    norm_set_id = request.GET.get('set')  # Get from query param when adding
    norm_set = None

    if norm_set_id:
        norm_set = get_object_or_404(ClearingNormSet, id=norm_set_id)

        # Optional: prevent adding to APO default (if desired)
        if norm_set.user is None:
            return HttpResponseForbidden("You cannot add to the APO default norm set.")

    if request.method == 'POST':
        form = ClearingNormForm(request.POST)
        if form.is_valid():
            norm = form.save(commit=False)

            # If coming from a set link, attach it
            if norm_set:
                norm.clearing_norm_set = norm_set

            norm.save()
            return redirect('support:clearing_norm_list')
    else:
        form = ClearingNormForm()

    return render(request, 'support/clearing_norm_form.html', {
        'form': form,
        'norm_set': norm_set,
        'action': "Create",
    })


# clearing norms update view
@login_required
def clearing_norm_update(request, pk):
    norm = get_object_or_404(ClearingNorm, pk=pk, clearing_norm_set__user=request.user)
    form = ClearingNormForm(request.POST or None, instance=norm)
    if form.is_valid():
        form.save()
        return redirect('support:clearing_norm_list')
    return render(request, 'support/clearing_norm_form.html', {'form': form, 'action':'Update'})

# clearing norms delete view
@login_required
def clearing_norm_delete(request, pk):
    norm = get_object_or_404(ClearingNorm, pk=pk, clearing_norm_set__user=request.user)
    if request.method == 'POST':
        norm.delete()
        return redirect('support:clearing_norm_list')
    return render(request, 'support/clearing_norm_confirm_delete.html', {'object': norm})


# -------------------------
# CREATE / DELETE CLEARING NORM SET
# -------------------------
# clearing norms set create view
@login_required
def clearing_norm_set_create(request):
    if request.method == 'POST':
        try:
            form = ClearingNormSetForm(request.POST)
            if form.is_valid():
                norm_set = form.save(commit=False)
                norm_set.user = request.user
                norm_set.save()
                return redirect('support:clearing_norm_list')
        except Exception as e:
            form.add_error(None, f"This Clearing norm set already exists. {e}")
    else:
        form = ClearingNormSetForm()
    return render(request, 'support/clearing_norm_set_form.html', {'form': form})

# clearing norms set delete view
@login_required
def clearing_norm_set_delete(request, pk):
    norm_set = get_object_or_404(ClearingNormSet, pk=pk, user=request.user)
    if request.method == 'POST':
        norm_set.delete()  # Cascades to all norms in the set
        return redirect('support:clearing_norm_list')
    return render(request, 'support/clearing_norm_set_confirm_delete.html', {'object': norm_set})



# -------------------------
# CREATE / DELETE PRIORITIZATION MODELS VIEWS
# -------------------------
# category list view
@login_required
def category_list(request):
    # System default categories (no user assigned)
    default_categories = Category.objects.filter(user__isnull=True)

    # User categories (belonging to current logged-in user)
    user_categories = Category.objects.filter(user=request.user)

    context = {
        'default_categories': default_categories,
        'user_categories': user_categories,
    }
    return render(request, 'support/category_list.html', context)

# category create view
@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Category created.")
                return redirect('support:category_list')
            except Exception as e:
                form.add_error(None, "This category already exists.")
    else:
        form = CategoryForm(user=request.user)
    return render(request, 'support/category_form.html', {'form': form})

# category update view
@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if category.is_default:
        messages.error(request, "Default categories cannot be edited.")
        return redirect('support:category_list')

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated.")
            return redirect('support:category_list')
    else:
        form = CategoryForm(instance=category, user=request.user)

    return render(request, 'support/category_form.html', {'form': form})

# category delete view
@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if category.is_default:
        messages.error(request, "Default categories cannot be deleted.")
        return redirect('support:category_list')

    if request.method == 'POST':
        category.delete()
        messages.success(request, "Category deleted.")
        return redirect('support:category_list')

    return render(request, 'support/category_confirm_delete.html', {'object': category})

# Numeric Priority Bands CRUD
# numeric bands list view
@login_required
def numeric_band_list(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    if category.category_type != 'numeric':
        messages.error(request, "Category is not numeric type.")
        return redirect('support:category_list')
    bands = category.numeric_bands.all()
    return render(request, 'support/numeric_band_list.html', {'category': category, 'bands': bands})

# numeric bands create view
@login_required
def numeric_band_create(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    if category.is_default and category.user is None:
        # Overrides allowed but only once per user in Category model validation
        if Category.objects.filter(user=request.user, name=category.name).exists():
            messages.error(request, "You already override this default category.")
            return redirect('support:numeric_band_list', category_id=category.id)

    if request.method == 'POST':
        form = NumericPriorityBandForm(request.POST, category=category)
        if form.is_valid():
            try:
                band = form.save(commit=False)
                band.category = category
                band.save()
                messages.success(request, "Priority band added.")
                return redirect('support:numeric_band_list', category_id=category.id)
            except Exception as e:
                form.add_error(None, "This range already exists.")
    else:
        form = NumericPriorityBandForm()
    return render(request, 'support/numeric_band_form.html', {'form': form, 'category': category})

# numeric bands update view
@login_required
def numeric_band_update(request, pk):
    band = get_object_or_404(NumericPriorityBand, pk=pk)
    category = band.category
    if category.is_default and category.user is None:
        messages.error(request, "Cannot edit default category bands directly.")
        return redirect('support:numeric_band_list', category_id=category.id)

    if request.method == 'POST':
        form = NumericPriorityBandForm(request.POST, instance=band)
        if form.is_valid():
            form.save()
            messages.success(request, "Priority band updated.")
            return redirect('support:numeric_band_list', category_id=category.id)
    else:
        form = NumericPriorityBandForm(instance=band)

    return render(request, 'support/numeric_band_form.html', {'form': form, 'category': category})

# numeric bands delete view
@login_required
def numeric_band_delete(request, pk):
    band = get_object_or_404(NumericPriorityBand, pk=pk)
    category = band.category
    if category.is_default and category.user is None:
        messages.error(request, "Cannot delete default category bands directly.")
        return redirect('support:numeric_band_list', category_id=category.id)

    if request.method == 'POST':
        band.delete()
        messages.success(request, "Priority band deleted.")
        return redirect('support:numeric_band_list', category_id=category.id)

    return render(request, 'support/numeric_band_confirm_delete.html', {'object': band})

# Text Priority Values CRUD
# text values list view
@login_required
def text_value_list(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    if category.category_type != 'text':
        messages.error(request, "Category is not text type.")
        return redirect('support:category_list')
    values = category.text_values.all()
    return render(request, 'support/text_value_list.html', {'category': category, 'values': values})

# text values create view
@login_required
def text_value_create(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    if category.is_default and category.user is None:
        if Category.objects.filter(user=request.user, name=category.name).exists():
            messages.error(request, "You already override this default category.")
            return redirect('support:text_value_list', category_id=category.id)

    if request.method == 'POST':
        form = TextPriorityValueForm(request.POST)
        if form.is_valid():
            try:
                value = form.save(commit=False)
                value.category = category
                value.save()
                messages.success(request, "Priority value added.")
                return redirect('support:text_value_list', category_id=category.id)
            except Exception as e:
                form.add_error(None, "This text value already exists.")
    else:
        form = TextPriorityValueForm()
    return render(request, 'support/text_value_form.html', {'form': form, 'category': category})

# text values update view
@login_required
def text_value_update(request, pk):
    value = get_object_or_404(TextPriorityValue, pk=pk)
    category = value.category
    if category.is_default and category.user is None:
        messages.error(request, "Cannot edit default category values directly.")
        return redirect('support:text_value_list', category_id=category.id)

    if request.method == 'POST':
        form = TextPriorityValueForm(request.POST, instance=value)
        if form.is_valid():
            form.save()
            messages.success(request, "Priority value updated.")
            return redirect('support:text_value_list', category_id=category.id)
    else:
        form = TextPriorityValueForm(instance=value)

    return render(request, 'support/text_value_form.html', {'form': form, 'category': category})

# text values delete view
@login_required
def text_value_delete(request, pk):
    value = get_object_or_404(TextPriorityValue, pk=pk)
    category = value.category
    if category.is_default and category.user is None:
        messages.error(request, "Cannot delete default category values directly.")
        return redirect('support:text_value_list', category_id=category.id)

    if request.method == 'POST':
        value.delete()
        messages.success(request, "Priority value deleted.")
        return redirect('support:text_value_list', category_id=category.id)

    return render(request, 'support/text_value_confirm_delete.html', {'object': value})



# -------------------------
# CREATE / DELETE COST MODEL
# -------------------------
# daily costing item list view
@login_required
def costing_item_list_daily(request, costing_model_id):
    costing_model = get_object_or_404(CostingModel, id=costing_model_id, user=request.user)
    daily_items = DailyCostItem.objects.filter(costing_model=costing_model, user=request.user)

    paginator = Paginator(daily_items, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'support/dailycostitem_list.html', {
        'costing_model': costing_model,
        'page_obj': page_obj
    })


# daily costing item create view
@login_required
def costing_item_add_daily(request, costing_model_id):
    costing_model = get_object_or_404(CostingModel, id=costing_model_id, user=request.user)

    if request.method == "POST":
        form = DailyCostItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.costing_model = costing_model
            item.user = request.user
            item.save()
            return redirect('support:dailycost_list', costing_model_id=costing_model_id)
    else:
        form = DailyCostItemForm()

    return render(request, 'support/dailycostitem_form.html', {
        'form': form,
        'costing_model': costing_model
    })


# daily costing item update view
@login_required
def cost_item_update_daily(request, pk):
    item = get_object_or_404(DailyCostItem, pk=pk, user=request.user)
    if request.method == 'POST':
        form = DailyCostItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('support:dailycost_list', costing_model_id=item.costing_model.id)
    else:
        form = DailyCostItemForm(instance=item)
    return render(request, 'support/dailycostitem_form.html', {
        'form': form,
        'object': item
    })


# daily costing item delete view
@login_required
def cost_item_delete_daily(request, pk):
    item = get_object_or_404(DailyCostItem, pk=pk, user=request.user)
    costing_model_id = item.costing_model.id

    if request.method == 'POST':
        item.delete()
        return redirect('support:dailycost_list', costing_model_id=costing_model_id)

    return render(request, 'support/dailycostitem_confirm_delete.html', {
        'object': item
    })


# costing model list view
@login_required
def costingmodel_list(request):
    models = CostingModel.objects.filter(user=request.user)

    # paginate
    paginator = Paginator(models, 10)  # 10 entries per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "support/costingmodel_list.html",
        {"page_obj": page_obj, "models": page_obj.object_list},
    )

# costing model create view
@login_required
def costingmodel_create(request):
    if request.method == "POST":
        form = CostingModelForm(request.POST)
        try:
            if form.is_valid():
                obj = form.save(commit=False)
                obj.user = request.user
                obj.save()
                return redirect('support:costingmodel_list')
        except Exception as e:
            form.add_error(None, "This costing model already exists.")
    else:
        form = CostingModelForm()
    return render(request, 'support/costingmodel_form.html', {'form': form})


# costing model update view
@login_required
def costingmodel_update(request, pk):
    model = get_object_or_404(CostingModel, pk=pk, user=request.user)
    if request.method == "POST":
        form = CostingModelForm(request.POST, instance=model)
        if form.is_valid():
            form.save()
            return redirect('support:costingmodel_list')
    else:
        form = CostingModelForm(instance=model)
    daily_items = model.daily_cost_items.filter(user=request.user)
    daily_form = DailyCostItemForm()
    return render(request, 'support/costingmodel_form.html', {
        'form': form,
        'object': model,
        'daily_items': daily_items,
        'daily_form': daily_form
    })


# costing model delete view
@login_required
def costingmodel_delete(request, pk):
    model = get_object_or_404(CostingModel, pk=pk, user=request.user)
    if request.method == "POST":
        model.delete()
        return redirect('support:costingmodel_list')
    return render(request, 'support/costingmodel_confirm_delete.html', {'object': model})

import csv
from django.core.management.base import BaseCommand
from support.models import GrowthForm, TreatmentMethod, Species, Herbicide, ClearingNorm, ClearingNormSet, Category, NumericPriorityBand, TextPriorityValue


class Command(BaseCommand):
    help = 'Load default data for the support app'

    def handle(self, *args, **kwargs):
        # Your custom logic here
        #############################
        ## Growth forms
        #############################
        # Run in shell or a migration
        growth_form_defults = [
            "All",
            "Aquatic weed",
            "Cactus",
            "Creeper",
            "Grass",
            "Herbaceous",
            "Non sprouting tree",
            "Sprouting tree",
        ]

        for growth_form in growth_form_defults:
            print("Loading growth form: ", growth_form)
            GrowthForm.objects.get_or_create(growth_form=growth_form.lower(), user=None)

        #############################
        ## Treatment methods
        #############################

        treatment_method_defults = ["Bark Strip",
                                    "Basal Stem + diesel",
                                    "Cut below ground",
                                    "Cut & Spray",
                                    "Cut & Spray + Diesel",
                                    "Cut stump",
                                    "Cut stump + diesel",
                                    "Cut stump + oil",
                                    "Dig out and burn",
                                    "Felling",
                                    "Foliar Spray",
                                    "Frill",
                                    "Hand pull",
                                    "Lopping / Pruning",
                                    "Manual Removal",
                                    "Ring bark",
                                    "Soil application",
                                    "Spray from boat",
                                    "Spray from shoreline (bakkie sakkie)",
                                    "Spray from shoreline (knapsack)",
                                    "Stem inject",
                                    ]

        for treatment_method in treatment_method_defults:
            print("Loading treatment method: ", treatment_method)
            TreatmentMethod.objects.get_or_create(treatment_method=treatment_method.lower(), user=None)

        #############################
        ## Species
        #############################
        with open('support/management/commands/species.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                print("Loading species: ", row['Genus'].title())
                growth_form_obj = GrowthForm.objects.get(growth_form=(row['Growth Form']).lower(), user=None)

                Species.objects.get_or_create(
                    species_name=row['Species Name'].title(),
                    user=None,
                    defaults={
                        # 'ref_id': int(row['Ref ID']),
                        'genus': row['Genus'].title(),
                        'english_name': row['English Name'].title(),
                        'afrikaans_name': row['Afrikaans Name'].title(),
                        'growth_form': growth_form_obj,
                        'WC': bool(int(row['WC'])),
                        'NC': bool(int(row['NC'])),
                        'KZN': bool(int(row['KZN'])),
                        'GTG': bool(int(row['GTG'])),
                        'MPL': bool(int(row['MPL'])),
                        'FS': bool(int(row['FS'])),
                        'EC': bool(int(row['EC'])),
                        'LMP': bool(int(row['LMP'])),
                        'NW': bool(int(row['NW'])),
                        'initial_reduction': row['Initial Reduction'],
                        'follow_up_reduction': row['Follow-up Reduction'],
                        'treatment_frequency': row['Treatment Frequency'],
                        'densification': row['Densification'],
                        'flow_optimal': row['Flow Optimal'],
                        'flow_sub_optimal': row['Flow Sub Optimal'],
                        'flow_young': row['Flow Young'],
                        'flow_seedling': row['Flow Seedling'],
                        'flow_coppice': row['Flow Coppice'],
                    }
                )

        #############################
        ## Herbicides
        #############################
        with open('support/management/commands/herbicides.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                print("Loading herbicide: ", row['Herbicide'].title())

                Herbicide.objects.get_or_create(
                    herbicide=row['Herbicide'].title(),
                    user=None,
                    defaults={
                        # 'ref_id': int(row['Ref ID']),
                        'cost_per_litre': row['Cost/Ltr'],
                        'litres_per_hectare': row['Ltr/HA'],
                        'active_ingredient': row['Active Ingredient'].lower(),
                        'registration_status': row['Registration'].lower(),
                    }
                )



        #############################
        ## clearing norms
        #############################
        # 1. create the clearing norm default set
        clearing_norm_default_set, _ = ClearingNormSet.objects.get_or_create(
            name="APO Default",
            user=None,
        )

        # 2. create the norms in the default set
        with open('support/management/commands/clearing_norm.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            print("Loading clearing norms. May take a while...")
            for row in reader:
                growth_form_obj = GrowthForm.objects.get(growth_form=(row['Growth Form']).lower(), user=None)
                # print((row['Treatment Method']).lower())
                treatment_method_obj = TreatmentMethod.objects.get(treatment_method=(row['Treatment Method']).lower(), user=None)

                ClearingNorm.objects.get_or_create(
                    density=row['Density'],
                    process=row['Process'].lower(),
                    growth_form=growth_form_obj,
                    size_class=row["Size Class"].lower(),
                    treatment_method=treatment_method_obj,
                    terrain=row["Terrain"].lower(),
                    ppd=row["PPD"],
                    clearing_norm_set=clearing_norm_default_set,
                )

        #############################
        ## prioritization categories
        #############################
        DEFAULT_NUMERIC_CATEGORIES = [
            "Aggression", "Diversity", "Density", "Elevation", "Erosion", "Flood", "Forage",
            "Fuel", "Invasion", "Products", "Quality", "Rain", "Riparian", "River",
            "Runoff", "Seepage", "Siltation", "Slope", "Soil", "Stress", "Tourism",
            "Treat", "Veld Age", "Zone"
        ]

        DEFAULT_TEXT_CATEGORIES = ["Owner", "Vegetation Status"]

        CATEGORY_WEIGHTS = {
            "Aggression": 0.23,
            "Diversity": 0.49,
            "Density": 0.14,
            "Elevation": 0.43,
            "Erosion": 0.17,
            "Flood": 0.14,
            "Forage": 0.41,
            "Fuel": 0.29,
            "Invasion": 0.34,
            "Products": 0.12,
            "Owner": 0.4,
            "Quality": 0.21,
            "Rain": 0.0,
            "Riparian": 0.0,
            "River": 0.0,
            "Runoff": 0.5,
            "Seepage": 0.09,
            "Siltation": 0.56,
            "Slope": 0.42,
            "Soil": 0.34,
            "Vegetation Status": 0.05,
            "Stress": 0.1,
            "Treat": 0.28,
            "Tourism": 0.4,
            "Veld Age": 0.23,
            "Zone": 0.21,
        }

        # Step 1: Create defaults
        category_objs = {}
        for cat in DEFAULT_NUMERIC_CATEGORIES:
            obj, _ = Category.objects.get_or_create(
                name=cat,
                category_type='numeric',
                is_default=True,
                user=None,
                defaults={'weight': CATEGORY_WEIGHTS.get(cat, 0)}
            )
            category_objs[cat] = obj

        for cat in DEFAULT_TEXT_CATEGORIES:
            obj, _ = Category.objects.get_or_create(
                name=cat,
                category_type='text',
                is_default=True,
                user=None,
                defaults={'weight': CATEGORY_WEIGHTS.get(cat, 0)}
            )
            category_objs[cat] = obj

        # Step 2: Add default priority bands for numeric categories
        numeric_defaults = {
            "Aggression": [
                (0, 10, 1),
                (11, 20, 2),
                (21, 30, 3),
                (31, 40, 4),
            ],
            "Density": [
                (0, 5, 1),
                (6, 10, 2),
                (11, 15, 3),
                (16, 20, 4),
                (21, 25, 5),
                (26, 30, 6),
                (31, 40, 7),
                (41, 60, 8),
                (61, 80, 9),
                (81, 100, 10),
            ],
            "Elevation": [
                (0, 400, 1),
                (401, 800, 2),
                (801, 1000, 3),
                (1001, 1200, 4),
                (1201, 1400, 5),
                (1401, 1600, 6),
                (1601, 1800, 7),
                (1801, 2000, 8),
            ],
            "Erosion": [
                (0, 10, 1),
                (11, 20, 2),
                (21, 30, 3),
                (31, 40, 4),
                (41, 50, 5),
                (51, 60, 6),
                (61, 70, 7),
                (71, 80, 8),
                (81, 90, 9),
            ],
            "Rain": [
                (0, 200, 1),
                (201, 400, 2),
                (401, 600, 3),
                (601, 800, 4),
                (801, 1000, 5),
                (1001, 1200, 6),
                (1201, 1400, 7),
                (1401, 1600, 8),
                (1601, 1800, 9),
                (1801, 2400, 10),
                (2401, 3000, 11),
            ],
            "Riparian": [
                (0, 3, 1),
                (4, 7, 2),
                (8, 11, 3),
                (12, 15, 4),
                (16, 19, 5),
                (20, 23, 6),
                (24, 27, 7),
                (28, 31, 8),
                (32, 35, 9),
            ],
            "Runoff": [
                (0, 100, 1),
                (101, 200, 2),
                (201, 300, 3),
                (301, 400, 4),
                (401, 500, 5),
                (501, 600, 6),
                (601, 700, 7),
                (701, 3500, 8),
            ],
            "Seepage": [
                (0, 3, 1),
                (4, 7, 2),
                (8, 11, 3),
                (12, 15, 4),
                (16, 19, 5),
                (20, 23, 6),
                (24, 27, 7),
                (28, 31, 8),
                (32, 35, 9),
            ],
            "Siltation": [
                (0, 100, 1),
                (101, 200, 2),
                (201, 300, 3),
                (301, 400, 4),
                (401, 500, 5),
                (501, 600, 6),
                (601, 700, 7),
                (701, 800, 8),
                (801, 900, 9),
            ],
            "Soil": [
                (0, 1, 1),
                (2, 3, 2),
                (4, 5, 3),
                (6, 7, 4),
                (8, 9, 5),
                (10, 11, 6),
            ],
            "Veld Age": [
                (1, 5, 1),
                (6, 10, 2),
                (11, 15, 3),
                (16, 20, 4),
                (21, 25, 5),
                (26, 30, 6),
                (31, 35, 7),
            ]
        }

        for cat_name, bands in numeric_defaults.items():
            print("Loading numeric categories: ", cat_name)

            cat = category_objs[cat_name]
            for low, high, priority in bands:
                NumericPriorityBand.objects.get_or_create(
                    category=cat,
                    range_low=low,
                    range_high=high,
                    priority=priority
                )

        # Step 3: Add default text priority values
        text_defaults = {
            "Owner": [
                ("CapeNature", 1),
                ("Dam Surroundings", 2),
                ("Farm", 3),
                ("Home owner", 4),
                ("Urban", 5),
                ("Private mountain catchment", 6),
                ("State Land", 7),
            ],
            "Vegetation Status": [
                ("LT", 1),
                ("E", 2),
                ("DE", 3),
                ("CE", 4),
                ("T", 5),
            ]
        }

        for cat_name, values in text_defaults.items():
            print("Loading text categories: ", cat_name)

            cat = category_objs[cat_name]
            for value, priority in values:
                TextPriorityValue.objects.get_or_create(
                    category=cat,
                    text_value=value,
                    priority=priority
                )

        self.stdout.write(self.style.SUCCESS('Default data loaded successfully.'))

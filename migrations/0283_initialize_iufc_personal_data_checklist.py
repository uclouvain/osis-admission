from django.db import migrations, models

from admission.migrations.utils.initialize_iufc_admissions_personal_data_checklist import (
    initialize_iufc_admissions_personal_data_checklist,
)


def initialize_iufc_admissions_personal_data_checklist_migration(apps, schema_editor):
    BaseAdmission = apps.get_model('admission', 'BaseAdmission')

    initialize_iufc_admissions_personal_data_checklist(model_class=BaseAdmission)


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0282_merge_20260119_1021'),
    ]

    operations = [
        migrations.RunPython(
            code=initialize_iufc_admissions_personal_data_checklist_migration,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="categorizedfreedocument",
            name="checklist_tab",
            field=models.CharField(
                blank=True,
                choices=[
                    (
                        "General education",
                        [
                            ("donnees_personnelles", "Personal data"),
                            ("assimilation", "Belgian student status"),
                            ("frais_dossier", "Application fee"),
                            ("parcours_anterieur", "Previous experience"),
                            ("experiences_parcours_anterieur", "Previous experiences"),
                            ("financabilite", "Financeability"),
                            ("choix_formation", "Course choice"),
                            ("specificites_formation", "Training specificities"),
                            ("decision_facultaire", "Decision of the faculty"),
                            ("decision_sic", "Decision of SIC"),
                        ],
                    ),
                    (
                        "Continuing education",
                        [
                            ("fiche_etudiant", "Student report"),
                            ("decision", "Decision"),
                            ("donnees_personnelles", "Personal data"),
                        ],
                    ),
                    (
                        "Doctorate education",
                        [
                            ("donnees_personnelles", "Personal data"),
                            ("assimilation", "Belgian student status"),
                            ("parcours_anterieur", "Previous experience"),
                            ("experiences_parcours_anterieur", "Previous experiences"),
                            ("financabilite", "Financeability"),
                            ("choix_formation", "Course choice"),
                            ("projet_recherche", "Research"),
                            ("decision_cdd", "Decision of the CDD"),
                            ("decision_sic", "Decision of SIC"),
                        ],
                    ),
                ],
                default="",
                max_length=255,
                verbose_name="Checklist tab",
            ),
        ),
    ]

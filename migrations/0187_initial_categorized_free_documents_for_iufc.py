# Generated by Django 3.2.25 on 2024-03-26 11:05

from django.db import migrations

from admission.models.categorized_free_document import TOKEN_ACADEMIC_YEAR
from admission.ddd.admission.formation_continue.domain.model.enums import OngletsChecklist


def initialize_categorized_free_documents(apps, schema_editor):
    """Initialize the categorized free documents"""

    CategorizedFreeDocument = apps.get_model('admission', 'CategorizedFreeDocument')

    categorized_free_documents = [
        CategorizedFreeDocument(
            checklist_tab=OngletsChecklist.fiche_etudiant.name,
            short_label_fr="Diplôme",
            with_academic_year=True,
            long_label_fr=f"Diplôme : {TOKEN_ACADEMIC_YEAR}",
            long_label_en=f"Diploma: {TOKEN_ACADEMIC_YEAR}",
        ),
        CategorizedFreeDocument(
            checklist_tab=OngletsChecklist.fiche_etudiant.name,
            short_label_fr="Curriculum vitae détaillé daté et signé",
            with_academic_year=False,
            long_label_fr="Curriculum vitae détaillé, daté et signé",
            long_label_en="Detailed curriculum vitae, dated and signed",
        ),
        CategorizedFreeDocument(
            checklist_tab=OngletsChecklist.fiche_etudiant.name,
            short_label_fr="Titre de séjour",
            with_academic_year=False,
            long_label_fr="Copie du titre de séjour qui couvre la totalité de la formation, épreuve d’évaluation "
            "comprise (sauf pour les formations organisées en ligne)",
            long_label_en="Copy of residence permit covering entire course, including assessment test "
            "(except for online courses).",
        ),
        CategorizedFreeDocument(
            checklist_tab=OngletsChecklist.fiche_etudiant.name,
            short_label_fr="Visa belge",
            with_academic_year=False,
            long_label_fr="Visa belge",
            long_label_en="Belgian visa",
        ),
    ]

    CategorizedFreeDocument.objects.bulk_create(categorized_free_documents)


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0186_alter_generaleducationadmission_refusal_type'),
    ]

    operations = [
        migrations.RunPython(code=initialize_categorized_free_documents, reverse_code=migrations.RunPython.noop)
    ]

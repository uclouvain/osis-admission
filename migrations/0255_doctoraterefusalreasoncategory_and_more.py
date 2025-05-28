# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################

import uuid

import ckeditor.fields
import django.db.models.deletion
import osis_document.contrib.fields
from django.db import migrations, models


def populate_refusal_reasons(apps, schema_editor):
    DoctorateRefusalReasonCategory = apps.get_model('admission', 'DoctorateRefusalReasonCategory')
    DoctorateRefusalReason = apps.get_model('admission', 'DoctorateRefusalReason')

    category_reasons = {
        'Titre requis insuffisant': [
            "Vous n'êtes pas titulaire du titre requis suffisant pour le programme visé.",
            "Votre formation initiale ne comporte pas l'équivalent de 300 crédits.",
            "Votre diplôme n'est pas issu d'une institution universitaire reconnue par l'un des sites officiels "
            "suivants "
            " <a href=\"https://www.whed.net/\" target=\"_blank\">"
            "https://www.whed.net/</a> ou "
            " <a href=\"https://www.enic-naric.net/\" target=\"_blank\">"
            "https://www.enic-naric.net/</a>.",
        ],
        'Résultats insuffisants': [
            "Vos résultats académiques ne satisfont pas aux critères d'admission.",
        ],
        'Prérequis insuffisants': [
            "Votre formation ne couvre pas les prérequis du programme visé.",
            "La durée de votre formation est insuffisante.",
        ],
        'Niveau de langue insuffisant/absent': [
            "Votre niveau de langue est insuffisant par rapport à celui exigé.",
            "La preuve du niveau de langue requis n'a pas été apportée.",
        ],
        'Finançabilité': [],
    }

    for category_order, (category_name, reasons) in enumerate(category_reasons.items()):
        category = DoctorateRefusalReasonCategory.objects.create(order=category_order, name=category_name)

        for reason_order, reason_name in enumerate(reasons):
            DoctorateRefusalReason.objects.create(order=reason_order, category=category, name=reason_name)


def migrate_newer_predefined_refusal_reasons_on_reverse(apps, schema_editor):
    """The new predefined reasons will be moved to the other reasons field."""
    DoctorateAdmission = apps.get_model('admission', 'DoctorateAdmission')

    doctorate_refusal_reasons = DoctorateAdmission.refusal_reasons.through.objects.select_related(
        'doctorateadmission',
        'doctoraterefusalreason',
    )

    doctorates_to_update = {}
    for doctorate_refusal_reason in doctorate_refusal_reasons:
        current_doctorate = doctorate_refusal_reason.doctorateadmission

        if current_doctorate.pk in doctorates_to_update:
            current_doctorate = doctorates_to_update[current_doctorate.pk]
        else:
            doctorates_to_update[current_doctorate.pk] = current_doctorate

        current_doctorate.other_refusal_reasons.append(doctorate_refusal_reason.doctoraterefusalreason.name)

    DoctorateAdmission.objects.bulk_update(list(doctorates_to_update.values()), fields=['other_refusal_reasons'])
    doctorate_refusal_reasons.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("admission", "0254_doctoraterefusalreason_old_data_migration"),
    ]

    operations = [
        migrations.CreateModel(
            name="DoctorateRefusalReasonCategory",
            fields=[
                (
                    "order",
                    models.PositiveIntegerField(db_index=True, editable=False, verbose_name="order"),
                ),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=255, verbose_name="Name")),
            ],
            options={
                "verbose_name": "Doctorate refusal reason category",
                "verbose_name_plural": "Doctorate refusal reason categories",
                "ordering": ("order",),
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="DoctorateRefusalReason",
            fields=[
                (
                    "order",
                    models.PositiveIntegerField(db_index=True, editable=False, verbose_name="order"),
                ),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", ckeditor.fields.RichTextField(verbose_name="Name")),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="admission.doctoraterefusalreasoncategory",
                        verbose_name="Category",
                    ),
                ),
            ],
            options={
                "verbose_name": "Doctorate refusal reason",
                "verbose_name_plural": "Doctorate refusal reasons",
                "ordering": ("order",),
                "abstract": False,
            },
        ),
        migrations.AlterField(
            model_name="doctorateadmission",
            name="refusal_reasons",
            field=models.ManyToManyField(
                blank=True,
                related_name="+",
                to="admission.doctoraterefusalreason",
                verbose_name="Refusal reasons",
            ),
        ),
        migrations.AddField(
            model_name="doctorateadmission",
            name="cdd_refusal_certificate",
            field=osis_document.contrib.fields.FileField(
                base_field=models.UUIDField(),
                blank=True,
                default=list,
                size=None,
                verbose_name="Refusal certificate of the CDD",
            ),
        ),
        migrations.RunPython(
            code=populate_refusal_reasons,
            reverse_code=migrate_newer_predefined_refusal_reasons_on_reverse,
        ),
    ]

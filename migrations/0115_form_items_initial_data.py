# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import sys

from django.conf import settings
from django.db import migrations

from admission.ddd.admission.domain.enums import TypeFormation
from admission.ddd.admission.enums import (
    TypeItemFormulaire,
    CritereItemFormulaireFormation,
    Onglets,
    CritereItemFormulaireLangueEtudes,
)
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.models.enums.education_group_types import TrainingType


def forward(apps, schema_editor):
    AdmissionFormItem = apps.get_model('admission', 'AdmissionFormItem')
    AdmissionFormItemInstantiation = apps.get_model('admission', 'AdmissionFormItemInstantiation')

    AcademicYear = apps.get_model('base', 'AcademicYear')
    EducationGroup = apps.get_model('base', 'EducationGroup')
    EducationGroupType = apps.get_model('base', 'EducationGroupType')

    academic_year = AcademicYear.objects.filter(year=2023).first()

    if not academic_year:
        return

    title = "Une lettre de motivation"
    tooltip = (
        "En fonction du programme sollicité, veuillez préciser dans votre lettre de "
        "motivation votre choix de finalité, spécialité, combinaison de langues ou "
        "options si nécessaires. Votre lettre doit également inclure les motivations "
        "de votre projet d’études."
    )

    # Motivation letter
    form_item = AdmissionFormItem.objects.create(
        internal_label="Lettre de motivation",
        type=TypeItemFormulaire.DOCUMENT.name,
        title={
            settings.LANGUAGE_CODE_EN: title,
            settings.LANGUAGE_CODE_FR: title,
        },
        text={
            settings.LANGUAGE_CODE_EN: tooltip,
            settings.LANGUAGE_CODE_FR: tooltip,
        },
        help_text={},
        values=[],
        configuration={},
    )

    # All masters, specialized masters, PHD, CAPAES et certificates
    for education_group_type in EducationGroupType.objects.filter(
        name__in=(
            AnneeInscriptionFormationTranslator.OSIS_ADMISSION_EDUCATION_TYPES_MAPPING[TypeFormation.MASTER.name]
            + AnneeInscriptionFormationTranslator.OSIS_ADMISSION_EDUCATION_TYPES_MAPPING[TypeFormation.DOCTORAT.name]
            + [TrainingType.CAPAES.name, TrainingType.CERTIFICATE.name]
        )
    ):
        AdmissionFormItemInstantiation.objects.create(
            form_item=form_item,
            academic_year=academic_year,
            weight=0,
            required=True,
            display_according_education=CritereItemFormulaireFormation.TYPE_DE_FORMATION.name,
            education_group_type=education_group_type,
            tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
        )

    # French language proficiency exam
    title = (
        "Attestation de réussite du test de 2ème cycle de l'examen de maîtrise de la langue française "
        "(informations : https://uclouvain.be/fr/etudier/inscriptions/emlf-aess.html)"
    )
    tooltip = ""

    form_item = AdmissionFormItem.objects.create(
        internal_label="Examen de maitrise de la langue française",
        type=TypeItemFormulaire.DOCUMENT.name,
        title={
            settings.LANGUAGE_CODE_EN: title,
            settings.LANGUAGE_CODE_FR: title,
        },
        text={},
        help_text={},
        values=[],
        configuration={},
    )

    # Didactic masters and aggregations
    for education_group_type in EducationGroupType.objects.filter(
        name__in=[
            TrainingType.MASTER_MD_120.name,
            TrainingType.MASTER_MD_180_240.name,
            TrainingType.AGGREGATION.name,
        ]
    ):
        AdmissionFormItemInstantiation.objects.create(
            form_item=form_item,
            academic_year=academic_year,
            weight=0,
            required=False,
            display_according_education=CritereItemFormulaireFormation.TYPE_DE_FORMATION.name,
            education_group_type=education_group_type,
            study_language=CritereItemFormulaireLangueEtudes.AUCUNE_ETUDE_FR.name,
            tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
        )

    # Medicine and dentistry question
    title = (
        "Attestation de réussite au concours d'entrée en médecine pour l'UCLouvain "
        "(https://www.mesetudes.be/concoursmd/)"
    )
    tooltip = (
        "Si vous n'avez pas encore présenté le concours, veuillez fournir la preuve d'inscription au concours. "
        "Si vous n'êtes pas encore inscrit·e au concours, vous ne devez joindre aucun document à ce stade."
    )

    form_item = AdmissionFormItem.objects.create(
        internal_label='Concours médecine et dentisterie',
        type=TypeItemFormulaire.DOCUMENT.name,
        title={
            settings.LANGUAGE_CODE_EN: title,
            settings.LANGUAGE_CODE_FR: title,
        },
        text={
            settings.LANGUAGE_CODE_EN: tooltip,
            settings.LANGUAGE_CODE_FR: tooltip,
        },
        help_text={},
        values=[],
        configuration={},
    )

    for education_group in EducationGroup.objects.filter(
        uuid__in=[
            "2661a933-389d-4732-bcce-02743692204d",  # MD1BA
            "143c119f-b89a-4ef8-aa6d-865c4dd4b491",  # DENT1BA
        ]
    ):
        AdmissionFormItemInstantiation.objects.create(
            form_item=form_item,
            academic_year=academic_year,
            weight=1,
            required=False,
            display_according_education=CritereItemFormulaireFormation.UNE_FORMATION.name,
            education_group=education_group,
            tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
        )

    # Admission exam - mathematics part question
    title = "Attestation de réussite de l’examen d’accès aux études d’ingénieur."
    tooltip = (
        "Si vous n'avez pas encore présenté l'examen d'accès aux études d'ingénieur, veuillez fournir la preuve "
        "d'inscription. Si vous n'êtes pas encore inscrit·e à l'examen, vous ne devez joindre aucun document à "
        "ce stade."
    )
    form_item = AdmissionFormItem.objects.create(
        internal_label="Examen d'admission - partie mathématique",
        type=TypeItemFormulaire.DOCUMENT.name,
        title={
            settings.LANGUAGE_CODE_EN: title,
            settings.LANGUAGE_CODE_FR: title,
        },
        text={
            settings.LANGUAGE_CODE_EN: tooltip,
            settings.LANGUAGE_CODE_FR: tooltip,
        },
        help_text={},
        values=[],
        configuration={},
    )

    for training in EducationGroup.objects.filter(
        uuid__in=[
            "1ed59fe9-3907-4570-a2c2-6a877ffb97ca",  # FSA1BA
            "7b9d47fe-63b7-402c-b5b7-7725eff7b272",  # ARCH1BA
        ]
    ):
        AdmissionFormItemInstantiation.objects.create(
            form_item=form_item,
            academic_year=academic_year,
            weight=1,
            required=True,
            display_according_education=CritereItemFormulaireFormation.UNE_FORMATION.name,
            education_group=training,
            tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0114_auto_20230808_1838'),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]

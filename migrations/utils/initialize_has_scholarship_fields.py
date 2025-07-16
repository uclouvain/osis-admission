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
from django.db.models import Value

from admission.ddd.admission.shared_kernel.domain.enums import TypeFormation
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)


def initialize_has_scholarship_fields(admission_class, on_migration=True):
    """
    Initialize the values of the fields has_[scholarship_field] depending on the scholarship fields.
    :param on_migration: True if this method is used in a migration, False otherwise
    :param admission_class: The admission model class
    """
    master_admissions = admission_class.objects.filter(
        baseadmission_ptr__training__education_group_type__name__in=(
            AnneeInscriptionFormationTranslator.OSIS_ADMISSION_EDUCATION_TYPES_MAPPING[TypeFormation.MASTER.name]
        ),
    )

    if on_migration:
        # Otherwise, the field is not found (FieldDoesNotExist exception)
        master_admissions = master_admissions.annotate(created_at=Value(''))

    for admission in master_admissions:
        admission.has_double_degree_scholarship = bool(admission.double_degree_scholarship_id)
        admission.has_international_scholarship = bool(admission.international_scholarship_id)
        admission.has_erasmus_mundus_scholarship = bool(admission.erasmus_mundus_scholarship_id)

    admission_class.objects.bulk_update(
        objs=master_admissions,
        fields=[
            'has_double_degree_scholarship',
            'has_international_scholarship',
            'has_erasmus_mundus_scholarship',
        ],
        batch_size=1000,
    )

    return master_admissions

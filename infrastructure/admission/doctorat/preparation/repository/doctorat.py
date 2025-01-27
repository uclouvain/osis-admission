# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from typing import Optional

from django.conf import settings
from django.utils.translation import get_language

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import (
    DoctoratIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    DoctoratNonTrouveException,
)
from admission.ddd.admission.doctorat.preparation.dtos.doctorat import DoctoratDTO
from admission.ddd.admission.doctorat.preparation.repository.i_doctorat import (
    IDoctoratRepository,
)
from admission.models import DoctorateAdmission
from admission.models.doctorate import PropositionProxy
from base.models.student import Student
from infrastructure.reference.domain.service.bourse import BourseTranslator


class DoctoratRepository(IDoctoratRepository):

    @classmethod
    def verifier_existence(cls, entity_id: 'DoctoratIdentity') -> None:  # pragma: no cover
        doctorate: DoctorateAdmission = DoctorateAdmission.objects.filter(uuid=entity_id.uuid)
        if not doctorate:
            raise DoctoratNonTrouveException

    @classmethod
    def get_dto(cls, entity_id: 'DoctoratIdentity') -> 'DoctoratDTO':
        try:
            doctorate: DoctorateAdmission = PropositionProxy.objects.for_dto().get(uuid=entity_id.uuid)
        except DoctorateAdmission.DoesNotExist:
            raise DoctoratNonTrouveException

        student: Optional[Student] = Student.objects.filter(person=doctorate.candidate).first()

        return DoctoratDTO(
            uuid=str(entity_id.uuid),
            reference=doctorate.formatted_reference,
            matricule_doctorant=doctorate.candidate.global_id,
            nom_doctorant=doctorate.candidate.last_name,
            prenom_doctorant=doctorate.candidate.first_name,
            genre_doctorant=doctorate.candidate.gender,
            annee_formation=doctorate.doctorate.academic_year.year,
            sigle_formation=doctorate.doctorate.acronym,
            noma_doctorant=student.registration_id if student else '',
            intitule_formation=(
                doctorate.doctorate.title
                if get_language() == settings.LANGUAGE_CODE_FR
                else doctorate.doctorate.title_english
            ),
            type_admission=doctorate.type,
            titre_these=doctorate.project_title,
            type_financement=doctorate.financing_type,
            autre_bourse_recherche=doctorate.other_international_scholarship,
            bourse_recherche=(
                BourseTranslator.build_dto(doctorate.international_scholarship)
                if doctorate.international_scholarship
                else None
            ),
            admission_acceptee_le=None,  # TODO to add when the field will be added to the model
        )

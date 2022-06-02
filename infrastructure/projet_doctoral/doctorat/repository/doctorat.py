# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Optional, List

from django.conf import settings
from django.utils.translation import get_language

from admission.contrib.models.doctorate import DoctorateProxy, DoctorateAdmission
from admission.ddd.projet_doctoral.doctorat.domain.model._formation import FormationIdentity
from admission.ddd.projet_doctoral.doctorat.domain.model.doctorat import DoctoratIdentity, Doctorat
from admission.ddd.projet_doctoral.doctorat.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.projet_doctoral.doctorat.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.projet_doctoral.doctorat.dtos import DoctoratDTO
from admission.ddd.projet_doctoral.doctorat.repository.i_doctorat import IDoctoratRepository
from osis_common.ddd.interface import EntityIdentity, RootEntity, ApplicationService


class DoctoratRepository(IDoctoratRepository):
    @classmethod
    def delete(cls, entity_id: EntityIdentity, **kwargs: ApplicationService) -> None:
        raise NotImplementedError

    @classmethod
    def search(cls, entity_ids: Optional[List[EntityIdentity]] = None, **kwargs) -> List[RootEntity]:
        raise NotImplementedError

    @classmethod
    def get(cls, entity_id: 'DoctoratIdentity') -> 'Doctorat':
        try:
            doctorate: DoctorateProxy = DoctorateProxy.objects.get(uuid=entity_id.uuid)
        except DoctorateProxy.DoesNotExist:
            raise DoctoratNonTrouveException

        return Doctorat(
            entity_id=entity_id,
            statut=ChoixStatutDoctorat[doctorate.post_enrolment_status],
            formation_id=FormationIdentity(doctorate.doctorate.acronym, doctorate.doctorate.academic_year.year),
            reference=doctorate.reference,
            matricule_doctorant=doctorate.candidate.global_id,
        )

    @classmethod
    def save(cls, entity: 'Doctorat') -> None:
        DoctorateAdmission.objects.update_or_create(
            uuid=entity.entity_id.uuid,
            defaults={
                'post_enrolment_status': entity.statut.name
            },
        )

    @classmethod
    def get_dto(cls, entity_id: 'DoctoratIdentity') -> 'DoctoratDTO':
        try:
            doctorate: DoctorateProxy = DoctorateProxy.objects.get(uuid=entity_id.uuid)
        except DoctorateProxy.DoesNotExist:
            raise DoctoratNonTrouveException

        return DoctoratDTO(
            uuid=str(entity_id.uuid),
            statut=ChoixStatutDoctorat[doctorate.post_enrolment_status].name,
            reference=doctorate.reference,
            matricule_doctorant=doctorate.candidate.global_id,
            nom_doctorant=doctorate.candidate.last_name,
            prenom_doctorant=doctorate.candidate.first_name,
            annee_formation=doctorate.doctorate.academic_year.year,
            sigle_formation=doctorate.doctorate.acronym,
            intitule_formation=doctorate.doctorate.title
            if get_language() == settings.LANGUAGE_CODE_FR
            else doctorate.doctorate.title_english,
        )

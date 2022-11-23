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
from typing import List, Optional

from django.conf import settings
from django.utils.translation import get_language

from admission.auth.roles.candidate import Candidate
from admission.contrib.models import GeneralEducationAdmissionProxy, Scholarship
from admission.contrib.models.general_education import GeneralEducationAdmission
from admission.ddd.admission.domain.builder.formation_identity import FormationIdentityBuilder
from admission.ddd.admission.domain.model.bourse import BourseIdentity
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.enums.type_bourse import TypeBourse
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutProposition
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.admission.formation_generale.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.formation_generale.dtos import PropositionDTO
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from admission.infrastructure.admission.domain.service.bourse import BourseTranslator
from base.models.education_group_year import EducationGroupYear
from base.models.person import Person
from osis_common.ddd.interface import ApplicationService


class PropositionRepository(IPropositionRepository):
    @classmethod
    def search(
        cls,
        entity_ids: Optional[List['PropositionIdentity']] = None,
        matricule_candidat: str = None,
        **kwargs,
    ) -> List['Proposition']:
        raise NotImplementedError

    @classmethod
    def search_dto(cls, matricule_candidat: Optional[str] = '') -> List['PropositionDTO']:
        # Default queryset
        qs = GeneralEducationAdmissionProxy.objects.all()

        # Add filters
        if matricule_candidat:
            qs = qs.filter(candidate__global_id=matricule_candidat)

        # Return dtos
        return [cls._load_dto(proposition) for proposition in qs]

    @classmethod
    def delete(cls, entity_id: 'PropositionIdentity', **kwargs: ApplicationService) -> None:
        raise NotImplementedError

    @classmethod
    def get(cls, entity_id: 'PropositionIdentity') -> 'Proposition':
        try:
            return cls._load(GeneralEducationAdmissionProxy.objects.get(uuid=entity_id.uuid))
        except GeneralEducationAdmission.DoesNotExist:
            raise PropositionNonTrouveeException

    @classmethod
    def save(cls, entity: 'Proposition') -> None:
        training = EducationGroupYear.objects.get(
            acronym=entity.formation_id.sigle,
            academic_year__year=entity.formation_id.annee,
        )
        candidate = Person.objects.get(global_id=entity.matricule_candidat)

        scholarships_uuids = list(
            scholarship.uuid
            for scholarship in [
                entity.bourse_double_diplome_id,
                entity.bourse_erasmus_mundus_id,
                entity.bourse_internationale_id,
            ]
            if scholarship
        )

        if scholarships_uuids:
            scholarships = {
                scholarship.type: scholarship
                for scholarship in Scholarship.objects.filter(
                    uuid__in=scholarships_uuids,
                )
            }
        else:
            scholarships = {}

        GeneralEducationAdmission.objects.update_or_create(
            uuid=entity.entity_id.uuid,
            defaults={
                'candidate': candidate,
                'training': training,
                'double_degree_scholarship': scholarships.get(TypeBourse.DOUBLE_TRIPLE_DIPLOMATION.name),
                'international_scholarship': scholarships.get(TypeBourse.BOURSE_INTERNATIONALE_FORMATION_GENERALE.name),
                'erasmus_mundus_scholarship': scholarships.get(TypeBourse.ERASMUS_MUNDUS.name),
                'is_external_reorientation': entity.est_reorientation_inscription_externe,
                'is_external_modification': entity.est_modification_inscription_externe,
                'is_non_resident': entity.est_non_resident_au_sens_decret,
                'status': entity.statut.name,
                'specific_question_answers': entity.reponses_questions_specifiques,
            },
        )

        Candidate.objects.get_or_create(person=candidate)

    @classmethod
    def get_dto(cls, entity_id: 'PropositionIdentity') -> 'PropositionDTO':
        try:
            return cls._load_dto(GeneralEducationAdmissionProxy.objects.get(uuid=entity_id.uuid))
        except GeneralEducationAdmission.DoesNotExist:
            raise PropositionNonTrouveeException

    @classmethod
    def _load(cls, admission: 'GeneralEducationAdmission') -> 'Proposition':
        return Proposition(
            entity_id=PropositionIdentityBuilder().build_from_uuid(admission.uuid),
            matricule_candidat=admission.candidate.global_id,
            creee_le=admission.created,
            modifiee_le=admission.modified,
            formation_id=FormationIdentityBuilder.build(
                sigle=admission.training.acronym,
                annee=admission.training.academic_year.year,
            ),
            statut=ChoixStatutProposition[admission.status],
            bourse_internationale_id=BourseIdentity(uuid=str(admission.international_scholarship.uuid))
            if admission.international_scholarship
            else None,
            bourse_double_diplome_id=BourseIdentity(uuid=str(admission.double_degree_scholarship.uuid))
            if admission.double_degree_scholarship
            else None,
            bourse_erasmus_mundus_id=BourseIdentity(uuid=str(admission.erasmus_mundus_scholarship.uuid))
            if admission.erasmus_mundus_scholarship
            else None,
            reponses_questions_specifiques=admission.specific_question_answers,
            est_reorientation_inscription_externe=admission.is_external_reorientation,
            est_modification_inscription_externe=admission.is_external_modification,
            est_non_resident_au_sens_decret=admission.is_non_resident,
        )

    @classmethod
    def _load_dto(cls, admission: GeneralEducationAdmission) -> 'PropositionDTO':
        return PropositionDTO(
            uuid=admission.uuid,
            creee_le=admission.created,
            modifiee_le=admission.modified,
            erreurs=admission.detailed_status or [],
            statut=admission.status,
            formation=FormationDTO(
                sigle=admission.training.acronym,
                annee=admission.training.academic_year.year,
                intitule=admission.training.title
                if get_language() == settings.LANGUAGE_CODE
                else admission.training.title_english,
                campus=admission.teaching_campus or '',
            ),
            matricule_candidat=admission.candidate.global_id,
            prenom_candidat=admission.candidate.first_name,
            nom_candidat=admission.candidate.last_name,
            bourse_double_diplome=BourseTranslator.build_dto(admission.double_degree_scholarship)
            if admission.double_degree_scholarship
            else None,
            bourse_internationale=BourseTranslator.build_dto(admission.international_scholarship)
            if admission.international_scholarship
            else None,
            bourse_erasmus_mundus=BourseTranslator.build_dto(admission.erasmus_mundus_scholarship)
            if admission.erasmus_mundus_scholarship
            else None,
            reponses_questions_specifiques=admission.specific_question_answers,
        )

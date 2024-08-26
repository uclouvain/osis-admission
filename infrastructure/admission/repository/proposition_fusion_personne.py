# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import contextlib
import logging
import re
from typing import Optional, List

from django.conf import settings

from admission.ddd.admission.domain.model.proposition_fusion_personne import PropositionFusionPersonneIdentity
from admission.ddd.admission.domain.validator.exceptions import PasDePropositionFusionPersonneTrouveeException
from admission.ddd.admission.dtos.proposition_fusion_personne import PropositionFusionPersonneDTO
from admission.ddd.admission.repository.i_proposition_fusion_personne import IPropositionPersonneFusionRepository
from admission.templatetags.admission import format_matricule
from base.business.student import find_student_by_discriminating
from base.models.person import Person
from base.models.person_merge_proposal import PersonMergeProposal, PersonMergeStatus
from base.models.student import Student
from osis_common.utils.models import get_object_or_none
from reference.models.country import Country

logger = logging.getLogger(settings.DEFAULT_LOGGER)


class PropositionPersonneFusionRepository(IPropositionPersonneFusionRepository):
    @classmethod
    def initialiser(
            cls,
            existing_merge_person_id: Optional[str],
            status: str,
            global_id: str,
            selected_global_id: str,
            nom: str,
            prenom: str,
            autres_prenoms: str,
            date_naissance: str,
            lieu_naissance: str,
            email: str,
            genre: str,
            sex: str,
            etat_civil: str,
            nationalite: str,
            numero_national: str,
            numero_carte_id: str,
            numero_passeport: str,
            dernier_noma_connu: str,
            expiration_carte_id: str,
            expiration_passeport: str,
            educational_curex_ids: List[str],
            professional_curex_ids: List[str],
    ) -> PropositionFusionPersonneIdentity:  # noqa

        country_of_citizenship = get_object_or_none(Country, name=nationalite)

        merge_person, created = Person.objects.update_or_create(
            id=existing_merge_person_id,
            defaults={
                'last_name': nom,
                'first_name': prenom,
                'middle_name': autres_prenoms,
                'birth_date': date_naissance,
                'birth_place': lieu_naissance,
                'email': email,
                'gender': genre,
                'sex': sex,
                'civil_state': etat_civil,
                'country_of_citizenship': country_of_citizenship,
                'national_number': numero_national,
                'id_card_number': numero_carte_id,
                'passport_number': numero_passeport,
                'last_registration_id': dernier_noma_connu,
                'id_card_expiry_date': expiration_carte_id,
                'passport_expiry_date': expiration_passeport,
            }
        )

        person_merge_proposal = PersonMergeProposal.objects.get(original_person__global_id=global_id)
        person_merge_proposal.proposal_merge_person_id = merge_person.id
        person_merge_proposal.status = PersonMergeStatus.IN_PROGRESS.name if status == "MERGE" else \
            PersonMergeStatus.PENDING.name
        person_merge_proposal.selected_global_id = selected_global_id
        person_merge_proposal.registration_id_sent_to_digit = cls._extract_registration_id_from_selected_global_id(
            person_merge_proposal,
            selected_global_id
        )
        person_merge_proposal.professional_curex_to_merge = professional_curex_ids
        person_merge_proposal.educational_curex_to_merge = educational_curex_ids
        person_merge_proposal.save()
        return PropositionFusionPersonneIdentity(uuid=person_merge_proposal.uuid)

    @classmethod
    def _extract_registration_id_from_selected_global_id(
        self,
        person_merge_proposal: PersonMergeProposal,
        selected_global_id: str,
    ) -> str:
        student = find_student_by_discriminating(qs=Student.objects.filter(person__global_id=selected_global_id))
        if student is not None and student.registration_id:
            return student.registration_id

        with contextlib.suppress(StopIteration):
            if isinstance(person_merge_proposal.similarity_result, list):
                selected_result = next(
                    selected_result for selected_result in person_merge_proposal.similarity_result
                    if format_matricule(selected_result['person']['matricule']) == selected_global_id
                )
                return next(app['sourceId'] for app in selected_result['applicationAccounts'] if app['source'] == 'ETU')
        return ""

    @classmethod
    def get(cls, global_id: str) -> Optional[PropositionFusionPersonneDTO]:
        person_merge_proposal = PersonMergeProposal.objects.filter(
            original_person__global_id=global_id,
        ).exclude(selected_global_id='').first()
        if not person_merge_proposal:
            return None

        country = person_merge_proposal.proposal_merge_person.country_of_citizenship \
            if person_merge_proposal.proposal_merge_person else None
        person = person_merge_proposal.proposal_merge_person \
            if person_merge_proposal.proposal_merge_person else person_merge_proposal.original_person
        return PropositionFusionPersonneDTO(
            status=person_merge_proposal.status,
            matricule=person_merge_proposal.selected_global_id,
            original_person_uuid=person_merge_proposal.original_person.uuid,
            first_name=person.first_name,
            last_name=person.last_name,
            other_name=person.middle_name,
            birth_date=person.birth_date,
            sex=person.sex,
            gender=person.gender,
            birth_place=person.birth_place,
            birth_country=person.birth_country,
            civil_state=person.civil_state,
            country_of_citizenship=country.name if country else None,
            national_number=person.national_number,
            id_card_number=person.id_card_number,
            passport_number=person.passport_number,
            id_card_expiry_date=person.id_card_expiry_date,
            professional_curex_uuids=person_merge_proposal.professional_curex_to_merge,
            educational_curex_uuids=person_merge_proposal.educational_curex_to_merge,
            validation=person_merge_proposal.validation,
            last_registration_id=person.last_registration_id,
        )

    @classmethod
    def defaire(cls, global_id: str) -> PropositionFusionPersonneIdentity:
        person_merge_proposal = PersonMergeProposal.objects.filter(
            original_person__global_id=global_id,
        ).exclude(selected_global_id='').first()
        if not person_merge_proposal:
            raise PasDePropositionFusionPersonneTrouveeException

        person_merge_proposal.status = PersonMergeStatus.MATCH_FOUND.name
        person_merge_proposal.selected_global_id = ''
        person_merge_proposal.registration_id_sent_to_digit = ''
        person_merge_proposal.professional_curex_to_merge = []
        person_merge_proposal.educational_curex_to_merge = []
        person_merge_proposal.proposal_merge_person = None
        person_merge_proposal.save()
        return PropositionFusionPersonneIdentity(uuid=person_merge_proposal.uuid)

    @classmethod
    def refuser(cls, global_id: str) -> PropositionFusionPersonneIdentity:
        person_merge_proposal = PersonMergeProposal.objects.get(original_person__global_id=global_id)
        if cls._peut_refuser_fusion(person_merge_proposal):
            person_merge_proposal.status = PersonMergeStatus.REFUSED.name
            person_merge_proposal.selected_global_id = ''
            person_merge_proposal.registration_id_sent_to_digit = ''
            person_merge_proposal.professional_curex_to_merge = []
            person_merge_proposal.educational_curex_to_merge = []
            person_merge_proposal.proposal_merge_person = None
            person_merge_proposal.save()
        # fail silently
        return PropositionFusionPersonneIdentity(uuid=person_merge_proposal.uuid)

    @classmethod
    def _peut_refuser_fusion(cls, person_merge_proposal):
        candidate = person_merge_proposal.original_person
        digit_results = person_merge_proposal.similarity_result
        for result in digit_results:
            # ne peut pas refuser fusion si NISS identiques
            if result['person']['nationalRegister'] and candidate.national_number and (
                    result['person']['nationalRegister'] == cls._only_digits(candidate.national_number)
            ):
                return False
        return True

    @classmethod
    def _only_digits(cls, input_string):
        return re.sub('[^0-9]', '', input_string)

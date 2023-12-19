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
from typing import Optional, List

from admission.ddd.admission.domain.model.proposition_fusion_personne import PropositionFusionPersonneIdentity
from admission.ddd.admission.dtos.proposition_fusion_personne import PropositionFusionPersonneDTO
from admission.ddd.admission.repository.i_proposition_fusion_personne import IPropositionPersonneFusionRepository
from base.models.person import Person
from base.models.person_merge_proposal import PersonMergeProposal, PersonMergeStatus
from osis_common.utils.models import get_object_or_none
from reference.models.country import Country


class PropositionPersonneFusionRepository(IPropositionPersonneFusionRepository):
    @classmethod
    def initialiser(
            cls,
            global_id: str,
            nom: str,
            prenom: str,
            autres_prenoms: str,
            date_naissance: str,
            lieu_naissance: str,
            email: str,
            genre: str,
            etat_civil: str,
            nationalite: str,
            numero_national: str,
            numero_carte_id: str,
            numero_passeport: str,
            dernier_noma_connu: str,
            expiration_carte_id: str,
            educational_curex_ids: List[str],
            professional_curex_ids: List[str],
    ) -> PropositionFusionPersonneIdentity:

        country_of_citizenship = Country.objects.get(name=nationalite)

        merge_person = Person.objects.create(
            last_name=nom,
            first_name=prenom,
            middle_name=autres_prenoms,
            birth_date=date_naissance,
            birth_place=lieu_naissance,
            email=email,
            gender=genre,
            civil_state=etat_civil,
            country_of_citizenship=country_of_citizenship,
            national_number=numero_national,
            id_card_number=numero_carte_id,
            passport_number=numero_passeport,
            last_registration_id=dernier_noma_connu,
            id_card_expiry_date=expiration_carte_id,
        )

        person_merge_proposal, created = PersonMergeProposal.objects.update_or_create(
            original_person__global_id=global_id,
            defaults={
                "proposal_merge_person_id": merge_person.id,
                "status": PersonMergeStatus.MERGED.name,
                "selected_global_id": "test",
                "professional_curex_to_merge": professional_curex_ids,
                "educational_curex_to_merge": educational_curex_ids,
            }
        )

        return PropositionFusionPersonneIdentity(uuid=person_merge_proposal.uuid)

    @classmethod
    def get(cls, global_id: str) -> Optional[PropositionFusionPersonneDTO]:
        person_merge_proposal = get_object_or_none(
            PersonMergeProposal, original_person__global_id=global_id
        )
        return PropositionFusionPersonneDTO(
            status=person_merge_proposal.status,
            matricule=person_merge_proposal.selected_global_id,
            original_person_uuid=person_merge_proposal.original_person.uuid,
            first_name=person_merge_proposal.proposal_merge_person.first_name,
            last_name=person_merge_proposal.proposal_merge_person.last_name,
            other_name=person_merge_proposal.proposal_merge_person.middle_name,
            birth_date=person_merge_proposal.proposal_merge_person.birth_date,
            sex=person_merge_proposal.proposal_merge_person.sex,
            gender=person_merge_proposal.proposal_merge_person.gender,
            birth_place=person_merge_proposal.proposal_merge_person.birth_place,
            birth_country=person_merge_proposal.proposal_merge_person.birth_country,
            civil_state=person_merge_proposal.proposal_merge_person.civil_state,
            country_of_citizenship=person_merge_proposal.proposal_merge_person.country_of_citizenship.name,
            national_number=person_merge_proposal.proposal_merge_person.national_number,
            id_card_number=person_merge_proposal.proposal_merge_person.id_card_number,
            passport_number=person_merge_proposal.proposal_merge_person.passport_number,
            id_card_expiry_date=person_merge_proposal.proposal_merge_person.id_card_expiry_date,
            professional_curex_uuids=person_merge_proposal.professional_curex_to_merge,
            educational_curex_uuids=person_merge_proposal.educational_curex_to_merge,
        ) if person_merge_proposal and person_merge_proposal.proposal_merge_person else None

    @classmethod
    def defaire(cls, global_id: str) -> PropositionFusionPersonneIdentity:
        person_merge_proposal, _ = PersonMergeProposal.objects.update_or_create(
            original_person__global_id=global_id,
            defaults={
                "status": PersonMergeStatus.MATCH_FOUND.name,
            }
        )
        return PropositionFusionPersonneIdentity(uuid=person_merge_proposal.uuid)

    @classmethod
    def refuser(cls, global_id: str) -> PropositionFusionPersonneIdentity:
        person_merge_proposal, _ = PersonMergeProposal.objects.update_or_create(
            original_person__global_id=global_id,
            defaults={
                "status": PersonMergeStatus.REFUSED.name,
            }
        )
        return PropositionFusionPersonneIdentity(uuid=person_merge_proposal.uuid)

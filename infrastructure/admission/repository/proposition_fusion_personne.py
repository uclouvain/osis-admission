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
import logging
import re
from typing import Optional, List

from django.apps import apps
from django.conf import settings
from django.db.models import Model, ForeignKey

from admission.contrib.models.base import BaseAdmission
from admission.ddd.admission.domain.model.proposition_fusion_personne import PropositionFusionPersonneIdentity
from admission.ddd.admission.domain.validator.exceptions import TicketDigitATraiterAvantException, \
    PasDePropositionDeFusionEligibleException
from admission.ddd.admission.dtos.proposition_fusion_personne import PropositionFusionPersonneDTO
from admission.ddd.admission.repository.i_proposition_fusion_personne import IPropositionPersonneFusionRepository
from base.models.person import Person
from base.models.person_creation_ticket import PersonTicketCreation, PersonTicketCreationMergeType, \
    PersonTicketCreationStatus
from base.models.person_merge_proposal import PersonMergeProposal, PersonMergeStatus
from osis_common.utils.models import get_object_or_none
from osis_profile.models import ProfessionalExperience, EducationalExperience
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

        person_merge_proposal, created = PersonMergeProposal.objects.update_or_create(
            original_person__global_id=global_id,
            defaults={
                "proposal_merge_person_id": merge_person.id,
                "status": PersonMergeStatus.IN_PROGRESS.name if status == "MERGE" else PersonMergeStatus.PENDING.name,
                "selected_global_id": selected_global_id,
                "professional_curex_to_merge": professional_curex_ids,
                "educational_curex_to_merge": educational_curex_ids,
            }
        )

        return PropositionFusionPersonneIdentity(uuid=person_merge_proposal.uuid)

    @classmethod
    def get(cls, global_id: str) -> Optional[PropositionFusionPersonneDTO]:
        person_merge_proposal = get_object_or_none(
            PersonMergeProposal,
            original_person__global_id=global_id,
        )
        if not person_merge_proposal or person_merge_proposal.selected_global_id == '':
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
        person_merge_proposal, _ = PersonMergeProposal.objects.update_or_create(
            original_person__global_id=global_id,
            defaults={
                "status": PersonMergeStatus.MATCH_FOUND.name,
            }
        )
        return PropositionFusionPersonneIdentity(uuid=person_merge_proposal.uuid)

    @classmethod
    def refuser(cls, global_id: str) -> PropositionFusionPersonneIdentity:
        person_merge_proposal = PersonMergeProposal.objects.get(original_person__global_id=global_id)
        if cls._peut_refuser_fusion(person_merge_proposal):
            person_merge_proposal.status = PersonMergeStatus.REFUSED.name
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

    @classmethod
    def fusionner(cls, candidate_global_id: str, ticket_uuid: str):

        cls.verifier_eligible_fusion(ticket_uuid)

        candidate = Person.objects.prefetch_related('personticketcreation_set').get(global_id=candidate_global_id)
        person_tickets = candidate.personticketcreation_set.all()

        ticket = next((t for t in person_tickets if str(t.uuid) == ticket_uuid), None)
        if not ticket:
            raise PersonTicketCreation.DoesNotExist

        if any(
                p for p in person_tickets if p.created_at < ticket.created_at and p.status not in [
                    PersonTicketCreationStatus.DONE.name,
                    PersonTicketCreationStatus.DONE_WITH_WARNINGS.name
                ]
        ):
            raise TicketDigitATraiterAvantException()

        person_merge_proposal = get_object_or_none(
            PersonMergeProposal, original_person__global_id=candidate_global_id
        )
        known_person_global_id = person_merge_proposal.selected_global_id
        known_person = get_object_or_none(Person, global_id=known_person_global_id)

        if known_person:
            person_to_merge = person_merge_proposal.proposal_merge_person
            cls._update_non_empty_fields(person_to_merge, known_person)
            known_person.save()

            models = cls._find_models_with_fk_to_person()
            for model, field_name in models:
                if model == BaseAdmission:
                    admissions = model.objects.filter(
                        **{field_name: person_merge_proposal.original_person}
                    )
                    for admission in admissions:
                        if admission.valuated_secondary_studies_person:
                            admission.valuated_secondary_studies_person = known_person
                            admission.candidate_id = known_person.id
                            admission.save()
                            logger.info(
                                f'Updated {admission} instances of {model.__name__} '
                                f'for fields valuated_secondary_studies_person and candidate_id.'
                            )
                        else:
                            admission.candidate_id = known_person.id
                            admission.save()
                            logger.info(
                                f'Updated {admission} instances of {model.__name__} for candidate_id.')
                elif model == ProfessionalExperience or model == EducationalExperience:
                    experiences = model.objects.filter(
                        **{field_name: person_merge_proposal.original_person}
                    )
                    curex_to_merge = (person_merge_proposal.professional_curex_to_merge +
                                      person_merge_proposal.educational_curex_to_merge)
                    for experience in experiences:
                        if experience.uuid in curex_to_merge:
                            experience.person_id = known_person.id
                            experience.save()
                        else:
                            experience.delete()
                else:
                    updated_count = model.objects.filter(
                        **{field_name: person_merge_proposal.original_person}
                    ).update(**{field_name: known_person})
                    logger.info(f'Updated {updated_count} instances of {model.__name__}.')

            person_merge_proposal.status = PersonMergeStatus.MERGED.name
            person_merge_proposal.save()

            # delete person_to_merge after merge
            person_to_merge.delete()

            ticket.merge_type = PersonTicketCreationMergeType.MERGED_WITH_KNOWN_PERSON.name
            ticket.save()


    @classmethod
    def _update_non_empty_fields(cls, source_obj: Model, target_obj: Model):
        """
        Update non-empty fields from source_obj to target_obj.
        """
        for field in source_obj._meta.fields:
            field_name = field.name
            source_value = getattr(source_obj, field_name)

            # Skip if the field is empty or uuid or it's the primary key
            if field.primary_key or field.name == 'uuid' or not source_value:
                continue

            setattr(target_obj, field_name, source_value)

    @classmethod
    def _find_models_with_fk_to_person(cls):
        models_with_fk = []
        for model in [model for model in apps.get_models() if model != PersonMergeProposal]:
            for field in model._meta.get_fields():
                if isinstance(field, ForeignKey) and field.related_model == Person:
                    models_with_fk.append((model, field.name))
        return models_with_fk

    @classmethod
    def verifier_eligible_fusion(cls, ticket_uuid: str):
        ticket = PersonTicketCreation.objects.get(uuid=ticket_uuid)
        person_merge_proposal = get_object_or_none(PersonMergeProposal, original_person=ticket.person)
        if not person_merge_proposal or person_merge_proposal.status != PersonMergeStatus.IN_PROGRESS.name:
            raise PasDePropositionDeFusionEligibleException

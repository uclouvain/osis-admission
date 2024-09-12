# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List
from uuid import UUID

import waffle
from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.db.models import Q, Model, ForeignKey
from django.shortcuts import redirect
from waffle.testutils import override_switch

from admission.auth.roles.candidate import Candidate
from admission.contrib.models import GeneralEducationAdmission
from admission.contrib.models.base import BaseAdmission, AdmissionEducationalValuatedExperiences, \
    AdmissionProfessionalValuatedExperiences
from admission.ddd.admission.commands import (
    RetrieveListeTicketsEnAttenteQuery,
    RetrieveAndStoreStatutTicketPersonneFromDigitCommand, RecupererMatriculeDigitQuery,
)
from admission.ddd.admission.dtos.statut_ticket_personne import StatutTicketPersonneDTO
from admission.ddd.admission.formation_generale.domain.model.enums import STATUTS_PROPOSITION_GENERALE_SOUMISE
from admission.infrastructure.admission.domain.service.digit import TEMPORARY_ACCOUNT_GLOBAL_ID_PREFIX
from backoffice.celery import app
from base.models.enums.person_address_type import PersonAddressType
from base.models.person import Person
from base.models.person_creation_ticket import PersonTicketCreation, PersonTicketCreationStatus
from base.models.person_merge_proposal import PersonMergeProposal, PersonMergeStatus
from base.tasks import send_pictures_to_card_app
from osis_profile.models import ProfessionalExperience, EducationalExperience, BelgianHighSchoolDiploma, \
    ForeignHighSchoolDiploma, HighSchoolDiplomaAlternative
from osis_profile.services.injection_epc import InjectionEPCCurriculum

logger = logging.getLogger(settings.CELERY_EXCEPTION_LOGGER)

PREFIX_TASK = "[Retrieve DigIT ticket status] :"


@app.task
@transaction.non_atomic_requests
def run(request=None):
    if not waffle.switch_is_active('fusion-digit'):
        logger.info(f"{PREFIX_TASK} fusion-digit switch not active")
        return

    from infrastructure.messages_bus import message_bus_instance
    logger.info(f"{PREFIX_TASK} starting task...")

    # Retrieve list of tickets
    logger.info(f"{PREFIX_TASK} fetch pending DigIT tickets...")
    tickets_pending = message_bus_instance.invoke(RetrieveListeTicketsEnAttenteQuery())  # type: List[StatutTicketPersonneDTO]
    logger.info(f"{PREFIX_TASK} pending DigIT tickets..." + str(tickets_pending))

    for ticket in tickets_pending:
        try:
            with transaction.atomic():
                status = message_bus_instance.invoke(
                    RetrieveAndStoreStatutTicketPersonneFromDigitCommand(ticket_uuid=ticket.uuid)
                )
                logger.info(f"{PREFIX_TASK} process DigIT ticket ({str(ticket)}")
                if status in ["DONE", "DONE_WITH_WARNINGS"]:
                    _process_successful_response_ticket(message_bus_instance, ticket)
                else:
                    logger.info(f"{PREFIX_TASK} ticket in status {status}. No processing ticket response.")
        except Exception as e:
            logger.info(f"{PREFIX_TASK} An error occured during processing ticket ({repr(e)})")
            PersonTicketCreation.objects.filter(uuid=ticket.uuid).update(
                status=PersonTicketCreationStatus.ERROR.name,
                errors=[{"errorCode": {"errorCode": "ERROR_DURING_RETRIEVE_DIGIT_TICKET"}, 'msg': repr(e)}]
            )

    # Handle response when task is ran as a cmd from admin panel
    if request:
        return redirect(request.META.get('HTTP_REFERER'))


def _process_successful_response_ticket(message_bus_instance, ticket):
    logger.info(f"{PREFIX_TASK} ####### START PROCESS SUCCESSFUL DIGIT RESPONSE #######")
    ticket_rowdb = PersonTicketCreation.objects.get(uuid=ticket.uuid)
    logger.info(f"{PREFIX_TASK} check if pending/errored tickets")
    qs_pending_errored_tickets = PersonTicketCreation.objects.filter(
        person=ticket_rowdb.person,
        created_at__lt=ticket_rowdb.created_at,
    ).exclude(
        Q(uuid=ticket.uuid) |
        Q(
            status__in=[
                PersonTicketCreationStatus.DONE.name,
                PersonTicketCreationStatus.DONE_WITH_WARNINGS.name
            ]
        )
    )
    if qs_pending_errored_tickets.exists():
        raise Exception(
            f"There exists some digit tickets to treat before (Count: {qs_pending_errored_tickets.count()})"
        )

    from admission.infrastructure.admission.repository.digit import DigitRepository
    noma = DigitRepository.get_registration_id_sent_to_digit(global_id=ticket.matricule)

    logger.info(f"{PREFIX_TASK} fetch matricule DigIT from noma (NOMA: {noma})")
    digit_matricule = message_bus_instance.invoke(RecupererMatriculeDigitQuery(noma=noma))
    logger.info(f"{PREFIX_TASK} matricule DigIT found ({digit_matricule}) for noma ({noma})")
    candidat = ticket_rowdb.person
    if candidat.global_id[0] in TEMPORARY_ACCOUNT_GLOBAL_ID_PREFIX and candidat.global_id != digit_matricule:
        # personne pas encore connue de osis - on remplace le global_id et external_id
        if not Person.objects.filter(global_id=digit_matricule).exists():
            logger.info(
                f"{PREFIX_TASK} "
                f"edit candidate global_id ({candidat.global_id}) to set DigIT matricule ({digit_matricule})"
            )
            candidat.global_id = digit_matricule
            candidat.external_id = f"osis.person_{digit_matricule}"
            for address in candidat.personaddress_set.all():
                address.external_id = f"osis.student_address_STUDENT_{digit_matricule}_{address.label}"
                address.save()
        if candidat.user:
            candidat.user.usergroup_set.all().delete()
            candidat.user.delete()
        candidat.user = None
        candidat.save()
    elif candidat.global_id == digit_matricule:
        logger.info(
            f"{PREFIX_TASK} "
            f"candidate global_id ({candidat.global_id}) is already the same as DigIT response ({digit_matricule})"
        )
    else:
        msg = f"candidate global_id ({candidat.global_id}) is not the same as DigIT response ({digit_matricule}) " \
              f"for noma {noma}. Please verify data integrity !"
        logger.info(f"{PREFIX_TASK} {msg}")
        PersonTicketCreation.objects.filter(uuid=ticket.uuid).update(
            status=PersonTicketCreationStatus.ERROR.name,
            errors=[{"errorCode": {"errorCode": "ERROR_DURING_RETRIEVE_DIGIT_TICKET"}, 'msg': msg}]
        )
        return

    try:
        proposition_fusion = PersonMergeProposal.objects.select_related(
            'proposal_merge_person'
        ).filter(
            original_person_id=candidat.pk,
            status=PersonMergeStatus.IN_PROGRESS.name,
            proposal_merge_person__isnull=False,
        ).exclude(selected_global_id='').get()
        logger.info(
            f"{PREFIX_TASK} Person merge proposal found in valid state for candidate "
            f"(PK: {candidat.pk} - UUID: {candidat.uuid})"
        )

        # OSIS only contains data >= 2015. Manager can select a matricule which are not present in OSIS
        # (result coming from search_potential_duplicate from DigIT)
        try:
            personne_connue = Person.objects.get(global_id=proposition_fusion.selected_global_id)
            logger.info(f"{PREFIX_TASK} Person with global_id ({personne_connue.global_id}) found")
        except Person.DoesNotExist:
            personne_connue = Person(
                external_id=f"osis.person_{proposition_fusion.selected_global_id}",
                global_id=proposition_fusion.selected_global_id,
            )
            logger.info(
                f"{PREFIX_TASK} Person with global_id ({personne_connue.global_id}) not found. (Maybe data < 2015 ?)"
            )

        # ne doit pas faire les modifications si le candidat est devenu la personne connue
        if candidat.global_id != personne_connue.global_id:

            _update_non_empty_fields(source_obj=candidat, target_obj=personne_connue)
            _update_non_empty_fields(source_obj=proposition_fusion.proposal_merge_person, target_obj=personne_connue)

            # remove address from personne_connue (will be replaced by candidate addresses)
            known_person_addresses = personne_connue.personaddress_set.filter(
                label__in=[PersonAddressType.RESIDENTIAL.name, PersonAddressType.CONTACT.name]
            )
            for address in known_person_addresses:
                logger.info(f"{PREFIX_TASK} remove address from known person: {address.location}")
                address.delete()
            for address in candidat.personaddress_set.all():
                logger.info(f"{PREFIX_TASK} add external id to candidate addresses: {address}")
                address.external_id = f"osis.student_address_STUDENT_{personne_connue.global_id}_{address.label}"
                address.save()

            personne_connue.save()

            models = _find_models_with_fk_to_person()
            for model, field_name in models:
                if model == Candidate:
                    if not model.objects.filter(person=proposition_fusion.original_person).exists():
                        updated_count = model.objects.filter(person=proposition_fusion.original_person).update(
                            person=personne_connue
                        )
                        logger.info(
                            f"{PREFIX_TASK} Link {updated_count} instances of {model.__name__}"
                            f" from candidate to known person"
                        )
                    else:
                        # delete deprecated role candidate to avoid duplicates
                        if model.objects.filter(person=personne_connue).exists():
                            model.objects.get(person=proposition_fusion.original_person).delete()

                if model == BaseAdmission:
                    admissions = model.objects.filter(
                        **{field_name: proposition_fusion.original_person}
                    )
                    for admission in admissions:
                        admission.candidate_id = personne_connue.pk
                        if admission.valuated_secondary_studies_person_id:
                            admission.valuated_secondary_studies_person_id = personne_connue.pk
                        admission.save()
                    logger.info(
                        f"{PREFIX_TASK} Link {len(admissions)} instances of {model.__name__}"
                        f" from candidate to known person"
                    )
                elif model in [BelgianHighSchoolDiploma, ForeignHighSchoolDiploma, HighSchoolDiplomaAlternative]:
                    candidate_high_school_diplomas = model.objects.filter(
                        **{field_name: proposition_fusion.original_person}
                    )
                    known_person_high_school_diplomas = model.objects.filter(
                        **{field_name: personne_connue}
                    )
                    if candidate_high_school_diplomas.exists() and known_person_high_school_diplomas.exists():
                        alternative_suppr = model == HighSchoolDiplomaAlternative
                        a_supprimer = list(known_person_high_school_diplomas.values_list('uuid', flat=True))
                        known_person_high_school_diplomas.delete()
                        _trigger_epc_diplomas_deletion(a_supprimer, noma, personne_connue, alternative_suppr)  # noqa
                    for diploma in candidate_high_school_diplomas:
                        diploma.person_id = personne_connue.pk
                        diploma.save()
                elif model in [ProfessionalExperience, EducationalExperience]:
                    candidate_experiences = model.objects.filter(**{field_name: proposition_fusion.original_person})
                    known_person_experiences = model.objects.filter(**{field_name: personne_connue})
                    logger.info(
                        f"{PREFIX_TASK} {len(candidate_experiences)} instances of {model.__name__} of candidate"
                    )
                    logger.info(
                        f"{PREFIX_TASK} {len(known_person_experiences)} instances of {model.__name__} of known person"
                    )
                    curex_to_merge = [
                        UUID(experience_uuid) for experience_uuid in
                        (proposition_fusion.professional_curex_to_merge + proposition_fusion.educational_curex_to_merge)
                    ]

                    # always keep curex from candidate and delete known_person curex that has not been selected
                    for experience in known_person_experiences:
                        if experience.uuid not in curex_to_merge:
                            logger.info(f"{PREFIX_TASK} Removing instance of {model.__name__} ({experience.uuid})")
                            experience_uuid = experience.uuid
                            if model == EducationalExperience:
                                a_supprimer = list(
                                    experience.educationalexperienceyear_set.values_list('uuid', flat=True)
                                )
                                experience.educationalexperienceyear_set.all().delete()
                                experience.delete()
                                _trigger_epc_academic_curriculum_deletion(
                                    experience_uuid, noma, personne_connue, a_supprimer
                                )
                            if model == ProfessionalExperience:
                                _trigger_epc_non_academic_curriculum_deletion(experience_uuid, noma, personne_connue)
                                experience.delete()
                        else:
                            admissions = BaseAdmission.objects.filter(candidate=candidat)
                            for admission in admissions:
                                if model == EducationalExperience:
                                    AdmissionEducationalValuatedExperiences.objects.create(
                                        baseadmission=admission, educationalexperience=experience
                                    )
                                elif model == ProfessionalExperience:
                                    AdmissionProfessionalValuatedExperiences.objects.create(
                                        baseadmission=admission, professionalexperience=experience
                                    )

                    for experience in candidate_experiences:
                        logger.info(
                            f"{PREFIX_TASK} Move instance of {model.__name__} ({experience.uuid}) "
                            f"from candidate to known person "
                        )
                        experience.person_id = personne_connue.pk
                        experience.save()

                else:
                    updated_count = model.objects.filter(
                        **{field_name: proposition_fusion.original_person}
                    ).update(**{field_name: personne_connue})
                    logger.info(
                        f"{PREFIX_TASK} Link {updated_count} instances of {model.__name__}"
                        f" from candidate to known person"
                    )
        else:
            _update_non_empty_fields(source_obj=proposition_fusion.proposal_merge_person, target_obj=candidat)
            candidat.save()

        proposition_fusion.proposal_merge_person.delete()
        proposition_fusion.proposal_merge_person = None
        proposition_fusion.status = PersonMergeStatus.MERGED.name
        proposition_fusion.selected_global_id = ''
        if personne_connue and personne_connue.global_id != candidat.global_id:
            proposition_fusion.original_person = personne_connue
        proposition_fusion.save()

    except PersonMergeProposal.DoesNotExist:
        logger.info(
            f"{PREFIX_TASK} No person merge proposal found in valid state for candidate (PK: {candidat.pk})"
            f"(Status: IN_PROGRESS / selected_global_id not empty / proposal_merge_person exist)"
        )

    logger.info(f"{PREFIX_TASK} send signaletique into EPC")
    _injecter_signaletique_a_epc(digit_matricule)
    if settings.USE_CELERY:
        # TODO refactor to create a model which monitor sending picture to card
        send_pictures_to_card_app.run.delay(global_id=digit_matricule)
    logger.info(f"{PREFIX_TASK} send picture to card")
    logger.info(f"{PREFIX_TASK} ####### END PROCESS SUCCESSFUL DIGIT RESPONSE #######")


def _trigger_epc_diplomas_deletion(a_supprimer, noma, personne_connue, alternative_suppr):
    InjectionEPCCurriculum().injecter_etudes_secondaires(
        fgs=personne_connue.global_id,
        noma=noma,
        user='fusion',
        alternative_supprimee=alternative_suppr,
        experiences_supprimees=a_supprimer,
    )


def _trigger_epc_academic_curriculum_deletion(experience_uuid, noma, personne_connue, a_supprimer):
    InjectionEPCCurriculum().injecter_experience_academique(
        fgs=personne_connue.global_id,
        noma=noma,
        user='fusion',
        experience_uuid=experience_uuid,
        experiences_supprimees=a_supprimer,
    )


def _trigger_epc_non_academic_curriculum_deletion(experience_uuid, noma, personne_connue):
    InjectionEPCCurriculum().injecter_experience_non_academique(
        fgs=personne_connue.global_id,
        noma=noma,
        user='fusion',
        experience_uuid=experience_uuid,
        experiences_supprimees=[experience_uuid],
    )


def _injecter_signaletique_a_epc(matricule: str):
    from admission.services.injection_epc.injection_signaletique import InjectionEPCSignaletique

    demande = GeneralEducationAdmission.objects.filter(
        candidate__global_id=matricule,
    ).filter(
        status__in=STATUTS_PROPOSITION_GENERALE_SOUMISE
    ).order_by('created_at').first()
    InjectionEPCSignaletique().injecter(admission=demande)


def _update_non_empty_fields(source_obj: Model, target_obj: Model):
    """
    Update non-empty fields from source_obj to target_obj.
    """
    for field in source_obj._meta.fields:
        field_name = field.name
        source_value = getattr(source_obj, field_name)
        # Skip fields that should not be updated
        if field.primary_key or field.name in [
            'uuid',
            'user',
            'external_id',
            'global_id',
            'email',
        ] or not source_value:
            continue
        setattr(target_obj, field_name, source_value)


def _find_models_with_fk_to_person():
    models_with_fk = []
    for model in [model for model in apps.get_models() if model != PersonMergeProposal]:
        for field in model._meta.get_fields():
            if isinstance(field, ForeignKey) and field.related_model == Person:
                models_with_fk.append((model, field.name))
    return models_with_fk


@override_switch('fusion-digit', active=True)
@transaction.non_atomic_requests
def force_run(request=None):
    return run(request=request)

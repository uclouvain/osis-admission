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

from admission.contrib.models import GeneralEducationAdmission
from admission.contrib.models.base import BaseAdmission
from admission.ddd.admission.commands import (
    RetrieveListeTicketsEnAttenteQuery,
    RetrieveAndStoreStatutTicketPersonneFromDigitCommand, RecupererMatriculeDigitQuery,
)
from admission.ddd.admission.dtos.statut_ticket_personne import StatutTicketPersonneDTO
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.infrastructure.admission.domain.service.digit import TEMPORARY_ACCOUNT_GLOBAL_ID_PREFIX
from backoffice.celery import app
from base.models.enums.person_address_type import PersonAddressType
from base.models.person import Person
from base.models.person_creation_ticket import PersonTicketCreation, PersonTicketCreationStatus
from base.models.person_merge_proposal import PersonMergeProposal, PersonMergeStatus
from base.tasks import send_pictures_to_card_app
from osis_profile.models import ProfessionalExperience, EducationalExperience, BelgianHighSchoolDiploma, \
    ForeignHighSchoolDiploma, HighSchoolDiplomaAlternative

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
        _update_non_empty_fields(source_obj=candidat, target_obj=personne_connue)
        _update_non_empty_fields(source_obj=proposition_fusion.proposal_merge_person, target_obj=personne_connue)

        # remove address from personne_connue (will be replaced by candidate addresses)
        personne_connue.personaddress_set.all().filter(
            label__in=[PersonAddressType.RESIDENTIAL.name, PersonAddressType.CONTACT.name]
        ).delete()

        personne_connue.save()
        proposition_fusion.proposal_merge_person.delete()
        proposition_fusion.proposal_merge_person = None

        models = _find_models_with_fk_to_person()
        for model, field_name in models:
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
                    f"{PREFIX_TASK} Link {len(admissions)} instances of {model.__name__} from candidate to known person"
                )
            elif model in [BelgianHighSchoolDiploma, ForeignHighSchoolDiploma, HighSchoolDiplomaAlternative]:
                candidate_high_school_diplomas = model.objects.filter(
                    **{field_name: proposition_fusion.original_person}
                )
                known_person_high_school_diplomas = model.objects.filter(
                    **{field_name: personne_connue}
                )
                if candidate_high_school_diplomas:
                    known_person_high_school_diplomas.delete()
                for diploma in candidate_high_school_diplomas:
                    diploma.person_id = personne_connue.pk
                    diploma.save()
            elif model in [ProfessionalExperience, EducationalExperience]:
                experiences = model.objects.filter(**{field_name: proposition_fusion.original_person})
                logger.info(f"{PREFIX_TASK} {len(experiences)} instances of {model.__name__} of candidate")
                curex_to_merge = [
                    UUID(experience_uuid) for experience_uuid in
                    (proposition_fusion.professional_curex_to_merge + proposition_fusion.educational_curex_to_merge)
                ]

                for experience in experiences:
                    if experience.uuid in curex_to_merge:
                        logger.info(
                            f"{PREFIX_TASK} Link instance of {model.__name__} ({experience.uuid}) from candidate "
                            f"to known person"
                        )
                        experience.person_id = personne_connue.pk
                        experience.save()
                    else:
                        logger.info(f"{PREFIX_TASK} Removing instance of {model.__name__} ({experience.uuid})")
                        experience.delete()

            else:
                updated_count = model.objects.filter(
                    **{field_name: proposition_fusion.original_person}
                ).update(**{field_name: personne_connue})
                logger.info(
                    f"{PREFIX_TASK} Link {updated_count} instances of {model.__name__} from candidate to known person"
                )

        for address in candidat.personaddress_set.all():
            address.external_id = f"osis.student_address_STUDENT_{personne_connue.global_id}_{address.label}"

        proposition_fusion.status = PersonMergeStatus.MERGED.name
        proposition_fusion.selected_global_id = ''
        if personne_connue:
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


def _injecter_signaletique_a_epc(matricule: str):
    from admission.services.injection_epc.injection_signaletique import InjectionEPCSignaletique

    # TODO: Inject also for other admisison type
    demande = GeneralEducationAdmission.objects.filter(
        candidate__global_id=matricule,
    ).filter(
        Q(
            type_demande=TypeDemande.ADMISSION.name,
            status=ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name
        )
        | Q(type_demande=TypeDemande.INSCRIPTION.name)
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

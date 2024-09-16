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

from django.conf import settings
from django.db.models import Q

from admission.calendar.admission_digit_ticket_submission import AdmissionDigitTicketSubmissionCalendar
from admission.contrib.models.base import BaseAdmission
from admission.contrib.models.epc_injection import EPCInjectionType, EPCInjectionStatus
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from backoffice.celery import app as celery_app
from base.models.person_merge_proposal import PersonMergeStatus
from ddd.logic.financabilite.domain.model.enums.etat import EtatFinancabilite

logger = logging.getLogger(settings.CELERY_EXCEPTION_LOGGER)


@celery_app.task
def run():  # pragma: no cover
    logger.info(f"[TASK - INJECTION EPC] Lancement de la tache")
    annee_ouverte = AdmissionDigitTicketSubmissionCalendar().get_target_years_opened()[0]
    # TODO: compatibilite avec doctorat et iufc
    admissions = BaseAdmission.objects.select_related(
        'generaleducationadmission',
        'epc_injection',
        'candidate__personmergeproposal',
    ).filter(
        # Dossier doit etre sur la bonne annee
        determined_academic_year__year=annee_ouverte,
        # Dossier doit être en INSCRIPTION AUTORISEE
        generaleducationadmission__status=ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name,
        # Doit avoir un matricule fgs interne
        candidate__global_id__startswith='00',
        # Doit avoir un email uclouvain
        candidate__email__endswith='uclouvain.be',
        # Aucune erreur syntaxique de signalétique
        candidate__personmergeproposal__validation__valid=True,
        # Doit être financable ou non concerné
        checklist__current__financabilite__statut__in=[
            EtatFinancabilite.FINANCABLE.name,
            EtatFinancabilite.NON_CONCERNE.name
        ],
    ).exclude(
        # Doit avoir une situation de financabilité + une date + un auteur
        Q(generaleducationadmission__financability_rule='')
        | Q(generaleducationadmission__financability_rule_established_on__isnull=True)
        | Q(generaleducationadmission__financability_rule_established_by_id__isnull=True)
        # Le dossier ne doit pas avoir ete injecté
        | Q(
            epc_injection__type=EPCInjectionType.DEMANDE.name,
            epc_injection__status__in=[EPCInjectionStatus.OK.name, EPCInjectionStatus.PENDING.name],
        )
        # Un noma doit exister
        | Q(candidate__personmergeproposal__registration_id_sent_to_digit='')
        # Aucune erreur avec Digit
        | Q(candidate__personmergeproposal__status__in=PersonMergeStatus.quarantine_statuses()),
    )
    logger.info(f"[TASK - INJECTION EPC] {admissions.count()} dossiers a traiter")
    from admission.services.injection_epc.injection_dossier import InjectionEPCAdmission
    for admission in admissions:
        InjectionEPCAdmission().injecter(admission)

    logger.info(f"[TASK - INJECTION EPC] Traitement termine")

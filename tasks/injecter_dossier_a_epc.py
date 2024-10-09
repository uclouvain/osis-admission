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
from django.db.models import Q, Exists, OuterRef

from admission.calendar.admission_digit_ticket_submission import AdmissionDigitTicketSubmissionCalendar
from admission.contrib.models.base import BaseAdmission
from admission.contrib.models.epc_injection import EPCInjectionType, EPCInjectionStatus, EPCInjection
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from backoffice.celery import app as celery_app
from base.models.person_merge_proposal import PersonMergeStatus

logger = logging.getLogger(settings.CELERY_EXCEPTION_LOGGER)


@celery_app.task
def run():  # pragma: no cover
    logger.info(f"[TASK - INJECTION EPC] Lancement de la tache")
    annee_ouverte = AdmissionDigitTicketSubmissionCalendar().get_target_years_opened()[0]
    # TODO: compatibilite avec doctorat et iufc
    admissions = BaseAdmission.objects.select_related(
        'generaleducationadmission',
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
        checklist__current__financabilite__statut__in=['INITIAL_NON_CONCERNE', 'GEST_REUSSITE'],
    ).exclude(
        # Doit avoir une situation de financabilité (si financable) + une date + un auteur (si concerné)
        Q(
            checklist__current__financabilite__status='GEST_REUSSITE',
            checklist__current__financanbilite__extra__reussite='financable',
            generaleducationadmission__financability_rule=''
        )
        | Q(
            checklist__current__financabilite__status='GEST_REUSSITE',
            generaleducationadmission__financability_rule_established_on__isnull=True
        )
        | Q(
            checklist__current__financabilite__status='GEST_REUSSITE',
            generaleducationadmission__financability_rule_established_by_id__isnull=True
        )
        # Un noma doit exister
        | Q(candidate__personmergeproposal__registration_id_sent_to_digit='')
        # Aucune erreur avec Digit
        | Q(candidate__personmergeproposal__status__in=PersonMergeStatus.quarantine_statuses()),
    ).annotate(
        a_ete_injecte=Exists(
            EPCInjection.objects.filter(
                admission_id=OuterRef('pk'),
                type=EPCInjectionType.DEMANDE.name,
                status__in=[EPCInjectionStatus.OK.name, EPCInjectionStatus.PENDING.name]
            )
        )
    ).exclude(
        a_ete_injecte=True
    )
    logger.info(f"[TASK - INJECTION EPC] {admissions.count()} dossiers a traiter")
    from admission.services.injection_epc.injection_dossier import InjectionEPCAdmission
    for admission in admissions:
        InjectionEPCAdmission().injecter(admission)

    logger.info(f"[TASK - INJECTION EPC] Traitement termine")

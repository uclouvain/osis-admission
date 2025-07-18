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
import logging
from typing import List

from django.conf import settings
from django.db.models import Q, Exists, OuterRef, When, Case, Value

from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.models.base import BaseAdmission
from admission.models.epc_injection import EPCInjectionType, EPCInjectionStatus, EPCInjection
from backoffice.celery import app as celery_app
from base.models.person_merge_proposal import PersonMergeStatus
from ddd.logic.gestion_des_comptes.dto.periode_soumission_ticket import PeriodeSoumissionTicketDigitDTO
from ddd.logic.gestion_des_comptes.queries import GetPeriodeActiveSoumissionTicketQuery

logger = logging.getLogger(settings.CELERY_EXCEPTION_LOGGER)


@celery_app.task
def run():  # pragma: no cover
    logger.info(f"[TASK - INJECTION EPC] Lancement de la tache")
    from infrastructure.messages_bus import message_bus_instance
    periodes_actives = message_bus_instance.invoke(
        GetPeriodeActiveSoumissionTicketQuery()
    )  # type: List[PeriodeSoumissionTicketDigitDTO]
    annee_ouverte = periodes_actives[0].annee

    # TODO: compatibilite avec doctorat et iufc
    admissions = BaseAdmission.objects.select_related(
        'generaleducationadmission',
        'candidate__personmergeproposal',
    ).filter(
        # Dossier doit être en INSCRIPTION AUTORISEE
        Q(generaleducationadmission__status=ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name)
        | Q(continuingeducationadmission__status=ChoixStatutPropositionContinue.INSCRIPTION_AUTORISEE.name),
        # Dossier doit etre sur la bonne annee
        determined_academic_year__year=annee_ouverte,
        # Doit avoir un matricule fgs interne
        candidate__global_id__startswith='00',
        # Doit avoir un email uclouvain
        candidate__email__endswith='uclouvain.be',
        # Aucune erreur syntaxique de signalétique
        candidate__personmergeproposal__validation__valid=True,
    ).exclude(
        # Un noma doit exister
        Q(candidate__personmergeproposal__registration_id_sent_to_digit='')
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
    ).annotate(
        financabilite_completee=Case(
            When(
                ~Q(checklist__current__financabilite__status__in=['INITIAL_NON_CONCERNE', 'GEST_REUSSITE'])
                | Q(
                    checklist__current__financabilite__status='GEST_REUSSITE',
                    checklist__current__financanbilite__extra__reussite='financable',
                    generaleducationadmission__financability_rule=''
                )
                | Q(
                    checklist__current__financabilite__status='GEST_REUSSITE',
                    generaleducationadmission__financability_established_on__isnull=True
                )
                | Q(
                    checklist__current__financabilite__status='GEST_REUSSITE',
                    generaleducationadmission__financability_established_by_id__isnull=True
                ),
                generaleducationadmission__isnull=False,
                then=Value(False),
            ),
            default=Value(True),
        ),
    ).exclude(
        financabilite_completee=False
    ).annotate(
        inscription_au_role_requise=Case(
            When(
                Q(continuingeducationadmission__isnull=False,
                  training__specificiufcinformations__registration_required=True)
                | Q(continuingeducationadmission__isnull=True),
                then=Value(True)
            ),
            default=Value(False),
        )
    ).exclude(
        inscription_au_role_requise=False
    ).annotate(
        ordre_priorite=Case(
            When(continuingeducationadmission__isnull=False, then=1),
            When(generaleducationadmission__isnull=False, then=2)
        )
    ).order_by('ordre_priorite')
    logger.info(f"[TASK - INJECTION EPC] {admissions.count()} dossiers a traiter")
    from admission.services.injection_epc.injection_dossier import InjectionEPCAdmission

    for admission in admissions:
        InjectionEPCAdmission().injecter(admission)

    logger.info(f"[TASK - INJECTION EPC] Traitement termine")

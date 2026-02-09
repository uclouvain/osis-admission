##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################
import datetime
from typing import List, Tuple

from django.conf import settings
from django.db import connection
from django.db.models import Q
from django.utils import timezone, translation
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from osis_document_components.services import get_remote_token
from osis_document_components.utils import get_file_url
from osis_mail_template.exceptions import EmptyMailTemplateContent
from osis_mail_template.models import MailTemplate

from admission.calendar.admission_calendar import SIGLES_WITH_QUOTA
from admission.ddd.admission.formation_generale.domain.model.contingente import (
    PropositionContingenteResume,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    STATUTS_PROPOSITION_GENERALE_SOUMISE,
    ChoixStatutChecklist,
    ChoixStatutPropositionGenerale,
    OngletsChecklist,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    Proposition,
    PropositionIdentity,
)
from admission.ddd.admission.formation_generale.domain.service.i_contingente import (
    IContingente,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    UneSeuleFormationContingentePossible,
)
from admission.ddd.admission.formation_generale.dtos.contingente import (
    AdmissionContingenteNonResidenteNotificationDTO,
)
from admission.ddd.admission.formation_generale.repository.i_proposition import (
    IPropositionRepository,
)
from admission.ddd.admission.shared_kernel.domain.model.formation import Formation
from admission.ddd.admission.shared_kernel.enums.emplacement_document import (
    ALL_DOCUMENTS_LABEL,
    StatutEmplacementDocument,
    StatutReclamationEmplacementDocument,
    TypeEmplacementDocument,
)
from admission.infrastructure.admission.formation_generale.domain.service.notification import (
    ONE_YEAR_SECONDS,
)
from admission.mail_templates.contingente import ADMISSION_EMAIL_CONTINGENTE_ACCEPTATION
from admission.models import AdmissionFormItem, GeneralEducationAdmission
from admission.models.contingente import ContingenteTraining
from admission.utils import get_backoffice_admission_url, get_portal_admission_url
from base.models.academic_calendar import AcademicCalendar
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.person import Person
from base.utils.utils import format_academic_year

SEQUENCE_PATTERN = "admission_contingente_{year}_{acronym}_seq"


class Contingente(IContingente):
    @classmethod
    def generer_numero_de_dossier_ares_si_necessaire(cls, proposition: 'Proposition', annee: int) -> str:
        acronym = proposition.formation_id.sigle
        year = str(annee)

        if acronym not in SIGLES_WITH_QUOTA or not proposition.est_non_resident_au_sens_decret:
            return ""

        # Get next value from sequence
        sequence = SEQUENCE_PATTERN.format(
            year=year,
            acronym=acronym,
        )
        cursor = connection.cursor()
        cursor.execute("CREATE SEQUENCE IF NOT EXISTS %(sequence)s" % {'sequence': sequence})
        cursor.execute("SELECT NEXTVAL('%(sequence)s')" % {'sequence': sequence})
        index = cursor.fetchone()[0]

        return f"UCLouvain/{acronym[0]}-{year[-2:]}{index:04}"

    @classmethod
    def verifier_proposition_contingente_unique(cls, proposition: 'Proposition'):
        if proposition.formation_id.sigle not in SIGLES_WITH_QUOTA or not proposition.est_non_resident_au_sens_decret:
            return
        if GeneralEducationAdmission.objects.filter(
            candidate__global_id=proposition.matricule_candidat,
            status__in=STATUTS_PROPOSITION_GENERALE_SOUMISE,
            training__acronym__in=SIGLES_WITH_QUOTA,
            training__academic_year__year=proposition.formation_id.annee,
            is_non_resident=True,
        ).exists():
            raise UneSeuleFormationContingentePossible()

    @classmethod
    def _get_admission_a_notifier_queryset(cls, formation_id: 'FormationIdentity'):
        contingente_training = ContingenteTraining.objects.filter(
            training__academic_year__year=formation_id.annee,
            training__acronym=formation_id.sigle,
        ).first()
        if contingente_training is None:
            return GeneralEducationAdmission.objects.none()
        nombre_places = contingente_training.places_number
        return (
            GeneralEducationAdmission.objects.select_related('candidate', 'training')
            .filter(
                training__academic_year__year=formation_id.annee,
                training__acronym=formation_id.sigle,
                status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            )
            .filter(
                Q(checklist__current__decision_sic__statut=ChoixStatutChecklist.INITIAL_CANDIDAT.name)
                | Q(
                    checklist__current__decision_sic__statut=ChoixStatutChecklist.GEST_BLOCAGE.name,
                    checklist__current__decision_sic__extra__blocage='to_be_completed',
                )
                | Q(
                    checklist__current__decision_sic__statut=ChoixStatutChecklist.GEST_EN_COURS.name,
                    checklist__current__decision_sic__extra__en_cours='derogation',
                )
                | Q(
                    checklist__current__decision_sic__statut=ChoixStatutChecklist.GEST_EN_COURS.name,
                    checklist__current__decision_sic__extra__en_cours='approval',
                )
            )
            .order_by('draw_number')
        )[:nombre_places]

    @classmethod
    def _load_dto_from_admission(
        cls, admission: GeneralEducationAdmission
    ) -> AdmissionContingenteNonResidenteNotificationDTO:
        documents_demandes = []
        for document_id, document in admission.requested_documents.items():
            if document_id in ALL_DOCUMENTS_LABEL:
                libelle = ALL_DOCUMENTS_LABEL[document_id]
            else:
                uuid = document_id.split('.')[-1]
                try:
                    admission_form_item = AdmissionFormItem.objects.get(uuid=uuid)
                    libelle = admission_form_item.title.get(get_language(), _('Document'))
                except AdmissionFormItem.DoesNotExist:
                    libelle = _('Document')
            documents_demandes.append(libelle)

        return AdmissionContingenteNonResidenteNotificationDTO(
            uuid=str(admission.uuid),
            sigle_formation=admission.training.acronym,
            annee_formation=admission.training.academic_year.year,
            statut=admission.status,
            prenom_candidat=admission.candidate.first_name,
            nom_candidat=admission.candidate.last_name,
            matricule_candidat=admission.candidate.global_id,
            documents_reclames_libelles=documents_demandes,
            notification_acceptation=admission.non_resident_notified_at,
            numero_tirage=admission.draw_number,
        )

    @classmethod
    def recuperer_admissions_a_notifier(
        cls, formation_id: 'FormationIdentity'
    ) -> List['AdmissionContingenteNonResidenteNotificationDTO']:
        admissions = cls._get_admission_a_notifier_queryset(formation_id)
        return [cls._load_dto_from_admission(admission) for admission in admissions]

    @classmethod
    def _get_notification_email_strings(
        cls, admission: GeneralEducationAdmission, deadline_calendar: 'AcademicCalendar'
    ) -> Tuple[str, str]:
        acceptance_document_link = get_file_url(
            get_remote_token(
                admission.non_resident_limited_enrolment_acceptance_file[0],
                custom_ttl=ONE_YEAR_SECONDS,
            )
        )
        required_documents_paragraph = ''
        with translation.override(admission.candidate.language):
            if admission.requested_documents:
                required_documents_paragraph = _(
                    "<p>After verification, we have found that some documents are still missing from your application.</p>"
                )

        tokens = {
            'candidate_first_name': admission.candidate.first_name,
            'candidate_last_name': admission.candidate.last_name,
            'training_title': (
                admission.training.title
                if admission.candidate.language == settings.LANGUAGE_CODE_FR
                else admission.training.title_en
            ),
            'admission_link_front': get_portal_admission_url('general-education', admission.uuid),
            'admission_link_back': get_backoffice_admission_url('general-education', admission.uuid),
            'ares_application_number': admission.ares_application_number,
            'required_documents_paragraph': required_documents_paragraph,
            'acceptance_document_link': acceptance_document_link,
            'admission_link_front_requested_documents': get_portal_admission_url(
                'general-education',
                admission.uuid,
            )
            + 'update/documents',
            'academic_year': format_academic_year(admission.training.academic_year.year),
            'deadline_date': deadline_calendar.start_date.strftime("%d/%m/%y"),
        }

        try:
            mail_template: MailTemplate = MailTemplate.objects.get_mail_template(
                ADMISSION_EMAIL_CONTINGENTE_ACCEPTATION,
                admission.candidate.language,
            )

            subject = mail_template.render_subject(tokens=tokens)
            body = mail_template.body_as_html(tokens=tokens)
        except EmptyMailTemplateContent:
            subject = ''
            body = ''
        return subject, body

    @classmethod
    def _get_deadline_calendar(cls) -> AcademicCalendar:
        return (
            AcademicCalendar.objects.filter(
                start_date__gte=datetime.date.today(),
                reference=AcademicCalendarTypes.ADMISSION_NON_RESIDENT_QUOTA_ANSWER_DEADLINE.name,
            )
            .order_by('start_date')
            .first()
        )

    @classmethod
    def _notifier_admission(
        cls,
        admission: GeneralEducationAdmission,
        gestionnaire: Person,
        deadline_calendar: AcademicCalendar,
        proposition_repository: 'IPropositionRepository',
        profil_candidat_translator: 'IProfilCandidatTranslator',
        pdf_generation: 'IPDFGeneration',
        notification: 'INotification',
        historique: 'IHistorique',
    ):
        now = timezone.now()
        proposition = PropositionContingenteResume(
            entity_id=PropositionIdentity(uuid=str(admission.uuid)),
            matricule_candidat=admission.candidate.global_id,
            acceptation_contingente=admission.non_resident_limited_enrolment_acceptance_file,
        )

        pdf_generation.generer_acceptation_contingente(
            proposition_repository=proposition_repository,
            profil_candidat_translator=profil_candidat_translator,
            proposition=proposition,
        )

        admission.non_resident_limited_enrolment_acceptance_file = proposition.acceptation_contingente
        admission.non_resident_notified_at = now
        admission.non_resident_notified_by = gestionnaire
        admission.requested_documents['ACCEPTATION_FORMATION_CONTINGENTE'] = {
            'last_actor': gestionnaire.global_id,
            'reason': '',
            'type': TypeEmplacementDocument.NON_LIBRE.name,
            'last_action_at': now,
            'status': StatutEmplacementDocument.RECLAME.name,
            'requested_at': now,
            'automatically_required': True,
            'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
            'related_checklist_tab': OngletsChecklist.specificites_formation.name,
        }
        admission.status = ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name
        admission.save(
            update_fields=[
                'status',
                'non_resident_notified_at',
                'non_resident_notified_by',
                'non_resident_limited_enrolment_acceptance_file',
                'requested_documents',
            ]
        )

        objet_message, corps_message = cls._get_notification_email_strings(admission, deadline_calendar)
        email_message = notification.notifier_candidat_contingente_acceptation(
            proposition=proposition,
            corps_message=corps_message,
            objet_message=objet_message,
        )
        historique.historiser_notification_acceptance_contingente(proposition, gestionnaire.global_id, email_message)

    @classmethod
    def notifier_admissions_en_lot(
        cls,
        formation_id: 'FormationIdentity',
        gestionnaire: str,
        proposition_repository: 'IPropositionRepository',
        profil_candidat_translator: 'IProfilCandidatTranslator',
        pdf_generation: 'IPDFGeneration',
        notification: 'INotification',
        historique: 'IHistorique',
    ) -> None:
        admissions = cls._get_admission_a_notifier_queryset(formation_id)
        gestionnaire_person = Person.objects.filter(global_id=gestionnaire).first()

        ContingenteTraining.objects.filter(
            training__academic_year__year=formation_id.annee,
            training__acronym=formation_id.sigle,
        ).update(
            last_bulk_notification_at=timezone.now(),
            last_bulk_notification_by=gestionnaire_person,
        )

        deadline_calendar = cls._get_deadline_calendar()

        for admission in admissions:
            cls._notifier_admission(
                admission,
                gestionnaire_person,
                deadline_calendar,
                proposition_repository,
                profil_candidat_translator,
                pdf_generation,
                notification,
                historique,
            )

    @classmethod
    def notifier_admission(
        cls,
        proposition_id: 'PropositionIdentity',
        gestionnaire: str,
        proposition_repository: 'IPropositionRepository',
        profil_candidat_translator: 'IProfilCandidatTranslator',
        pdf_generation: 'IPDFGeneration',
        notification: 'INotification',
        historique: 'IHistorique',
    ) -> None:
        try:
            admission = GeneralEducationAdmission.objects.select_related('candidate', 'training').get(
                uuid=str(proposition_id.uuid)
            )
        except GeneralEducationAdmission.DoesNotExist:
            return
        gestionnaire_person = Person.objects.filter(global_id=gestionnaire).first()
        deadline_calendar = cls._get_deadline_calendar()

        cls._notifier_admission(
            admission,
            gestionnaire_person,
            deadline_calendar,
            proposition_repository,
            profil_candidat_translator,
            pdf_generation,
            notification,
            historique,
        )

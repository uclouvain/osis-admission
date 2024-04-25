# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from email.message import EmailMessage
from typing import Dict, List

from django.conf import settings
from django.shortcuts import resolve_url
from django.utils.translation import gettext as _
from osis_async.models import AsyncTask

from admission.ddd import MAIL_INSCRIPTION_DEFAUT
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums.emplacement_document import StatutEmplacementDocument
from admission.ddd.admission.formation_continue.dtos import PropositionDTO
from admission.infrastructure.utils import get_requested_documents_html_lists
from admission.mail_templates import (
    ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_AND_NOT_SUBMITTED_CONTINUING,
    ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_CONTINUING,
)
from base.utils.utils import format_academic_year
from osis_document.api.utils import get_remote_token
from osis_document.utils import get_file_url
from osis_mail_template import generate_email
from osis_mail_template.utils import transform_html_to_text
from osis_notification.contrib.handlers import EmailNotificationHandler
from osis_notification.contrib.notification import EmailNotification

from admission.auth.roles.program_manager import ProgramManager
from admission.contrib.models import AdmissionTask, ContinuingEducationAdmission
from admission.contrib.models.base import BaseAdmission
from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition
from admission.ddd.admission.formation_continue.domain.service.i_notification import INotification
from admission.mail_templates.submission import ADMISSION_EMAIL_CONFIRM_SUBMISSION_CONTINUING
from admission.utils import get_salutation_prefix, get_portal_admission_url, get_backoffice_admission_url

from base.models.person import Person


class Notification(INotification):
    @classmethod
    def _create_email_message_for_person(
        cls,
        person: Person,
        objet_message: str,
        corps_message: str,
    ):
        email_notification = EmailNotification(
            recipient=person.private_email,
            subject=objet_message,
            html_content=corps_message,
            plain_text_content=transform_html_to_text(corps_message),
        )

        email_message = EmailNotificationHandler.build(email_notification)
        EmailNotificationHandler.create(email_message, person=person)

        return email_message

    @classmethod
    def get_common_tokens(cls, admission: ContinuingEducationAdmission) -> Dict:
        """Return common tokens about a submission"""
        frontend_link = settings.ADMISSION_FRONTEND_LINK.format(
            context='continuing-education',
            uuid=admission.uuid,
        )
        backend_link = '{}{}'.format(
            settings.ADMISSION_BACKEND_LINK_PREFIX,
            resolve_url('admission:continuing-education', uuid=admission.uuid),
        )
        return {
            'candidate_first_name': admission.candidate.first_name,
            'candidate_last_name': admission.candidate.last_name,
            'training_title': {
                settings.LANGUAGE_CODE_FR: admission.training.title,
                settings.LANGUAGE_CODE_EN: admission.training.title_english,
            }[admission.candidate.language],
            'training_acronym': admission.training.acronym,
            'admission_link_front': frontend_link,
            'admission_link_back': backend_link,
            'salutation': get_salutation_prefix(admission.candidate),
            'admission_reference': admission.formatted_reference,
        }

    @classmethod
    def confirmer_soumission(cls, proposition: Proposition) -> None:
        from admission.exports.admission_recap.admission_recap import admission_pdf_recap

        admission = (
            BaseAdmission.objects.with_training_management_and_reference()
            .select_related('candidate', 'training')
            .get(uuid=proposition.entity_id.uuid)
        )

        # Generate the pdf recap
        token = admission_pdf_recap(admission, admission.candidate.language, ContinuingEducationAdmission)
        admission.pdf_recap = [token]
        admission.save(update_fields=['pdf_recap'])
        read_token = get_remote_token(
            uuid=admission.pdf_recap[0],
            custom_ttl=60 * 60 * 24 * cls.DUREE_EN_JOURS_TOKEN_LECTURE_RECAPITULATIF_ADMISSION,
        )

        # Create the async task to merge each document field of the proposition into one PDF
        task = AsyncTask.objects.create(
            name=_('Document merging of the proposition %(reference)s') % {'reference': proposition.reference},
            description=_('Merging of each document field of the proposition into one PDF'),
            person=admission.candidate,
        )
        AdmissionTask.objects.create(
            task=task,
            admission=admission,
            type=AdmissionTask.TaskType.CONTINUING_MERGE.name,
        )

        # Notify the candidate via email and the program managers in cc
        program_managers = ProgramManager.objects.filter(
            education_group=admission.training.education_group,
        ).select_related('person')

        common_tokens = cls.get_common_tokens(admission)
        common_tokens['recap_link'] = get_file_url(token=read_token)
        common_tokens['program_managers_emails'] = (' ' + _('or') + ' ').join(
            [
                f'<a href="mailto:{program_manager.person.email}">{program_manager.person.email}</a>'
                for program_manager in program_managers
            ]
        )
        common_tokens['program_managers_names'] = ', '.join(
            f'{manager.person.first_name} {manager.person.last_name}' for manager in program_managers
        )

        email_message = generate_email(
            ADMISSION_EMAIL_CONFIRM_SUBMISSION_CONTINUING,
            admission.candidate.language,
            common_tokens,
            recipients=[admission.candidate.private_email],
        )

        if program_managers:
            email_message['Cc'] = ','.join([program_manager.person.email for program_manager in program_managers])

        EmailNotificationHandler.create(email_message, person=admission.candidate)

    @classmethod
    def mettre_en_attente(
        cls,
        proposition: Proposition,
        objet_message: str,
        corps_message: str,
    ) -> EmailMessage:
        candidate = Person.objects.get(global_id=proposition.matricule_candidat)
        return cls._create_email_message_for_person(
            person=candidate,
            objet_message=objet_message,
            corps_message=corps_message,
        )

    @classmethod
    def approuver_par_fac(
        cls,
        proposition: Proposition,
        objet_message: str,
        corps_message: str,
    ) -> EmailMessage:
        candidate = Person.objects.get(global_id=proposition.matricule_candidat)
        return cls._create_email_message_for_person(
            person=candidate,
            objet_message=objet_message,
            corps_message=corps_message,
        )

    @classmethod
    def refuser_proposition(
        cls,
        proposition: Proposition,
        objet_message: str,
        corps_message: str,
    ) -> EmailMessage:
        candidate = Person.objects.get(global_id=proposition.matricule_candidat)
        return cls._create_email_message_for_person(
            person=candidate,
            objet_message=objet_message,
            corps_message=corps_message,
        )

    @classmethod
    def annuler_proposition(
        cls,
        proposition: Proposition,
        objet_message: str,
        corps_message: str,
    ) -> EmailMessage:
        candidate = Person.objects.get(global_id=proposition.matricule_candidat)
        return cls._create_email_message_for_person(
            person=candidate,
            objet_message=objet_message,
            corps_message=corps_message,
        )

    @classmethod
    def approuver_proposition(
        cls,
        proposition: Proposition,
        objet_message: str,
        corps_message: str,
    ) -> EmailMessage:
        candidate = Person.objects.get(global_id=proposition.matricule_candidat)
        return cls._create_email_message_for_person(
            person=candidate,
            objet_message=objet_message,
            corps_message=corps_message,
        )

    @classmethod
    def envoyer_message_libre_au_candidat(
        cls,
        proposition: Proposition,
        objet_message: str,
        corps_message: str,
    ) -> EmailMessage:
        candidate = Person.objects.get(global_id=proposition.matricule_candidat)
        return cls._create_email_message_for_person(
            person=candidate,
            objet_message=objet_message,
            corps_message=corps_message,
        )

    @classmethod
    def confirmer_reception_documents_envoyes_par_candidat(
        cls,
        proposition: PropositionDTO,
        liste_documents_reclames: List[EmplacementDocument],
        liste_documents_dto: List[EmplacementDocumentDTO],
    ):
        admission: BaseAdmission = BaseAdmission.objects.select_related(
            'candidate',
            'training__enrollment_campus',
        ).get(uuid=proposition.uuid)

        html_list_by_status = get_requested_documents_html_lists(liste_documents_reclames, liste_documents_dto)

        tokens = {
            'admission_reference': proposition.reference,
            'candidate_first_name': proposition.prenom_candidat,
            'candidate_last_name': proposition.nom_candidat,
            'salutation': get_salutation_prefix(person=admission.candidate),
            'training_title': admission.training.title
            if admission.candidate.language == settings.LANGUAGE_CODE_FR
            else admission.training.title_english,
            'training_acronym': proposition.formation.sigle,
            'training_campus': proposition.formation.campus,
            'requested_submitted_documents': html_list_by_status[StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION],
            'requested_not_submitted_documents': html_list_by_status[StatutEmplacementDocument.A_RECLAMER],
            'enrolment_service_email': admission.training.enrollment_campus.sic_enrollment_email
            or MAIL_INSCRIPTION_DEFAUT,
            'training_year': format_academic_year(proposition.annee_calculee),
            'admission_link_front': get_portal_admission_url('continuing-education', proposition.uuid),
            'admission_link_back': get_backoffice_admission_url('continuing-education', proposition.uuid),
        }

        email_message = generate_email(
            ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_AND_NOT_SUBMITTED_CONTINUING
            if html_list_by_status[StatutEmplacementDocument.A_RECLAMER]
            else ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_CONTINUING,
            admission.candidate.language,
            tokens,
            recipients=[admission.candidate.private_email],
        )
        EmailNotificationHandler.create(email_message, person=admission.candidate)

        # Create the async task to create the folder analysis containing the submitted documents
        task = AsyncTask.objects.create(
            name=_('Folder analysis of the proposition %(reference)s') % {'reference': admission.reference},
            description=_(
                'Create the folder analysis of the proposition containing the requested documents that the '
                'candidate submitted.',
            ),
            person=admission.candidate,
        )
        AdmissionTask.objects.create(
            task=task,
            admission=admission,
            type=AdmissionTask.TaskType.CONTINUING_FOLDER.name,
        )

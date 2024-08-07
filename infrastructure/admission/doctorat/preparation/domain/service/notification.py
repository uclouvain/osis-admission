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
from typing import List

from django.conf import settings
from django.db.models import OuterRef, Subquery
from django.shortcuts import resolve_url
from django.utils import translation
from django.utils.functional import lazy
from django.utils.translation import get_language, gettext_lazy as _
from osis_mail_template.utils import transform_html_to_text

from admission.contrib.models import AdmissionTask, SupervisionActor
from admission.contrib.models.base import BaseAdmission
from admission.contrib.models.doctorate import PropositionProxy
from admission.contrib.models.enums.actor_type import ActorType
from admission.ddd import MAIL_INSCRIPTION_DEFAUT
from admission.ddd.admission.doctorat.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixEtatSignature
from admission.ddd.admission.doctorat.preparation.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    SignataireIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition
from admission.ddd.admission.doctorat.preparation.domain.service.i_notification import INotification
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    SignataireNonTrouveException,
)
from admission.ddd.admission.doctorat.preparation.dtos import AvisDTO, PropositionDTO
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument
from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums.emplacement_document import StatutEmplacementDocument
from admission.infrastructure.admission.doctorat.preparation.domain.service.doctorat import DoctoratTranslator
from admission.infrastructure.utils import get_requested_documents_html_lists
from admission.mail_templates import (
    ADMISSION_EMAIL_CONFIRM_SUBMISSION_DOCTORATE,
    ADMISSION_EMAIL_MEMBER_REMOVED,
    ADMISSION_EMAIL_SIGNATURE_CANDIDATE,
    ADMISSION_EMAIL_SIGNATURE_REFUSAL,
    ADMISSION_EMAIL_SIGNATURE_REQUESTS_ACTOR,
    ADMISSION_EMAIL_SIGNATURE_REQUESTS_CANDIDATE,
    ADMISSION_EMAIL_SUBMISSION_CDD,
    ADMISSION_EMAIL_SUBMISSION_MEMBER,
)
from admission.mail_templates.document import (
    ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_AND_NOT_SUBMITTED_DOCTORATE,
    ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_DOCTORATE,
)
from admission.utils import (
    get_admission_cdd_managers,
    get_salutation_prefix,
    get_portal_admission_url,
    get_backoffice_admission_url,
)
from base.models.person import Person
from osis_async.models import AsyncTask
from osis_mail_template import generate_email
from osis_notification.contrib.handlers import EmailNotificationHandler, WebNotificationHandler
from osis_notification.contrib.notification import WebNotification, EmailNotification
from osis_signature.enums import SignatureState
from osis_signature.models import Actor
from osis_signature.utils import get_signing_token

from base.utils.utils import format_academic_year


class Notification(INotification):
    @classmethod
    def _get_doctorate_title_translation(cls, doctorat_id: 'FormationIdentity'):
        """Populate the translations of doctorate title and lazy return them"""
        # Create a dict to cache the translations of the doctorate title
        doctorate_title = {}
        for lang_code in dict(settings.LANGUAGES):
            with translation.override(lang_code):
                doctorate_title[lang_code] = DoctoratTranslator().get_dto(doctorat_id.sigle, doctorat_id.annee).intitule

        # Return a lazy proxy which, when evaluated to string, return the correct translation given the current language
        return lazy(lambda: doctorate_title[get_language()], str)()

    @classmethod
    def get_common_tokens(cls, proposition, candidat):
        """Return common tokens about a submission"""
        frontend_link = settings.ADMISSION_FRONTEND_LINK.format(context='doctorate', uuid=proposition.entity_id.uuid)
        return {
            "candidate_first_name": candidat.first_name,
            "candidate_last_name": candidat.last_name,
            "training_title": cls._get_doctorate_title_translation(proposition.formation_id),
            "admission_link_front": frontend_link,
            "admission_link_front_supervision": "{}supervision".format(frontend_link),
            "admission_link_back": "{}{}".format(
                settings.ADMISSION_BACKEND_LINK_PREFIX,
                resolve_url('admission:doctorate:project', uuid=proposition.entity_id.uuid),
            ),
            "reference": proposition.reference,
        }

    @classmethod
    def envoyer_signatures(cls, proposition: Proposition, groupe_de_supervision: GroupeDeSupervision) -> None:
        admission = PropositionProxy.objects.get(uuid=proposition.entity_id.uuid)

        # Création de la tâche de génération du document
        task = AsyncTask.objects.create(
            name=_("Exporting %(reference)s to PDF") % {'reference': admission.reference},
            description=_("Exporting the admission information to PDF"),
            person=admission.candidate,
            time_to_live=5,
        )
        AdmissionTask.objects.create(
            task=task,
            admission=admission,
            type=AdmissionTask.TaskType.ARCHIVE.name,
        )

        # Tokens communs
        candidat = Person.objects.get(global_id=proposition.matricule_candidat)
        common_tokens = cls.get_common_tokens(proposition, candidat)
        common_tokens["admission_link_back"] = "{}{}".format(
            settings.ADMISSION_BACKEND_LINK_PREFIX,
            resolve_url('admission:doctorate:supervision', uuid=proposition.entity_id.uuid),
        )
        common_tokens["admission_link_front"] = "{}{}".format(
            common_tokens["admission_link_front"],
            'supervision',
        )
        actor_list = SupervisionActor.objects.filter(process=admission.supervision_group).select_related('person')

        # Envoyer aux gestionnaires CDD
        for manager in get_admission_cdd_managers(admission.training.education_group_id):
            with translation.override(manager.language):
                content = (
                    _(
                        '<a href="%(admission_link_back)s">%(reference)s</a> - '
                        '%(candidate_first_name)s %(candidate_last_name)s requested '
                        'signatures for %(training_title)s'
                    )
                    % common_tokens
                )
                web_notification = WebNotification(recipient=manager, content=str(content))
            WebNotificationHandler.create(web_notification)

        # Envoyer au doctorant
        with translation.override(candidat.language):
            actor_list_str = [
                f"{actor.first_name} {actor.last_name} ({actor.get_type_display()})" for actor in actor_list
            ]
        email_message = generate_email(
            ADMISSION_EMAIL_SIGNATURE_REQUESTS_CANDIDATE,
            candidat.language,
            {
                **common_tokens,
                "actors_as_list_items": '<li></li>'.join(actor_list_str),
                "actors_comma_separated": ', '.join(actor_list_str),
            },
            recipients=[candidat.email],
        )
        EmailNotificationHandler.create(email_message, person=candidat)

        # Envoyer aux acteurs n'ayant pas répondu
        actors_invited = [actor for actor in actor_list if actor.last_state == SignatureState.INVITED.name]
        for actor in actors_invited:
            tokens = {
                **common_tokens,
                "signataire_first_name": actor.first_name,
                "signataire_last_name": actor.last_name,
                "signataire_role": actor.get_type_display(),
            }
            if actor.is_external:
                tokens["admission_link_front"] = cls._lien_invitation_externe(proposition, actor)
            email_message = generate_email(
                ADMISSION_EMAIL_SIGNATURE_REQUESTS_ACTOR,
                actor.language,
                tokens,
                recipients=[actor.email],
            )
            EmailNotificationHandler.create(email_message, person=actor.person_id and actor.person)

    @classmethod
    def notifier_avis(cls, proposition: Proposition, signataire_id: 'SignataireIdentity', avis: AvisDTO) -> None:
        admission = PropositionProxy.objects.get(uuid=proposition.entity_id.uuid)
        candidat = Person.objects.get(global_id=proposition.matricule_candidat)
        signataire = Actor.objects.get(uuid=signataire_id.uuid)

        if isinstance(signataire_id, PromoteurIdentity):
            actor_role = ActorType.PROMOTER.value
        else:
            actor_role = ActorType.CA_MEMBER.value

        # Notifier le doctorant via web si approuvé
        if avis.etat == ChoixEtatSignature.APPROVED.name:
            common_tokens = cls.get_common_tokens(proposition, candidat)
            with translation.override(candidat.language):
                content = _(
                    '<a href="%(admission_link_front)s">%(reference)s</a> - '
                    '%(signataire_first_name)s %(signataire_last_name)s '
                    '(%(actor_role)s) has approved your signature request.'
                ) % dict(
                    **common_tokens,
                    signataire_first_name=signataire.first_name,
                    signataire_last_name=signataire.last_name,
                    actor_role=str(actor_role).lower(),
                )
            web_notification = WebNotification(recipient=candidat, content=content)
            WebNotificationHandler.create(web_notification)

        # Notifier le doctorant via mail
        common_tokens = {
            **cls.get_common_tokens(proposition, candidat),
            "signataire_first_name": signataire.first_name,
            "signataire_last_name": signataire.last_name,
            "signataire_role": actor_role,
        }
        email_message = generate_email(
            ADMISSION_EMAIL_SIGNATURE_CANDIDATE,
            candidat.language,
            {
                **common_tokens,
                "comment": avis.commentaire_externe,
                "decision": ChoixEtatSignature.get_value(avis.etat),
                "reason": avis.motif_refus,
            },
            recipients=[candidat.email],
        )
        EmailNotificationHandler.create(email_message, person=candidat)

        # Notifier les autres promoteurs en cas de refus
        if avis.etat == ChoixEtatSignature.DECLINED.name:
            other_promoters = (
                admission.supervision_group.actors.select_related('person')
                .annotate(type=Subquery(SupervisionActor.objects.filter(actor_ptr=OuterRef('pk')).values('type')[:1]))
                .filter(type=ActorType.PROMOTER.name)
                .exclude(uuid=signataire_id.uuid)
            )
            for other_promoter in other_promoters:
                email_message = generate_email(
                    ADMISSION_EMAIL_SIGNATURE_REFUSAL,
                    other_promoter.language,
                    {
                        **common_tokens,
                        "comment": avis.commentaire_externe,
                        "decision": ChoixEtatSignature.get_value(avis.etat),
                        "reason": avis.motif_refus,
                        "actor_first_name": other_promoter.first_name,
                        "actor_last_name": other_promoter.last_name,
                    },
                    recipients=[other_promoter.email],
                )
                EmailNotificationHandler.create(
                    email_message, person=other_promoter.person_id and other_promoter.person
                )

    @classmethod
    def notifier_soumission(cls, proposition: Proposition) -> None:
        candidat = Person.objects.get(global_id=proposition.matricule_candidat)
        admission = PropositionProxy.objects.get(uuid=proposition.entity_id.uuid)

        # Create the async task to generate the pdf recap
        task = AsyncTask.objects.create(
            name=_('Recap of the proposition %(reference)s') % {'reference': admission.reference},
            description=_('Create the recap of the proposition'),
            person=admission.candidate,
        )
        AdmissionTask.objects.create(
            task=task,
            admission=admission,
            type=AdmissionTask.TaskType.DOCTORATE_RECAP.name,
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
            type=AdmissionTask.TaskType.DOCTORATE_MERGE.name,
        )

        # Notifier le doctorant via mail
        common_tokens = cls.get_common_tokens(proposition, candidat)
        email_message = generate_email(
            ADMISSION_EMAIL_CONFIRM_SUBMISSION_DOCTORATE,
            candidat.language,
            common_tokens,
            recipients=[candidat.private_email],
        )
        EmailNotificationHandler.create(email_message, person=candidat)

        # Envoyer aux gestionnaires CDD
        for manager in get_admission_cdd_managers(admission.training.education_group_id):
            email_message = generate_email(
                ADMISSION_EMAIL_SUBMISSION_CDD,
                manager.language,
                {
                    **common_tokens,
                    "actor_first_name": manager.first_name,
                    "actor_last_name": manager.last_name,
                },
                recipients=[manager.email],
            )
            EmailNotificationHandler.create(email_message, person=manager)

            with translation.override(manager.language):
                content = (
                    _(
                        '<a href="%(admission_link_back)s">%(reference)s</a> - '
                        '%(candidate_first_name)s %(candidate_last_name)s '
                        'submitted request for %(training_title)s'
                    )
                    % common_tokens
                )
                web_notification = WebNotification(recipient=manager, content=str(content))
            WebNotificationHandler.create(web_notification)

        # Envoyer aux membres du groupe de supervision
        actors_invited = admission.supervision_group.actors.select_related('person')
        for actor in actors_invited:
            email_message = generate_email(
                ADMISSION_EMAIL_SUBMISSION_MEMBER,
                actor.language,
                {
                    **common_tokens,
                    "actor_first_name": actor.first_name,
                    "actor_last_name": actor.last_name,
                },
                recipients=[actor.email],
            )
            EmailNotificationHandler.create(email_message, person=actor.person_id and actor.person)

    @classmethod
    def notifier_suppression_membre(cls, proposition: Proposition, signataire_id: 'SignataireIdentity') -> None:
        # Notifier uniquement si le signataire a déjà signé
        admission = PropositionProxy.objects.get(uuid=proposition.entity_id.uuid)
        actor = admission.supervision_group.actors.select_related('person').get(uuid=signataire_id.uuid)
        if actor.state in [SignatureState.APPROVED.name, SignatureState.DECLINED.name]:
            candidat = Person.objects.get(global_id=proposition.matricule_candidat)
            email_message = generate_email(
                ADMISSION_EMAIL_MEMBER_REMOVED,
                actor.language,
                {
                    **cls.get_common_tokens(proposition, candidat),
                    "actor_first_name": actor.first_name,
                    "actor_last_name": actor.last_name,
                },
                recipients=[actor.email],
            )
            EmailNotificationHandler.create(email_message, person=actor.person_id and actor.person)

    @classmethod
    def renvoyer_invitation(cls, proposition: Proposition, membre: SignataireIdentity):
        # Charger le membre et vérifier qu'il est externe et déjà invité
        actor = SupervisionActor.objects.filter(
            uuid=membre.uuid,
            person_id=None,
            last_state=SignatureState.INVITED.name,
        ).first()
        if not actor:
            raise SignataireNonTrouveException

        # Réinitiliser l'état afin de mettre à jour le token
        actor.switch_state(SignatureState.INVITED)
        actor.refresh_from_db()

        # Tokens communs
        candidat = Person.objects.get(global_id=proposition.matricule_candidat)
        common_tokens = cls.get_common_tokens(proposition, candidat)

        # Envoyer aux acteurs n'ayant pas répondu
        tokens = {
            **common_tokens,
            "signataire_first_name": actor.first_name,
            "signataire_last_name": actor.last_name,
            "signataire_role": actor.get_type_display(),
            "admission_link_front": cls._lien_invitation_externe(proposition, actor),
        }
        email_message = generate_email(
            ADMISSION_EMAIL_SIGNATURE_REQUESTS_ACTOR,
            actor.language,
            tokens,
            recipients=[actor.email],
        )
        EmailNotificationHandler.create(email_message)

    @classmethod
    def _lien_invitation_externe(cls, proposition, actor):
        url = settings.ADMISSION_FRONTEND_LINK.format(context='public/doctorate', uuid=proposition.entity_id.uuid)
        return url + f"external-approval/{get_signing_token(actor)}"

    @classmethod
    def envoyer_message_libre_au_candidat(
        cls,
        proposition: Proposition,
        objet_message: str,
        corps_message: str,
    ) -> EmailMessage:
        candidate = Person.objects.get(global_id=proposition.matricule_candidat)

        email_notification = EmailNotification(
            recipient=candidate.private_email,
            subject=objet_message,
            html_content=corps_message,
            plain_text_content=transform_html_to_text(corps_message),
        )

        email_message = EmailNotificationHandler.build(email_notification)
        EmailNotificationHandler.create(email_message, person=candidate)
        return email_message

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
            'training_acronym': proposition.doctorat.sigle,
            'training_campus': proposition.doctorat.campus,
            'requested_submitted_documents': html_list_by_status[StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION],
            'requested_not_submitted_documents': html_list_by_status[StatutEmplacementDocument.A_RECLAMER],
            'enrolment_service_email': admission.training.enrollment_campus.sic_enrollment_email
            or MAIL_INSCRIPTION_DEFAUT,
            'training_year': format_academic_year(proposition.annee_calculee),
            'admission_link_front': get_portal_admission_url('continuing-education', proposition.uuid),
            'admission_link_back': get_backoffice_admission_url('continuing-education', proposition.uuid),
        }

        email_message = generate_email(
            ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_AND_NOT_SUBMITTED_DOCTORATE
            if html_list_by_status[StatutEmplacementDocument.A_RECLAMER]
            else ADMISSION_EMAIL_SUBMISSION_CONFIRM_WITH_SUBMITTED_DOCTORATE,
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
            type=AdmissionTask.TaskType.DOCTORATE_FOLDER.name,
        )

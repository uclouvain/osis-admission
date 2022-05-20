# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Union

from django.conf import settings
from django.db.models import F, OuterRef, Subquery
from django.shortcuts import resolve_url
from django.utils import translation
from django.utils.functional import lazy
from django.utils.translation import get_language, gettext_lazy as _

from admission.auth.roles.cdd_manager import CddManager
from admission.contrib.models import AdmissionTask, SupervisionActor
from admission.contrib.models.doctorate import PropositionProxy
from admission.contrib.models.enums.actor_type import ActorType
from admission.ddd.projet_doctoral.preparation.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.projet_doctoral.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.projet_doctoral.preparation.domain.model._signature_promoteur import ChoixEtatSignature
from admission.ddd.projet_doctoral.preparation.domain.model.doctorat import DoctoratIdentity
from admission.ddd.projet_doctoral.preparation.domain.model.groupe_de_supervision import GroupeDeSupervision
from admission.ddd.projet_doctoral.preparation.domain.model.proposition import Proposition
from admission.ddd.projet_doctoral.preparation.domain.service.i_notification import INotification
from admission.ddd.projet_doctoral.preparation.dtos import AvisDTO
from admission.infrastructure.projet_doctoral.preparation.domain.service.doctorat import DoctoratTranslator
from admission.mail_templates import (
    ADMISSION_EMAIL_MEMBER_REMOVED,
    ADMISSION_EMAIL_SIGNATURE_CANDIDATE,
    ADMISSION_EMAIL_SIGNATURE_REFUSAL,
    ADMISSION_EMAIL_SIGNATURE_REQUESTS_ACTOR,
    ADMISSION_EMAIL_SIGNATURE_REQUESTS_CANDIDATE,
    ADMISSION_EMAIL_SUBMISSION_CANDIDATE,
    ADMISSION_EMAIL_SUBMISSION_MEMBER,
)
from base.models.person import Person
from osis_async.models import AsyncTask
from osis_mail_template import generate_email
from osis_notification.contrib.handlers import EmailNotificationHandler, WebNotificationHandler
from osis_notification.contrib.notification import WebNotification
from osis_signature.enums import SignatureState


class Notification(INotification):
    @classmethod
    def _get_doctorate_title_translation(cls, doctorat_id: DoctoratIdentity):
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
        frontend_link = settings.ADMISSION_FRONTEND_LINK.format(uuid=proposition.entity_id.uuid)
        return {
            "candidate_first_name": candidat.first_name,
            "candidate_last_name": candidat.last_name,
            "doctorate_title": cls._get_doctorate_title_translation(proposition.doctorat_id),
            "admission_link_front": frontend_link,
            "admission_link_front_supervision": "{}supervision".format(frontend_link),
            "admission_link_back": "{}{}".format(
                settings.ADMISSION_BACKEND_LINK_PREFIX.rstrip('/'),
                resolve_url('admission:doctorate:project', pk=proposition.entity_id.uuid),
            ),
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
        actor_list = admission.supervision_group.actors.annotate(
            first_name=F('person__first_name'),
            last_name=F('person__last_name'),
            type=Subquery(SupervisionActor.objects.filter(actor_ptr=OuterRef('pk')).values('type')[:1]),
        ).values("first_name", "last_name", "type")
        common_tokens = cls.get_common_tokens(proposition, candidat)

        # Envoyer au gestionnaire CDD
        cdd_managers = CddManager.objects.filter(
            entity_id=admission.doctorate.management_entity_id,
        ).select_related('person')
        for manager in cdd_managers:
            content = (
                _("%(candidate_first_name)s %(candidate_last_name)s requested signatures for %(doctorate_title)s")
                % common_tokens
            )
            with translation.override(manager.person.language):
                web_notification = WebNotification(recipient=manager.person, content=str(content))
            WebNotificationHandler.create(web_notification)

        # Envoyer au doctorant
        with translation.override(candidat.language):
            actor_list_str = (
                f"{actor['first_name']} {actor['last_name']} ({ActorType[actor['type']].value})" for actor in actor_list
            )
        email_message = generate_email(
            ADMISSION_EMAIL_SIGNATURE_REQUESTS_CANDIDATE,
            candidat.language,
            {
                **common_tokens,
                "actors_as_list_items": '<li></li>'.join(actor_list_str),
                "actors_comma_separated": ', '.join(actor_list_str),
            },
            recipients=[candidat],
        )
        EmailNotificationHandler.create(email_message, person=candidat)

        # Envoyer aux acteurs n'ayant pas répondu
        actors_invited = (
            admission.supervision_group.actors.select_related('person')
            .filter(last_state=SignatureState.INVITED.name)
            .annotate(type=Subquery(SupervisionActor.objects.filter(actor_ptr=OuterRef('pk')).values('type')[:1]))
        )
        for actor in actors_invited:
            email_message = generate_email(
                ADMISSION_EMAIL_SIGNATURE_REQUESTS_ACTOR,
                actor.person.language,
                {
                    **common_tokens,
                    "signataire_first_name": actor.person.first_name,
                    "signataire_last_name": actor.person.last_name,
                    "signataire_role": ActorType[actor.type].value,
                },
                recipients=[actor.person],
            )
            EmailNotificationHandler.create(email_message, person=actor.person)

    @classmethod
    def notifier_avis(
        cls,
        proposition: Proposition,
        signataire_id: Union[PromoteurIdentity, MembreCAIdentity],
        avis: AvisDTO,
    ) -> None:
        admission = PropositionProxy.objects.get(uuid=proposition.entity_id.uuid)
        candidat = Person.objects.get(global_id=proposition.matricule_candidat)
        signataire = Person.objects.get(global_id=signataire_id.matricule)

        if isinstance(signataire_id, PromoteurIdentity):
            actor_role = ActorType.PROMOTER.value
        else:
            actor_role = ActorType.CA_MEMBER.value

        # Notifier le doctorant via web si approuvé
        if avis.etat == ChoixEtatSignature.APPROVED.name:
            with translation.override(candidat.language):
                content = _(
                    "%(signataire_first_name)s %(signataire_last_name)s (%(actor_role)s) has approved "
                    "your signature request."
                ) % dict(
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
            recipients=[candidat],
        )
        EmailNotificationHandler.create(email_message, person=candidat)

        # Notifier les autres promoteurs en cas de refus
        if avis.etat == ChoixEtatSignature.DECLINED.name:
            other_promoters = (
                admission.supervision_group.actors.select_related('person')
                .annotate(type=Subquery(SupervisionActor.objects.filter(actor_ptr=OuterRef('pk')).values('type')[:1]))
                .filter(type=ActorType.PROMOTER.name)
                .exclude(person__global_id=signataire_id.matricule)
            )
            for other_promoter in other_promoters:
                email_message = generate_email(
                    ADMISSION_EMAIL_SIGNATURE_REFUSAL,
                    other_promoter.person.language,
                    {
                        **common_tokens,
                        "comment": avis.commentaire_externe,
                        "decision": ChoixEtatSignature.get_value(avis.etat),
                        "reason": avis.motif_refus,
                        "actor_first_name": other_promoter.person.first_name,
                        "actor_last_name": other_promoter.person.last_name,
                    },
                    recipients=[other_promoter.person],
                )
                EmailNotificationHandler.create(email_message, person=other_promoter.person)

    @classmethod
    def notifier_soumission(cls, proposition: Proposition) -> None:
        candidat = Person.objects.get(global_id=proposition.matricule_candidat)
        admission = PropositionProxy.objects.get(uuid=proposition.entity_id.uuid)

        # Notifier le doctorant via mail
        common_tokens = cls.get_common_tokens(proposition, candidat)
        email_message = generate_email(
            ADMISSION_EMAIL_SUBMISSION_CANDIDATE,
            candidat.language,
            common_tokens,
            recipients=[candidat],
        )
        EmailNotificationHandler.create(email_message, person=candidat)

        # Envoyer aux gestionnaires CDD
        cdd_managers = CddManager.objects.filter(
            entity_id=admission.doctorate.management_entity_id,
        ).select_related('person')
        for manager in cdd_managers:
            email_message = generate_email(
                ADMISSION_EMAIL_SUBMISSION_CANDIDATE,
                manager.person.language,
                {
                    **common_tokens,
                    "actor_first_name": manager.person.first_name,
                    "actor_last_name": manager.person.last_name,
                },
                recipients=[manager.person],
            )
            EmailNotificationHandler.create(email_message, person=manager.person)

            content = (
                _("%(candidate_first_name)s %(candidate_last_name)s submitted request for %(doctorate_title)s")
                % common_tokens
            )
            with translation.override(manager.person.language):
                web_notification = WebNotification(recipient=manager.person, content=str(content))
            WebNotificationHandler.create(web_notification)

        # Envoyer aux membres du groupe de supervision
        actors_invited = admission.supervision_group.actors.select_related('person')
        for actor in actors_invited:
            email_message = generate_email(
                ADMISSION_EMAIL_SUBMISSION_MEMBER,
                actor.person.language,
                {
                    **common_tokens,
                    "actor_first_name": actor.person.first_name,
                    "actor_last_name": actor.person.last_name,
                },
                recipients=[actor.person],
            )
            EmailNotificationHandler.create(email_message, person=actor.person)

    @classmethod
    def notifier_suppression_membre(
        cls,
        proposition: Proposition,
        signataire_id: Union[PromoteurIdentity, MembreCAIdentity],
    ) -> None:
        # Notifier uniquement si le signataire a déjà signé
        admission = PropositionProxy.objects.get(uuid=proposition.entity_id.uuid)
        actor = admission.supervision_group.actors.select_related('person').get(
            person__global_id=signataire_id.matricule
        )
        if actor.state in [SignatureState.APPROVED.name, SignatureState.DECLINED.name]:
            candidat = Person.objects.get(global_id=proposition.matricule_candidat)
            email_message = generate_email(
                ADMISSION_EMAIL_MEMBER_REMOVED,
                actor.person.language,
                {
                    **cls.get_common_tokens(proposition, candidat),
                    "actor_first_name": actor.person.first_name,
                    "actor_last_name": actor.person.last_name,
                },
                recipients=[actor.person],
            )
            EmailNotificationHandler.create(email_message, person=actor.person)

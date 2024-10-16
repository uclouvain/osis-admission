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
from typing import Optional

from django.conf import settings
from django.utils import translation

from admission.ddd.admission.doctorat.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.doctorat.preparation.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    SignataireIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition
from admission.ddd.admission.doctorat.preparation.domain.service.i_historique import IHistorique
from admission.ddd.admission.doctorat.preparation.dtos import AvisDTO
from admission.infrastructure.admission.doctorat.preparation.domain.service.membre_CA import MembreCATranslator
from admission.infrastructure.admission.doctorat.preparation.domain.service.promoteur import PromoteurTranslator
from admission.infrastructure.utils import get_message_to_historize
from ddd.logic.shared_kernel.personne_connue_ucl.dtos import PersonneConnueUclDTO
from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import PersonneConnueUclTranslator
from osis_history.utilities import add_history_entry
import datetime
from django.utils import formats


class Historique(IHistorique):
    @classmethod
    def get_signataire(cls, signataire_id):
        if isinstance(signataire_id, PromoteurIdentity):
            return PromoteurTranslator.get_dto(signataire_id)
        return MembreCATranslator.get_dto(signataire_id)

    @classmethod
    def historiser_initiation(cls, proposition: Proposition):
        candidat = PersonneConnueUclTranslator().get(proposition.matricule_candidat)
        add_history_entry(
            proposition.entity_id.uuid,
            "La proposition a été initiée.",
            "The proposition has been initialized.",
            "{candidat.prenom} {candidat.nom}".format(candidat=candidat),
            tags=["proposition", "status-changed"],
        )

    @classmethod
    def historiser_completion(cls, proposition: Proposition, matricule_auteur: str):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        add_history_entry(
            proposition.entity_id.uuid,
            "La proposition a été modifiée (Projet de recherche).",
            "The proposition has been completed (Research project).",
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["proposition", 'modification'],
        )

    @classmethod
    def historiser_completion_cotutelle(cls, proposition: Proposition, matricule_auteur: str):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        add_history_entry(
            proposition.entity_id.uuid,
            "La proposition a été modifiée (Cotutelle).",
            "The proposition has been completed (Cotutelle).",
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["proposition", 'modification'],
        )

    @classmethod
    def historiser_avis(
        cls,
        proposition: Proposition,
        signataire_id: 'SignataireIdentity',
        avis: AvisDTO,
        statut_original_proposition: 'ChoixStatutPropositionDoctorale',
        matricule_auteur: Optional[str] = '',
    ):
        signataire = cls.get_signataire(signataire_id)
        if matricule_auteur:
            auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        else:
            auteur = signataire

        # Basculer en français pour la traduction de l'état
        with translation.override(settings.LANGUAGE_CODE_FR):
            message_fr = (
                "{signataire.prenom} {signataire.nom} a {action} la proposition {via_pdf}en tant que {role}".format(
                    signataire=signataire,
                    action="refusé" if avis.motif_refus else "aprouvé",
                    via_pdf="via PDF " if avis.pdf else "",
                    role="promoteur"
                    if isinstance(signataire_id, PromoteurIdentity)
                    else "membre du comité d'accompagnement",
                )
            )
            details = []
            if avis.motif_refus:
                details.append("motif : {}".format(avis.motif_refus))
            if avis.commentaire_externe:
                details.append("commentaire : {}".format(avis.commentaire_externe))
            if details:
                details = " ({})".format(' ; '.join(details))
                message_fr += details

        # Anglais
        with translation.override(settings.LANGUAGE_CODE_EN):
            message_en = "{signataire.prenom} {signataire.nom} has {action} the proposition {via_pdf}as {role}".format(
                signataire=signataire,
                action="refused" if avis.motif_refus else "approved",
                via_pdf="via PDF " if avis.pdf else "",
                role="promoter" if isinstance(signataire_id, PromoteurIdentity) else "supervisory panel member",
            )
            details = []
            if avis.motif_refus:
                details.append("reason : {}".format(avis.motif_refus))
            if avis.commentaire_externe:
                details.append("comment : {}".format(avis.commentaire_externe))
            if details:
                details = " ({})".format('; '.join(details))
                message_en += details

        tags = ["proposition", "supervision"]

        if statut_original_proposition != proposition.statut:
            tags.append("status-changed")

        add_history_entry(
            proposition.entity_id.uuid,
            message_fr,
            message_en,
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=tags,
        )

    @classmethod
    def historiser_ajout_membre(
        cls,
        proposition: Proposition,
        groupe_de_supervision: GroupeDeSupervision,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        signataire = cls.get_signataire(signataire_id)
        add_history_entry(
            proposition.entity_id.uuid,
            "{membre.prenom} {membre.nom} a été ajouté en tant que {}.".format(
                "promoteur" if isinstance(signataire_id, PromoteurIdentity) else "membre du comité d'accompagnement",
                membre=signataire,
            ),
            "{membre.prenom} {membre.nom} has been added as {}.".format(
                "promoter" if isinstance(signataire_id, PromoteurIdentity) else "CA member",
                membre=signataire,
            ),
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["proposition", "supervision"],
        )

    @classmethod
    def historiser_suppression_membre(
        cls,
        proposition: Proposition,
        groupe_de_supervision: GroupeDeSupervision,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        signataire = cls.get_signataire(signataire_id)
        add_history_entry(
            proposition.entity_id.uuid,
            "{membre.prenom} {membre.nom} a été retiré des {}.".format(
                "promoteurs" if isinstance(signataire_id, PromoteurIdentity) else "membres du comité d'accompagnement",
                membre=signataire,
            ),
            "{membre.prenom} {membre.nom} has been removed from {}.".format(
                "promoters" if isinstance(signataire_id, PromoteurIdentity) else "CA members",
                membre=signataire,
            ),
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["proposition", "supervision"],
        )

    @classmethod
    def historiser_modification_membre(
        cls,
        proposition: Proposition,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        signataire = cls.get_signataire(signataire_id)
        add_history_entry(
            proposition.entity_id.uuid,
            "{membre.prenom} {membre.nom} a été modifié.".format(membre=signataire),
            "{membre.prenom} {membre.nom} has been updated.".format(membre=signataire),
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["proposition", "supervision"],
        )

    @classmethod
    def historiser_designation_promoteur_reference(
        cls,
        proposition: Proposition,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        signataire = cls.get_signataire(signataire_id)
        add_history_entry(
            proposition.entity_id.uuid,
            "{membre.prenom} {membre.nom} a été désigné comme promoteur de référence.".format(membre=signataire),
            "{membre.prenom} {membre.nom} has been designated as lead supervisor.".format(membre=signataire),
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["proposition", "supervision"],
        )

    @classmethod
    def historiser_send_back_to_candidate(cls, proposition: Proposition, matricule_gestionnaire: str):
        gestionnaire = PersonneConnueUclTranslator.get(matricule_gestionnaire)
        add_history_entry(
            proposition.entity_id.uuid,
            "La main a été redonné au candidat.",
            "Proposition was sent back to the candidate.",
            "{gestionnaire.prenom} {gestionnaire.nom}".format(gestionnaire=gestionnaire),
            tags=["proposition", "supervision", "status-changed"],
        )

    @classmethod
    def historiser_demande_signatures(cls, proposition: Proposition, matricule_auteur: str):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        add_history_entry(
            proposition.entity_id.uuid,
            "Les demandes de signatures ont été envoyées.",
            "Signing requests have been sent.",
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["proposition", "supervision", "status-changed"],
        )

    @classmethod
    def historiser_soumission(cls, proposition: Proposition):
        candidat = PersonneConnueUclTranslator().get(proposition.matricule_candidat)
        add_history_entry(
            proposition.entity_id.uuid,
            "La proposition a été soumise.",
            "The proposition has been submitted.",
            "{candidat.prenom} {candidat.nom}".format(candidat=candidat),
            tags=["proposition", "soumission", "status-changed"],
        )

    @classmethod
    def historiser_suppression(cls, proposition: Proposition):
        candidat = PersonneConnueUclTranslator().get(proposition.matricule_candidat)
        add_history_entry(
            proposition.entity_id.uuid,
            "La proposition a été annulée.",
            "The proposition has been cancelled.",
            "{candidat.prenom} {candidat.nom}".format(candidat=candidat),
            tags=["proposition", "status-changed"],
        )

    @classmethod
    def historiser_message_au_candidat(cls, proposition: Proposition, matricule_emetteur: str, message: EmailMessage):
        emetteur = PersonneConnueUclTranslator.get(matricule_emetteur)

        message_a_historiser = get_message_to_historize(message)

        add_history_entry(
            proposition.entity_id.uuid,
            message_a_historiser[settings.LANGUAGE_CODE_FR],
            message_a_historiser[settings.LANGUAGE_CODE_EN],
            "{emetteur.prenom} {emetteur.nom}".format(emetteur=emetteur),
            tags=["proposition", "message"],
        )

    @classmethod
    def historiser_envoi_fac_par_sic_lors_de_la_decision_facultaire(
        cls,
        proposition: Proposition,
        message: Optional[EmailMessage],
        gestionnaire: str,
    ):
        gestionnaire_dto = PersonneConnueUclTranslator().get(gestionnaire)
        now = formats.date_format(datetime.datetime.now(), "DATETIME_FORMAT")

        if message:
            recipient = message['To']
            fr_message = (
                f'Un mail informant de la soumission du dossier en faculté a été envoyé à "{recipient}" le {now}.'
            )
            en_message = (
                f'An e-mail notifying that the dossier has been submitted to the faculty was sent to "{recipient}" on '
                f'{now}.'
            )
        else:
            fr_message = f"Le dossier a été soumis en faculté le {now}."
            en_message = f"The dossier has been submitted to the faculty on {now}."

        add_history_entry(
            proposition.entity_id.uuid,
            fr_message,
            en_message,
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
            tags=["proposition", "fac-decision", "send-to-fac", "status-changed"],
        )

    @classmethod
    def historiser_envoi_sic_par_fac_lors_de_la_decision_facultaire(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        envoi_par_fac: bool,
    ):
        gestionnaire_dto = PersonneConnueUclTranslator().get(gestionnaire)

        if envoi_par_fac:
            message_fr = "Le dossier a été soumis au SIC par la faculté."
            message_en = "The dossier has been submitted to the SIC by the faculty."
        else:
            message_fr = "Le dossier a été soumis au SIC par le SIC."
            message_en = "The dossier has been submitted to the SIC by the SIC."

        add_history_entry(
            object_uuid=proposition.entity_id.uuid,
            message_fr=message_fr,
            message_en=message_en,
            author="{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
            tags=["proposition", "fac-decision", "send-to-sic", "status-changed"],
        )

    @classmethod
    def historiser_refus_fac(cls, proposition: Proposition, gestionnaire: PersonneConnueUclDTO):
        add_history_entry(
            proposition.entity_id.uuid,
            "La faculté a informé le SIC de son refus.",
            "The faculty informed the SIC of its refusal.",
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire),
            tags=["proposition", "fac-decision", "refusal-send-to-sic", "status-changed"],
        )

    @classmethod
    def historiser_acceptation_fac(cls, proposition: Proposition, gestionnaire: PersonneConnueUclDTO):
        add_history_entry(
            proposition.entity_id.uuid,
            "La faculté a informé le SIC de son acceptation.",
            "The faculty informed the SIC of its approval.",
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire),
            tags=["proposition", "fac-decision", "approval-send-to-sic", "status-changed"],
        )

    @classmethod
    def historiser_refus_sic(cls, proposition: Proposition, message: EmailMessage, gestionnaire: str):
        gestionnaire_dto = PersonneConnueUclTranslator().get(gestionnaire)

        if message is not None:
            message_a_historiser = get_message_to_historize(message)

            add_history_entry(
                proposition.entity_id.uuid,
                message_a_historiser[settings.LANGUAGE_CODE_FR],
                message_a_historiser[settings.LANGUAGE_CODE_EN],
                "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
                tags=["proposition", "sic-decision", "refusal", "message"],
            )

        add_history_entry(
            proposition.entity_id.uuid,
            "Le dossier a été refusé par SIC.",
            "The dossier has been refused by SIC.",
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
            tags=["proposition", "sic-decision", "refusal", "status-changed"],
        )

    @classmethod
    def historiser_acceptation_sic(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: Optional[EmailMessage] = None,
    ):
        gestionnaire_dto = PersonneConnueUclTranslator().get(gestionnaire)

        if message is not None:
            message_a_historiser = get_message_to_historize(message)

            add_history_entry(
                proposition.entity_id.uuid,
                message_a_historiser[settings.LANGUAGE_CODE_FR],
                message_a_historiser[settings.LANGUAGE_CODE_EN],
                "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
                tags=["proposition", "sic-decision", "approval", "message"],
            )

        add_history_entry(
            proposition.entity_id.uuid,
            "Le dossier a été accepté par SIC.",
            "The dossier has been accepted by SIC.",
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
            tags=["proposition", "sic-decision", "approval", "status-changed"],
        )

    @classmethod
    def historiser_mail_acceptation_inscription_sic(
        cls,
        proposition_uuid: str,
        gestionnaire: str,
        message: EmailMessage,
    ):
        gestionnaire_dto = PersonneConnueUclTranslator().get(gestionnaire)

        message_a_historiser = get_message_to_historize(message)

        add_history_entry(
            proposition_uuid,
            message_a_historiser[settings.LANGUAGE_CODE_FR],
            message_a_historiser[settings.LANGUAGE_CODE_EN],
            "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
            tags=["proposition", "sic-decision", "approval", "message"],
        )

    @classmethod
    def historiser_specification_motifs_refus_sic(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        statut_original: ChoixStatutPropositionDoctorale,
    ):
        if statut_original == proposition.statut:
            return

        gestionnaire_dto = PersonneConnueUclTranslator().get(matricule=gestionnaire)

        add_history_entry(
            proposition.entity_id.uuid,
            'Des motifs de refus ont été spécifiés par SIC.',
            'Refusal reasons have been specified by SIC.',
            '{gestionnaire_dto.prenom} {gestionnaire_dto.nom}'.format(gestionnaire_dto=gestionnaire_dto),
            tags=['proposition', 'sic-decision', 'specify-refusal-reasons', 'status-changed'],
        )

    @classmethod
    def historiser_specification_informations_acceptation_sic(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        statut_original: ChoixStatutPropositionDoctorale,
    ):
        if statut_original == proposition.statut:
            return

        gestionnaire_dto = PersonneConnueUclTranslator().get(matricule=gestionnaire)

        add_history_entry(
            proposition.entity_id.uuid,
            'Des informations concernant la décision d\'acceptation ont été spécifiés par SIC.',
            'Approval decision information has been specified by SIC.',
            '{gestionnaire_dto.prenom} {gestionnaire_dto.nom}'.format(gestionnaire_dto=gestionnaire_dto),
            tags=['proposition', 'sic-decision', 'specify-approval-info', 'status-changed'],
        )

    @classmethod
    def historiser_demande_verification_titre_acces(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: EmailMessage,
        uuid_experience: str,
    ):
        manager_dto = PersonneConnueUclTranslator().get(gestionnaire)
        manager_name = f"{manager_dto.prenom} {manager_dto.nom}"

        now = formats.date_format(datetime.datetime.now(), "DATETIME_FORMAT")
        recipient = message['To']
        message_a_historiser = get_message_to_historize(message)

        add_history_entry(
            proposition.entity_id.uuid,
            f'Mail envoyé à "{recipient}" le {now} par {manager_name}.\n\n'
            f'{message_a_historiser[settings.LANGUAGE_CODE_FR]}',
            f'Mail sent to "{recipient}" on {now} by {manager_name}.\n\n'
            f'{message_a_historiser[settings.LANGUAGE_CODE_EN]}',
            manager_name,
            tags=['proposition', 'experience-authentication', 'authentication-request', 'message'],
            extra_data={'experience_id': uuid_experience},
        )

    @classmethod
    def historiser_information_candidat_verification_parcours_en_cours(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: EmailMessage,
        uuid_experience: str,
    ):
        manager_dto = PersonneConnueUclTranslator().get(gestionnaire)
        manager_name = f"{manager_dto.prenom} {manager_dto.nom}"

        now = formats.date_format(datetime.datetime.now(), "DATETIME_FORMAT")
        message_a_historiser = get_message_to_historize(message)

        add_history_entry(
            proposition.entity_id.uuid,
            f'Mail envoyé à le/la candidat·e le {now} par {manager_name}.\n\n'
            f'{message_a_historiser[settings.LANGUAGE_CODE_FR]}',
            f'Mail sent to the candidate on {now} by {manager_name}.\n\n'
            f'{message_a_historiser[settings.LANGUAGE_CODE_EN]}',
            manager_name,
            tags=['proposition', 'experience-authentication', 'institute-contact', 'message'],
            extra_data={'experience_id': uuid_experience},
        )

    @classmethod
    def historiser_derogation_financabilite(
        cls,
        proposition: Proposition,
        gestionnaire: str,
        message: Optional[EmailMessage] = None,
    ):
        gestionnaire_dto = PersonneConnueUclTranslator().get(gestionnaire)
        now = formats.date_format(datetime.datetime.now(), "DATETIME_FORMAT")
        status = proposition.financabilite_derogation_statut.value

        if message is not None:
            message_a_historiser = get_message_to_historize(message)

            add_history_entry(
                proposition.entity_id.uuid,
                message_a_historiser[settings.LANGUAGE_CODE_FR],
                message_a_historiser[settings.LANGUAGE_CODE_EN],
                "{gestionnaire_dto.prenom} {gestionnaire_dto.nom}".format(gestionnaire_dto=gestionnaire_dto),
                tags=['proposition', 'financabilite', 'financabilite-derogation', 'message'],
            )

        add_history_entry(
            proposition.entity_id.uuid,
            f'Le statut de besoin de dérogation à la financabilité est passé à {status} par {gestionnaire_dto.prenom} '
            f'{gestionnaire_dto.nom}.',
            f'Status of financability dispensation needs changed to {status} on {now} by {gestionnaire_dto.prenom} '
            f'{gestionnaire_dto.nom}.',
            '{gestionnaire_dto.prenom} {gestionnaire_dto.nom}'.format(gestionnaire_dto=gestionnaire_dto),
            tags=['proposition', 'financabilite', 'financabilite-derogation'],
        )

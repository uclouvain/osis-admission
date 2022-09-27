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
from django.utils import translation

from admission.ddd.admission.projet_doctoral.preparation.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.admission.projet_doctoral.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.admission.projet_doctoral.preparation.domain.model.groupe_de_supervision import GroupeDeSupervision
from admission.ddd.admission.projet_doctoral.preparation.domain.model.proposition import Proposition
from admission.ddd.admission.projet_doctoral.preparation.domain.service.i_historique import IHistorique
from admission.ddd.admission.projet_doctoral.preparation.dtos import AvisDTO
from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import PersonneConnueUclTranslator
from osis_history.utilities import add_history_entry


class Historique(IHistorique):
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
    def historiser_completion(cls, proposition: Proposition):
        candidat = PersonneConnueUclTranslator().get(proposition.matricule_candidat)
        add_history_entry(
            proposition.entity_id.uuid,
            "La proposition a été modifiée (Projet doctoral).",
            "The proposition has been completed (Doctoral project).",
            "{candidat.prenom} {candidat.nom}".format(candidat=candidat),
            tags=["proposition", 'modification'],
        )

    @classmethod
    def historiser_completion_cotutelle(cls, proposition: Proposition):
        candidat = PersonneConnueUclTranslator().get(proposition.matricule_candidat)
        add_history_entry(
            proposition.entity_id.uuid,
            "La proposition a été modifiée (Cotutelle).",
            "The proposition has been completed (Cotutelle).",
            "{candidat.prenom} {candidat.nom}".format(candidat=candidat),
            tags=["proposition", 'modification'],
        )

    @classmethod
    def historiser_avis(
        cls,
        proposition: Proposition,
        signataire_id: Union[PromoteurIdentity, MembreCAIdentity],
        avis: AvisDTO,
    ):
        signataire = PersonneConnueUclTranslator().get(signataire_id.matricule)
        auteur = PersonneConnueUclTranslator().get(proposition.matricule_candidat) if avis.pdf else signataire

        # Basculer en Français pour la traduction de l'état
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

        add_history_entry(
            proposition.entity_id.uuid,
            message_fr,
            message_en,
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["proposition", "supervision"],
        )

    @classmethod
    def historiser_ajout_membre(
        cls,
        proposition: Proposition,
        groupe_de_supervision: GroupeDeSupervision,
        signataire_id: Union[PromoteurIdentity, MembreCAIdentity],
    ):
        candidat = PersonneConnueUclTranslator().get(proposition.matricule_candidat)
        signataire = PersonneConnueUclTranslator().get(signataire_id.matricule)
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
            "{candidat.prenom} {candidat.nom}".format(candidat=candidat),
            tags=["proposition", "supervision"],
        )

    @classmethod
    def historiser_suppression_membre(
        cls,
        proposition: Proposition,
        groupe_de_supervision: GroupeDeSupervision,
        signataire_id: Union[PromoteurIdentity, MembreCAIdentity],
    ):
        candidat = PersonneConnueUclTranslator().get(proposition.matricule_candidat)
        signataire = PersonneConnueUclTranslator().get(signataire_id.matricule)
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
            "{candidat.prenom} {candidat.nom}".format(candidat=candidat),
            tags=["proposition", "supervision"],
        )

    @classmethod
    def historiser_demande_signatures(cls, proposition: Proposition):
        candidat = PersonneConnueUclTranslator().get(proposition.matricule_candidat)
        add_history_entry(
            proposition.entity_id.uuid,
            "Les demandes de signatures ont été envoyées.",
            "Signing requests have been sent.",
            "{candidat.prenom} {candidat.nom}".format(candidat=candidat),
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

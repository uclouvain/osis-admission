##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Optional, Union
from uuid import UUID

from admission.ddd.preparation.projet_doctoral.builder.proposition_identity_builder import \
    PropositionIdentityBuilder
from admission.ddd.preparation.projet_doctoral.commands import InitierPropositionCommand
from admission.ddd.preparation.projet_doctoral.domain.model._detail_projet import (
    ChoixLangueRedactionThese,
    DetailProjet,
)
from admission.ddd.preparation.projet_doctoral.domain.model._enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixStatutProposition,
    ChoixTypeAdmission,
)
from admission.ddd.preparation.projet_doctoral.domain.model._experience_precedente_recherche import (
    ChoixDoctoratDejaRealise,
    ExperiencePrecedenteRecherche,
    aucune_experience_precedente_recherche,
)
from admission.ddd.preparation.projet_doctoral.domain.model._financement import (
    ChoixTypeFinancement,
    Financement,
    financement_non_rempli,
)
from admission.ddd.preparation.projet_doctoral.domain.model._institut import InstitutIdentity
from admission.ddd.preparation.projet_doctoral.domain.model.doctorat import DoctoratIdentity
from admission.ddd.preparation.projet_doctoral.domain.model.proposition import (
    Proposition,
)
from admission.ddd.preparation.projet_doctoral.domain.validator.validator_by_business_action import \
    InitierPropositionValidatorList
from admission.ddd.preparation.projet_doctoral.repository.i_proposition import IPropositionRepository
from osis_common.ddd import interface


class PropositionBuilder(interface.RootEntityBuilder):

    @classmethod
    def build_from_repository_dto(cls, dto_object: 'interface.DTO') -> 'Proposition':
        raise NotImplementedError

    @classmethod
    def build_from_command(
            cls,
            cmd: 'InitierPropositionCommand'
    ):
        raise NotImplementedError

    @classmethod
    def initier_proposition(
            cls,
            cmd: 'InitierPropositionCommand',
            doctorat_id: 'DoctoratIdentity',
            proposition_repository: 'IPropositionRepository',
    ) -> 'Proposition':
        InitierPropositionValidatorList(
            type_admission=cmd.type_admission,
            justification=cmd.justification,
            type_financement=cmd.type_financement,
            type_contrat_travail=cmd.type_contrat_travail,
            doctorat_deja_realise=cmd.doctorat_deja_realise,
            institution=cmd.institution,
        ).validate()
        commission_proximite: Optional[Union[ChoixCommissionProximiteCDEouCLSM, ChoixCommissionProximiteCDSS]] = None
        if cmd.commission_proximite and cmd.commission_proximite in ChoixCommissionProximiteCDEouCLSM.get_names():
            commission_proximite = ChoixCommissionProximiteCDEouCLSM[cmd.commission_proximite]
        elif cmd.commission_proximite and cmd.commission_proximite in ChoixCommissionProximiteCDSS.get_names():
            commission_proximite = ChoixCommissionProximiteCDSS[cmd.commission_proximite]
        reference = "{}-{}".format(
            doctorat_id.annee % 100,
            Proposition.valeur_reference_base + proposition_repository.get_next_reference(),
        )
        return Proposition(
            entity_id=PropositionIdentityBuilder.build(),
            reference=reference,
            statut=ChoixStatutProposition.IN_PROGRESS,
            justification=cmd.justification,
            type_admission=ChoixTypeAdmission[cmd.type_admission],
            doctorat_id=doctorat_id,
            matricule_candidat=cmd.matricule_candidat,
            commission_proximite=commission_proximite,
            financement=_build_financement(cmd),
            projet=_build_projet(cmd),
            experience_precedente_recherche=_build_experience_precedente_recherche(cmd),
        )


def _build_financement(cmd: 'InitierPropositionCommand') -> 'Financement':
    if cmd.type_financement:
        return Financement(
            type=ChoixTypeFinancement[cmd.type_financement],
            type_contrat_travail=cmd.type_contrat_travail,
            eft=cmd.eft,
            bourse_recherche=cmd.bourse_recherche,
            duree_prevue=cmd.duree_prevue,
            temps_consacre=cmd.temps_consacre,
        )
    return financement_non_rempli


def _build_projet(cmd: 'InitierPropositionCommand') -> 'DetailProjet':
    return DetailProjet(
        titre=cmd.titre_projet or '',
        resume=cmd.resume_projet or '',
        documents=cmd.documents_projet,
        langue_redaction_these=ChoixLangueRedactionThese[cmd.langue_redaction_these],
        institut_these=InstitutIdentity(UUID(cmd.institut_these)) if cmd.institut_these else None,
        lieu_these=cmd.lieu_these or '',
        autre_lieu_these=cmd.autre_lieu_these or '',
        graphe_gantt=cmd.graphe_gantt,
        proposition_programme_doctoral=cmd.proposition_programme_doctoral,
        projet_formation_complementaire=cmd.projet_formation_complementaire,
        lettres_recommandation=cmd.lettres_recommandation,
    )


def _build_experience_precedente_recherche(cmd: 'InitierPropositionCommand') -> 'ExperiencePrecedenteRecherche':
    if cmd.doctorat_deja_realise == ChoixDoctoratDejaRealise.NO.name:
        return aucune_experience_precedente_recherche
    return ExperiencePrecedenteRecherche(
        doctorat_deja_realise=ChoixDoctoratDejaRealise[cmd.doctorat_deja_realise],
        institution=cmd.institution,
        date_soutenance=cmd.date_soutenance,
        raison_non_soutenue=cmd.raison_non_soutenue,
    )

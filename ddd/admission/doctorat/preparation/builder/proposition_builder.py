##############################################################################
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
##############################################################################
from typing import Optional, Union

from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.commands import InitierPropositionCommand
from admission.ddd.admission.doctorat.preparation.domain.model._detail_projet import projet_non_rempli
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    Proposition,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.admission.doctorat.preparation.domain.validator.validator_by_business_action import (
    InitierPropositionValidatorList,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository
from osis_common.ddd import interface


class PropositionBuilder(interface.RootEntityBuilder):
    @classmethod
    def build_from_repository_dto(cls, dto_object: 'interface.DTO') -> 'Proposition':
        raise NotImplementedError

    @classmethod
    def build_from_command(cls, cmd: 'InitierPropositionCommand'):  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    def initier_proposition(
        cls,
        cmd: 'InitierPropositionCommand',
        doctorat_translator: 'IDoctoratTranslator',
        proposition_repository: 'IPropositionRepository',
    ) -> 'Proposition':
        if cmd.pre_admission_associee:
            return cls.initier_nouvelle_proposition_attachee_a_pre_admission(
                cmd,
                doctorat_translator,
                proposition_repository,
            )
        else:
            return cls.initier_nouvelle_proposition_non_attachee_a_pre_admission(
                cmd,
                doctorat_translator,
                proposition_repository,
            )

    @classmethod
    def initier_nouvelle_proposition_non_attachee_a_pre_admission(
        cls,
        cmd: 'InitierPropositionCommand',
        doctorat_translator: 'IDoctoratTranslator',
        proposition_repository: 'IPropositionRepository',
    ) -> 'Proposition':
        doctorat = doctorat_translator.get(cmd.sigle_formation, cmd.annee_formation)
        InitierPropositionValidatorList(
            type_admission=cmd.type_admission,
            justification=cmd.justification,
            commission_proximite=cmd.commission_proximite,
            doctorat=doctorat,
        ).validate()
        commission_proximite: Optional[
            Union[ChoixCommissionProximiteCDEouCLSM, ChoixCommissionProximiteCDSS, ChoixSousDomaineSciences]
        ] = None
        if cmd.commission_proximite and cmd.commission_proximite in ChoixCommissionProximiteCDEouCLSM.get_names():
            commission_proximite = ChoixCommissionProximiteCDEouCLSM[cmd.commission_proximite]
        elif cmd.commission_proximite and cmd.commission_proximite in ChoixCommissionProximiteCDSS.get_names():
            commission_proximite = ChoixCommissionProximiteCDSS[cmd.commission_proximite]
        elif cmd.commission_proximite and cmd.commission_proximite in ChoixSousDomaineSciences.get_names():
            commission_proximite = ChoixSousDomaineSciences[cmd.commission_proximite]
        reference = proposition_repository.recuperer_reference_suivante()

        return Proposition(
            entity_id=PropositionIdentityBuilder.build(),
            reference=reference,
            statut=ChoixStatutPropositionDoctorale.EN_BROUILLON,
            justification=cmd.justification,
            type_admission=ChoixTypeAdmission[cmd.type_admission],
            formation_id=doctorat.entity_id,
            matricule_candidat=cmd.matricule_candidat,
            commission_proximite=commission_proximite,
            projet=projet_non_rempli,
            auteur_derniere_modification=cmd.matricule_candidat,
        )

    @classmethod
    def initier_nouvelle_proposition_attachee_a_pre_admission(
        cls,
        cmd: 'InitierPropositionCommand',
        doctorat_translator: 'IDoctoratTranslator',
        proposition_repository: 'IPropositionRepository',
    ) -> 'Proposition':
        pre_admission = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.pre_admission_associee))

        doctorat = doctorat_translator.get(
            sigle=pre_admission.formation_id.sigle, annee=pre_admission.formation_id.annee
        )

        reference = proposition_repository.recuperer_reference_suivante()

        proposition = Proposition(
            entity_id=PropositionIdentityBuilder.build(),
            reference=reference,
            statut=ChoixStatutPropositionDoctorale.EN_BROUILLON,
            type_admission=ChoixTypeAdmission[cmd.type_admission],
            formation_id=pre_admission.formation_id,
            matricule_candidat=pre_admission.matricule_candidat,
            projet=projet_non_rempli,
            auteur_derniere_modification=cmd.matricule_candidat,
            pre_admission_associee=pre_admission.entity_id,
            curriculum=pre_admission.curriculum,
        )

        proposition.completer(
            doctorat=doctorat,
            justification=pre_admission.justification,
            commission_proximite=pre_admission.commission_proximite.name if pre_admission.commission_proximite else '',
            type_financement=pre_admission.financement.type.name if pre_admission.financement.type else '',
            type_contrat_travail=pre_admission.financement.type_contrat_travail
            if pre_admission.financement.type_contrat_travail
            else '',
            eft=pre_admission.financement.eft,
            bourse_recherche=pre_admission.financement.bourse_recherche,
            autre_bourse_recherche=pre_admission.financement.autre_bourse_recherche,
            bourse_date_debut=pre_admission.financement.bourse_date_debut,
            bourse_date_fin=pre_admission.financement.bourse_date_fin,
            bourse_preuve=pre_admission.financement.bourse_preuve,
            duree_prevue=pre_admission.financement.duree_prevue,
            temps_consacre=pre_admission.financement.temps_consacre,
            est_lie_fnrs_fria_fresh_csc=pre_admission.financement.est_lie_fnrs_fria_fresh_csc,
            commentaire_financement=pre_admission.financement.commentaire,
            langue_redaction_these=pre_admission.projet.langue_redaction_these,
            institut_these=str(pre_admission.projet.institut_these.uuid) if pre_admission.projet.institut_these else '',
            lieu_these=pre_admission.projet.lieu_these,
            titre=pre_admission.projet.titre,
            resume=pre_admission.projet.resume,
            doctorat_deja_realise=pre_admission.experience_precedente_recherche.doctorat_deja_realise.name
            if pre_admission.experience_precedente_recherche.doctorat_deja_realise
            else '',
            institution=pre_admission.experience_precedente_recherche.institution,
            domaine_these=pre_admission.experience_precedente_recherche.domaine_these,
            date_soutenance=pre_admission.experience_precedente_recherche.date_soutenance,
            raison_non_soutenue=pre_admission.experience_precedente_recherche.raison_non_soutenue,
            projet_doctoral_deja_commence=pre_admission.projet.deja_commence,
            projet_doctoral_institution=pre_admission.projet.deja_commence_institution,
            projet_doctoral_date_debut=pre_admission.projet.date_debut,
            documents=pre_admission.projet.documents,
            graphe_gantt=pre_admission.projet.graphe_gantt,
            proposition_programme_doctoral=pre_admission.projet.proposition_programme_doctoral,
            projet_formation_complementaire=pre_admission.projet.projet_formation_complementaire,
            lettres_recommandation=pre_admission.projet.lettres_recommandation,
        )

        return proposition

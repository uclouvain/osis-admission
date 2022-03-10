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
from admission.ddd.projet_doctoral.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.projet_doctoral.preparation.commands import GetPropositionCommand
from admission.ddd.projet_doctoral.preparation.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.projet_doctoral.preparation.domain.service.i_secteur_ucl import ISecteurUclTranslator
from admission.ddd.projet_doctoral.preparation.dtos import AfficherPropositionDTO
from admission.ddd.projet_doctoral.preparation.repository.i_proposition import IPropositionRepository


def recuperer_proposition(
    cmd: 'GetPropositionCommand',
    proposition_repository: 'IPropositionRepository',
    doctorat_translator: 'IDoctoratTranslator',
    secteur_ucl_translator: 'ISecteurUclTranslator',
) -> 'AfficherPropositionDTO':
    dto = proposition_repository.get_dto(PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition))
    return AfficherPropositionDTO(
        uuid=dto.uuid,
        type_admission=dto.type_admission,
        reference=dto.reference,
        justification=dto.justification,
        sigle_doctorat=dto.sigle_doctorat,
        annee_doctorat=dto.annee_doctorat,
        intitule_doctorat=dto.intitule_doctorat,
        matricule_candidat=dto.matricule_candidat,
        code_secteur_formation=dto.code_secteur_formation,
        commission_proximite=dto.commission_proximite,
        type_financement=dto.type_financement,
        type_contrat_travail=dto.type_contrat_travail,
        eft=dto.eft,
        bourse_recherche=dto.bourse_recherche,
        duree_prevue=dto.duree_prevue,
        temps_consacre=dto.temps_consacre,
        titre_projet=dto.titre_projet,
        resume_projet=dto.resume_projet,
        documents_projet=dto.documents_projet,
        graphe_gantt=dto.graphe_gantt,
        proposition_programme_doctoral=dto.proposition_programme_doctoral,
        projet_formation_complementaire=dto.projet_formation_complementaire,
        lettres_recommandation=dto.lettres_recommandation,
        langue_redaction_these=dto.langue_redaction_these,
        institut_these=dto.institut_these,
        lieu_these=dto.lieu_these,
        doctorat_deja_realise=dto.doctorat_deja_realise,
        institution=dto.institution,
        date_soutenance=dto.date_soutenance,
        raison_non_soutenue=dto.raison_non_soutenue,
        statut=dto.statut,
    )

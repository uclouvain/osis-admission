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
from admission.ddd.preparation.projet_doctoral.builder.proposition_identity_builder import \
    PropositionIdentityBuilder
from admission.ddd.preparation.projet_doctoral.domain.model.proposition import Proposition
from admission.ddd.preparation.projet_doctoral.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.preparation.projet_doctoral.domain.service.i_secteur_ucl import ISecteurUclTranslator
from admission.ddd.preparation.projet_doctoral.dtos import PropositionDTO, PropositionSearchDTO
from admission.ddd.preparation.projet_doctoral.repository.i_proposition import IPropositionRepository
from osis_common.ddd import interface


class GetPropositionDTODomainService(interface.DomainService):
    @classmethod
    def get(
            cls,
            uuid_proposition: str,
            repository: 'IPropositionRepository',
            doctorat_translator: 'IDoctoratTranslator',
            secteur_ucl_translator: 'ISecteurUclTranslator',
    ) -> 'PropositionDTO':
        proposition = repository.get(PropositionIdentityBuilder.build_from_uuid(uuid_proposition))
        doctorat = doctorat_translator.get_dto(proposition.doctorat_id.sigle, proposition.doctorat_id.annee)
        return PropositionDTO(
            type_admission=proposition.type_admission.name,
            reference=proposition.reference,
            sigle_doctorat=proposition.doctorat_id.sigle,
            annee_doctorat=proposition.doctorat_id.annee,
            intitule_doctorat_fr=doctorat.intitule_fr,
            intitule_doctorat_en=doctorat.intitule_en,
            matricule_candidat=proposition.matricule_candidat,
            justification=proposition.justification,
            code_secteur_formation=secteur_ucl_translator.get(doctorat.sigle_entite_gestion).sigle,
            bureau_CDE=proposition.bureau_CDE and proposition.bureau_CDE.name,
            type_financement=proposition.financement.type and proposition.financement.type.name,
            type_contrat_travail=proposition.financement.type_contrat_travail,
            eft=proposition.financement.eft,
            bourse_recherche=proposition.financement.bourse_recherche,
            duree_prevue=proposition.financement.duree_prevue,
            temps_consacre=proposition.financement.temps_consacre,
            titre_projet=proposition.projet.titre,
            resume_projet=proposition.projet.resume,
            documents_projet=proposition.projet.documents,
            graphe_gantt=proposition.projet.graphe_gantt,
            proposition_programme_doctoral=proposition.projet.proposition_programme_doctoral,
            projet_formation_complementaire=proposition.projet.projet_formation_complementaire,
            lettres_recommandation=proposition.projet.lettres_recommandation,
            langue_redaction_these=proposition.projet.langue_redaction_these,
            institut_these=proposition.projet.institut_these.uuid if proposition.projet.institut_these else None,
            lieu_these=proposition.projet.lieu_these,
            autre_lieu_these=proposition.projet.autre_lieu_these,
            doctorat_deja_realise=proposition.experience_precedente_recherche.doctorat_deja_realise.name,
            institution=proposition.experience_precedente_recherche.institution,
            date_soutenance=proposition.experience_precedente_recherche.date_soutenance,
            raison_non_soutenue=proposition.experience_precedente_recherche.raison_non_soutenue,
            statut=proposition.statut.name,
        )

    @classmethod
    def search_dto(
            cls,
            proposition: 'Proposition',
            doctorat_translator: 'IDoctoratTranslator',
            secteur_ucl_translator: 'ISecteurUclTranslator',
    ) -> 'PropositionSearchDTO':
        doctorat = doctorat_translator.get_dto(proposition.doctorat_id.sigle, proposition.doctorat_id.annee)
        secteur = secteur_ucl_translator.get(doctorat.sigle_entite_gestion)
        return PropositionSearchDTO(
            uuid=proposition.entity_id.uuid,
            reference=proposition.reference,
            type_admission=proposition.type_admission,
            sigle_doctorat=doctorat.sigle,
            matricule_candidat=proposition.matricule_candidat,
            code_secteur_formation=secteur.sigle,
            intitule_secteur_formation=secteur.intitule,
            bureau_CDE=proposition.bureau_CDE,
            intitule_doctorat_en=doctorat.intitule_en,
            intitule_doctorat_fr=doctorat.intitule_fr,
            creee_le=proposition.creee_le,
            statut=proposition.statut.name,
        )

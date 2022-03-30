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
from typing import Dict, List

from admission.ddd.projet_doctoral.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.projet_doctoral.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.projet_doctoral.preparation.repository.i_proposition import IPropositionRepository
from admission.ddd.projet_doctoral.validation.commands import FiltrerDemandesQuery
from admission.ddd.projet_doctoral.validation.domain.service.proposition_identity import PropositionIdentityTranslator
from admission.ddd.projet_doctoral.validation.dtos import DemandeDTO, DemandeRechercheDTO
from admission.ddd.projet_doctoral.validation.repository.i_demande import IDemandeRepository
from osis_common.ddd import interface


class PropositionAvecDemande(interface.DomainService):
    @classmethod
    def rechercher(
        cls,
        cmd: FiltrerDemandesQuery,
        proposition_repository: 'IPropositionRepository',
        demande_repository: 'IDemandeRepository',
    ) -> List["DemandeRechercheDTO"]:
        proposition_ids = cls._recherche_combinee(cmd, proposition_repository, demande_repository)

        proposition_dtos = proposition_repository.search_dto(entity_ids=proposition_ids)
        demande_ids = [
            PropositionIdentityTranslator.convertir_en_demande(proposition_id) for proposition_id in proposition_ids
        ]
        demande_dto_mapping: Dict[str, DemandeDTO] = {
            demande_dto.uuid: demande_dto for demande_dto in demande_repository.search_dto(entity_ids=demande_ids)
        }

        resultats = [
            DemandeRechercheDTO(
                uuid=proposition_dto.uuid,
                numero_demande=proposition_dto.reference,
                statut_cdd=demande_dto_mapping[proposition_dto.uuid].statut_cdd
                if proposition_dto.uuid in demande_dto_mapping
                else None,
                statut_sic=demande_dto_mapping[proposition_dto.uuid].statut_sic
                if proposition_dto.uuid in demande_dto_mapping
                else None,
                statut_demande=proposition_dto.statut,
                nom_candidat=', '.join([proposition_dto.nom_candidat, proposition_dto.prenom_candidat]),
                formation='{} - {}'.format(proposition_dto.sigle_doctorat, proposition_dto.intitule_doctorat),
                nationalite=proposition_dto.nationalite_candidat,
                derniere_modification=proposition_dto.modifiee_le,
                date_confirmation=(
                    demande_dto_mapping[proposition_dto.uuid].admission_confirmee_le
                    or demande_dto_mapping[proposition_dto.uuid].pre_admission_confirmee_le
                )
                if proposition_dto.uuid in demande_dto_mapping
                else None,
                code_bourse=proposition_dto.bourse_recherche,
            )
            for proposition_dto in proposition_dtos
        ]

        # Tri
        champ_tri = cmd.champ_tri or ''
        if champ_tri:
            resultats.sort(
                # We use a tuple to manage the None values
                key=lambda demande: (getattr(demande, champ_tri) is None, getattr(demande, champ_tri)),
                reverse=cmd.tri_inverse,
            )

        return resultats

    @classmethod
    def _recherche_combinee(
        cls,
        cmd: FiltrerDemandesQuery,
        proposition_repository: 'IPropositionRepository',
        demande_repository: 'IDemandeRepository',
    ) -> List['PropositionIdentity']:
        proposition_criteria = [
            "numero",
            "matricule_candidat",
            "nationalite",
            "type",
            "commission_proximite",
            "annee_academique",
            "sigles_formations",
            "type_financement",
            "type_contrat_travail",
            "bourse_recherche",
            "matricule_promoteur",
            "cdds",
        ]
        demande_criteria = [
            "etat_cdd",
            "etat_sic",
            "date_pre_admission_debut",
            "date_pre_admission_fin",
        ]
        proposition_ids_from_proposition = None
        proposition_ids_from_demande = None
        # Search proposition if any proposition criteria
        if any(getattr(cmd, criterion) for criterion in proposition_criteria) or cmd.cotutelle is not None:
            proposition_ids_from_proposition = [
                PropositionIdentityBuilder.build_from_uuid(dto.uuid)
                for dto in proposition_repository.search_dto(
                    numero=cmd.numero,
                    matricule_candidat=cmd.matricule_candidat,
                    nationalite=cmd.nationalite,
                    type=cmd.type,
                    commission_proximite=cmd.commission_proximite,
                    annee_academique=cmd.annee_academique,
                    sigles_formations=cmd.sigles_formations,
                    financement=cmd.type_financement,
                    type_contrat_travail=cmd.type_contrat_travail,
                    bourse_recherche=cmd.bourse_recherche,
                    matricule_promoteur=cmd.matricule_promoteur,
                    cotutelle=cmd.cotutelle,
                    cdds=cmd.cdds,
                )
            ]
        # Search demandes if any demande criteria
        if any(getattr(cmd, criterion) for criterion in demande_criteria):
            proposition_ids_from_demande = [
                PropositionIdentityBuilder.build_from_uuid(dto.uuid)
                for dto in demande_repository.search_dto(
                    etat_cdd=cmd.etat_cdd,
                    etat_sic=cmd.etat_sic,
                )
            ]
        # Only work with proposition identities
        if proposition_ids_from_proposition is not None and proposition_ids_from_demande is not None:
            # Search both and intersect
            return list(set(proposition_ids_from_proposition) & set(proposition_ids_from_demande))
        return proposition_ids_from_proposition or proposition_ids_from_demande or []

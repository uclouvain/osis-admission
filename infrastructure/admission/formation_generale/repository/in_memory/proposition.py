# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from dataclasses import dataclass
from typing import List, Optional

import factory

from admission.ddd import CODE_BACHELIER_VETERINAIRE
from admission.ddd.admission.dtos.profil_candidat import ProfilCandidatDTO
from admission.ddd.admission.enums import TypeSituationAssimilation
from admission.ddd.admission.enums.emplacement_document import TypeEmplacementDocument, StatutEmplacementDocument
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.admission.formation_generale.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.formation_generale.dtos import PropositionDTO
from admission.ddd.admission.formation_generale.dtos.proposition import PropositionGestionnaireDTO
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.formation_generale.test.factory.proposition import (
    PropositionFactory,
    _PropositionIdentityFactory,
)
from admission.ddd.admission.repository.i_proposition import formater_reference
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.infrastructure.admission.domain.service.in_memory.bourse import BourseInMemoryTranslator
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.formation import (
    FormationGeneraleInMemoryTranslator,
)
from admission.infrastructure.admission.repository.in_memory.proposition import GlobalPropositionInMemoryRepository
from admission.infrastructure.utils import dto_to_dict
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


@dataclass
class _Candidat:
    prenom: str
    nom: str
    nationalite: str


@dataclass
class _Formation:
    intitule: str
    campus: str
    type: str


class PropositionInMemoryRepository(
    GlobalPropositionInMemoryRepository,
    InMemoryGenericRepository,
    IPropositionRepository,
):
    entities: List['Proposition'] = []
    countries = {
        'BE': 'Belgium',
        'FR': 'France',
    }
    documents_libres_sic_uclouvain = {
        'uuid-MASTER-SCI': ['24de0c3d-3c06-4c93-8eb4-c8648f04f142'],
    }
    documents_libres_fac_uclouvain = {
        'uuid-MASTER-SCI': ['24de0c3d-3c06-4c93-8eb4-c8648f04f143'],
    }

    @classmethod
    def get(cls, entity_id: 'PropositionIdentity') -> 'Proposition':
        proposition = super().get(entity_id)
        if not proposition:
            raise PropositionNonTrouveeException
        return proposition

    @classmethod
    def search_dto(cls, matricule_candidat: Optional[str] = '') -> List['PropositionDTO']:
        propositions = [
            cls._load_dto(proposition)
            for proposition in cls.entities
            if proposition.matricule_candidat == matricule_candidat
        ]
        return propositions

    @classmethod
    def search(
        cls,
        entity_ids: Optional[List['PropositionIdentity']] = None,
        matricule_candidat: str = None,
        **kwargs,
    ) -> List['Proposition']:
        returned = cls.entities
        if matricule_candidat:
            returned = filter(lambda p: p.matricule_candidat == matricule_candidat, returned)
        if entity_ids:  # pragma: no cover
            returned = filter(lambda p: p.entity_id in entity_ids, returned)
        return list(returned)

    @classmethod
    def reset(cls):
        cls.entities = [
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-MASTER-SCI'),
                matricule_candidat='0000000001',
                formation_id=FormationIdentityFactory(sigle="MASTER-SCI", annee=2021),
                bourse_double_diplome_id=BourseInMemoryTranslator.bourse_dd_1.entity_id,
                bourse_erasmus_mundus_id=BourseInMemoryTranslator.bourse_em_1.entity_id,
                bourse_internationale_id=BourseInMemoryTranslator.bourse_ifg_1.entity_id,
                curriculum=['file1.pdf'],
                reponses_questions_specifiques={
                    '16de0c3d-3c06-4c93-8eb4-c8648f04f140': 'My response 0',
                    '16de0c3d-3c06-4c93-8eb4-c8648f04f141': 'My response 1',
                    '16de0c3d-3c06-4c93-8eb4-c8648f04f142': 'My response 2',
                    '16de0c3d-3c06-4c93-8eb4-c8648f04f143': 'My response 3',
                    '16de0c3d-3c06-4c93-8eb4-c8648f04f144': 'My response 4',
                    '16de0c3d-3c06-4c93-8eb4-c8648f04f145': ['24de0c3d-3c06-4c93-8eb4-c8648f04f144'],
                },
                documents_demandes={
                    'CURRICULUM.CURRICULUM': {
                        'last_actor': '00321234',
                        'reason': 'Le document est à mettre à jour.',
                        'type': TypeEmplacementDocument.NON_LIBRE.name,
                        'last_action_at': '2023-01-02T00:00:00',
                        'status': StatutEmplacementDocument.RECLAME.name,
                        'requested_at': '2023-01-02T00:00:00',
                        'deadline_at': '2023-01-19',
                        'automatically_required': False,
                    },
                    'LIBRE_CANDIDAT.16de0c3d-3c06-4c93-8eb4-c8648f04f146': {
                        'last_actor': '00987890',
                        'reason': 'Ce nouveau document pourrait être intéressant.',
                        'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
                        'last_action_at': '2023-01-03T00:00:00',
                        'status': StatutEmplacementDocument.RECLAME.name,
                        'requested_at': '2023-01-03T00:00:00',
                        'deadline_at': '2023-01-19',
                        'automatically_required': False,
                    },
                },
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-BACHELIER-ECO1'),
                matricule_candidat='0000000001',
                formation_id=FormationIdentityFactory(sigle="BACHELIER-ECO", annee=2020),
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-BACHELIER-VET'),
                matricule_candidat='0000000001',
                formation_id=FormationIdentityFactory(sigle=CODE_BACHELIER_VETERINAIRE, annee=2020),
                est_non_resident_au_sens_decret=False,
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-AGGREGATION-ECO'),
                matricule_candidat='0000000002',
                formation_id=FormationIdentityFactory(sigle="AGGREGATION-ECO", annee=2020),
                curriculum=['file1.pdf'],
                equivalence_diplome=['file1.pdf'],
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-CAPAES-ECO'),
                matricule_candidat='0000000002',
                formation_id=FormationIdentityFactory(sigle="CAPAES-ECO", annee=2020),
                curriculum=['file1.pdf'],
                equivalence_diplome=['file1.pdf'],
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-BACHELIER-ECO2'),
                matricule_candidat='0123456789',
                formation_id=FormationIdentityFactory(sigle="BACHELIER-ECO", annee=2020),
                bourse_erasmus_mundus_id=BourseInMemoryTranslator.bourse_em_1.entity_id,
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-MASTER-SCI-CONFIRMED'),
                matricule_candidat='0000000001',
                formation_id=FormationIdentityFactory(sigle="MASTER-SCI", annee=2021),
                curriculum=['file1.pdf'],
                est_confirmee=True,
            ),
        ]

    @classmethod
    def get_dto(cls, entity_id: 'PropositionIdentity') -> 'PropositionDTO':
        return cls._load_dto(cls.get(entity_id))

    @classmethod
    def _load_dto(cls, proposition: Proposition) -> PropositionDTO:
        candidat = ProfilCandidatInMemoryTranslator.get_identification(proposition.matricule_candidat)
        formation = FormationGeneraleInMemoryTranslator.get_dto(
            proposition.formation_id.sigle,
            proposition.formation_id.annee,
        )

        return PropositionDTO(
            uuid=proposition.entity_id.uuid,
            reference=formater_reference(
                reference=proposition.reference,
                nom_campus_inscription=formation.campus_inscription,
                sigle_entite_gestion=formation.sigle_entite_gestion,
                annee=proposition.formation_id.annee,
            ),
            matricule_candidat=proposition.matricule_candidat,
            prenom_candidat=candidat.prenom,
            nom_candidat=candidat.nom,
            creee_le=proposition.creee_le,
            modifiee_le=proposition.modifiee_le,
            statut=proposition.statut.name,
            erreurs=[],
            formation=formation,
            annee_calculee=proposition.annee_calculee,
            pot_calcule=proposition.pot_calcule and proposition.pot_calcule.name or '',
            date_fin_pot=None,
            soumise_le=None,
            bourse_double_diplome=BourseInMemoryTranslator.get_dto(proposition.bourse_double_diplome_id.uuid)
            if proposition.bourse_double_diplome_id
            else None,
            bourse_erasmus_mundus=BourseInMemoryTranslator.get_dto(proposition.bourse_erasmus_mundus_id.uuid)
            if proposition.bourse_erasmus_mundus_id
            else None,
            bourse_internationale=BourseInMemoryTranslator.get_dto(proposition.bourse_internationale_id.uuid)
            if proposition.bourse_internationale_id
            else None,
            reponses_questions_specifiques=proposition.reponses_questions_specifiques,
            equivalence_diplome=proposition.equivalence_diplome,
            curriculum=proposition.curriculum,
            est_bachelier_belge=proposition.est_bachelier_belge,
            est_non_resident_au_sens_decret=proposition.est_non_resident_au_sens_decret,
            elements_confirmation=proposition.elements_confirmation,
            est_modification_inscription_externe=proposition.est_modification_inscription_externe,
            formulaire_modification_inscription=proposition.formulaire_modification_inscription,
            est_reorientation_inscription_externe=proposition.est_reorientation_inscription_externe,
            attestation_inscription_reguliere=proposition.attestation_inscription_reguliere,
            pdf_recapitulatif=[],
            documents_demandes=proposition.documents_demandes,
            documents_libres_sic_uclouvain=cls.documents_libres_sic_uclouvain.get(proposition.entity_id.uuid, []),
            documents_libres_fac_uclouvain=cls.documents_libres_fac_uclouvain.get(proposition.entity_id.uuid, []),
        )

    @classmethod
    def get_dto_for_gestionnaire(cls, entity_id: 'PropositionIdentity') -> 'PropositionGestionnaireDTO':
        proposition = cls.get(entity_id=entity_id)
        propositions = cls.search_dto(matricule_candidat=proposition.matricule_candidat)
        base_proposition = cls._load_dto(proposition)

        candidat = ProfilCandidatInMemoryTranslator.get_identification(proposition.matricule_candidat)

        return PropositionGestionnaireDTO(
            **dto_to_dict(base_proposition),
            type='',
            date_changement_statut=base_proposition.modifiee_le,
            genre_candidat=candidat.genre,
            noma_candidat=candidat.noma_derniere_inscription_ucl,
            adresse_email_candidat=candidat.email,
            langue_contact_candidat=candidat.langue_contact,
            nationalite_candidat=candidat.pays_nationalite,
            nationalite_ue_candidat=candidat.pays_nationalite_europeen,
            photo_identite_candidat=candidat.photo_identite,
            poursuite_de_cycle_a_specifier=proposition.poursuite_de_cycle_a_specifier,
            poursuite_de_cycle=proposition.poursuite_de_cycle if proposition.poursuite_de_cycle_a_specifier else '',
            candidat_a_plusieurs_demandes=any(
                proposition.statut == ChoixStatutPropositionGenerale.EN_BROUILLON for proposition in propositions
            ),
            titre_access='',
            candidat_assimile=proposition.comptabilite.type_situation_assimilation
            and proposition.comptabilite.type_situation_assimilation != TypeSituationAssimilation.AUCUNE_ASSIMILATION,
            fraudeur_ares=False,
            non_financable=False,
            est_inscription_tardive=proposition.est_inscription_tardive,
            profil_soumis_candidat=ProfilCandidatDTO(
                prenom=proposition.profil_soumis_candidat.prenom,
                nom=proposition.profil_soumis_candidat.nom,
                genre=proposition.profil_soumis_candidat.genre,
                nationalite=proposition.profil_soumis_candidat.nationalite,
                nom_pays_nationalite=cls.countries.get(proposition.profil_soumis_candidat.nationalite, ''),
                pays=proposition.profil_soumis_candidat.pays,
                nom_pays=cls.countries.get(proposition.profil_soumis_candidat.pays, ''),
                code_postal=proposition.profil_soumis_candidat.code_postal,
                ville=proposition.profil_soumis_candidat.ville,
                lieu_dit=proposition.profil_soumis_candidat.lieu_dit,
                rue=proposition.profil_soumis_candidat.rue,
                numero_rue=proposition.profil_soumis_candidat.numero_rue,
                boite_postale=proposition.profil_soumis_candidat.boite_postale,
            )
            if proposition.profil_soumis_candidat
            else None,
        )

# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import random
from dataclasses import dataclass
from typing import List, Optional

import factory

from admission.constants import ADMISSION_POOL_ACADEMIC_CALENDAR_TYPES
from admission.ddd import CODE_BACHELIER_VETERINAIRE
from admission.ddd.admission.domain.service.i_unites_enseignement_translator import (
    IUnitesEnseignementTranslator,
)
from admission.ddd.admission.dtos.formation import BaseFormationDTO
from admission.ddd.admission.dtos.profil_candidat import ProfilCandidatDTO
from admission.ddd.admission.enums import TypeSituationAssimilation
from admission.ddd.admission.enums.emplacement_document import (
    StatutEmplacementDocument,
    StatutReclamationEmplacementDocument,
    TypeEmplacementDocument,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    DROITS_INSCRIPTION_MONTANT_VALEURS,
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    Proposition,
    PropositionIdentity,
)
from admission.ddd.admission.formation_generale.domain.service.checklist import (
    Checklist,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    PropositionNonTrouveeException,
)
from admission.ddd.admission.formation_generale.dtos import PropositionDTO
from admission.ddd.admission.formation_generale.dtos.motif_refus import MotifRefusDTO
from admission.ddd.admission.formation_generale.dtos.proposition import (
    PropositionGestionnaireDTO,
)
from admission.ddd.admission.formation_generale.repository.i_proposition import (
    IPropositionRepository,
)
from admission.ddd.admission.formation_generale.test.factory.proposition import (
    PropositionFactory,
    _PropositionIdentityFactory,
)
from admission.ddd.admission.repository.i_proposition import formater_reference
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.infrastructure.admission.domain.service.in_memory.poste_diplomatique import (
    PosteDiplomatiqueInMemoryTranslator,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import (
    ProfilCandidatInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.formation import (
    FormationGeneraleInMemoryTranslator,
)
from admission.infrastructure.admission.repository.in_memory.proposition import (
    GlobalPropositionInMemoryRepository,
)
from admission.infrastructure.utils import dto_to_dict
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository
from infrastructure.reference.domain.service.in_memory.bourse import (
    BourseInMemoryTranslator,
)


@dataclass
class _MotifRefus:
    intitule: str
    categorie: str


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
    motifs_refus = {
        'uuid-refus-1': _MotifRefus(intitule='Motif 1', categorie='Categorie 1'),
        'uuid-refus-2': _MotifRefus(intitule='Motif 2', categorie='Categorie 2'),
        'uuid-refus-3': _MotifRefus(intitule='Motif 3', categorie='Categorie 3'),
    }

    @classmethod
    def save(cls, entity: 'Proposition', mise_a_jour_date_derniere_modification=True) -> None:
        return super().save(entity)

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
                        'automatically_required': False,
                        'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
                    },
                    'LIBRE_CANDIDAT.16de0c3d-3c06-4c93-8eb4-c8648f04f146': {
                        'last_actor': '00987890',
                        'reason': 'Ce nouveau document pourrait être intéressant.',
                        'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
                        'last_action_at': '2023-01-03T00:00:00',
                        'status': StatutEmplacementDocument.RECLAME.name,
                        'requested_at': '2023-01-03T00:00:00',
                        'automatically_required': False,
                        'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT.name,
                    },
                },
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-BACHELIER-ECO1'),
                matricule_candidat='0000000001',
                formation_id=FormationIdentityFactory(sigle="BACHELIER-ECO", annee=2020),
                avec_bourse_double_diplome=None,
                avec_bourse_internationale=None,
                avec_bourse_erasmus_mundus=None,
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
                pot_calcule=random.choice(list(ADMISSION_POOL_ACADEMIC_CALENDAR_TYPES)),
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-CERTIFICATE-CONFIRMED'),
                matricule_candidat='0000000002',
                formation_id=FormationIdentityFactory(sigle="CERTIF-BUS", annee=2021),
                curriculum=['file1.pdf'],
                est_confirmee=True,
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-BACHELIER-FINANCABILITE'),
                matricule_candidat='0000000001',
                formation_id=FormationIdentityFactory(sigle="ABCD2MC", annee=2024),
                curriculum=['file1.pdf'],
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-MASTER-MC'),
                matricule_candidat='0000000001',
                formation_id=FormationIdentityFactory(sigle="MASTER-MC", annee=2020),
                annee_calculee=2020,
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-MASTER-M4'),
                matricule_candidat='0000000001',
                formation_id=FormationIdentityFactory(sigle="MASTER-M4", annee=2020),
                annee_calculee=2020,
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-MASTER-M5'),
                matricule_candidat='0000000001',
                formation_id=FormationIdentityFactory(sigle="MASTER-M5", annee=2020),
                annee_calculee=2020,
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
        poste_diplomatique = (
            PosteDiplomatiqueInMemoryTranslator.get_dto(
                code=proposition.poste_diplomatique.code,
            )
            if proposition.poste_diplomatique
            else None
        )

        return PropositionDTO(
            uuid=proposition.entity_id.uuid,
            reference=formater_reference(
                reference=proposition.reference,
                nom_campus_inscription=formation.campus_inscription.nom,
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
            avec_bourse_double_diplome=bool(proposition.avec_bourse_double_diplome),
            bourse_double_diplome=(
                BourseInMemoryTranslator.get_dto(proposition.bourse_double_diplome_id.uuid)
                if proposition.bourse_double_diplome_id
                else None
            ),
            avec_bourse_erasmus_mundus=bool(proposition.avec_bourse_erasmus_mundus),
            bourse_erasmus_mundus=(
                BourseInMemoryTranslator.get_dto(proposition.bourse_erasmus_mundus_id.uuid)
                if proposition.bourse_erasmus_mundus_id
                else None
            ),
            avec_bourse_internationale=bool(proposition.avec_bourse_internationale),
            bourse_internationale=(
                BourseInMemoryTranslator.get_dto(proposition.bourse_internationale_id.uuid)
                if proposition.bourse_internationale_id
                else None
            ),
            reponses_questions_specifiques=proposition.reponses_questions_specifiques,
            equivalence_diplome=proposition.equivalence_diplome,
            curriculum=proposition.curriculum,
            est_bachelier_belge=proposition.est_bachelier_belge,
            est_non_resident_au_sens_decret=proposition.est_non_resident_au_sens_decret,
            elements_confirmation=proposition.elements_confirmation,
            est_modification_inscription_externe=proposition.est_modification_inscription_externe,
            formulaire_modification_inscription=proposition.formulaire_modification_inscription,
            attestation_inscription_reguliere_pour_modification_inscription=(
                proposition.attestation_inscription_reguliere_pour_modification_inscription
            ),
            est_reorientation_inscription_externe=proposition.est_reorientation_inscription_externe,
            attestation_inscription_reguliere=proposition.attestation_inscription_reguliere,
            formulaire_reorientation=proposition.formulaire_reorientation,
            pdf_recapitulatif=['recap.pdf'],
            documents_demandes=proposition.documents_demandes,
            echeance_demande_documents=proposition.echeance_demande_documents,
            documents_libres_sic_uclouvain=cls.documents_libres_sic_uclouvain.get(proposition.entity_id.uuid, []),
            documents_libres_fac_uclouvain=cls.documents_libres_fac_uclouvain.get(proposition.entity_id.uuid, []),
            certificat_refus_fac=proposition.certificat_refus_fac,
            certificat_approbation_fac=proposition.certificat_approbation_fac,
            certificat_approbation_sic=proposition.certificat_approbation_sic,
            certificat_approbation_sic_annexe=proposition.certificat_approbation_sic_annexe,
            certificat_refus_sic=proposition.certificat_refus_sic,
            documents_additionnels=proposition.documents_additionnels,
            poste_diplomatique=poste_diplomatique,
            derogation_delegue_vrae=(
                proposition.derogation_delegue_vrae.name if proposition.derogation_delegue_vrae else ''
            ),
            derogation_delegue_vrae_commentaire=proposition.derogation_delegue_vrae_commentaire,
            justificatif_derogation_delegue_vrae=proposition.justificatif_derogation_delegue_vrae,
            financabilite_regle_calcule=(
                proposition.financabilite_regle_calcule.name if proposition.financabilite_regle_calcule else ''
            ),
            financabilite_regle_calcule_situation=(
                proposition.financabilite_regle_calcule_situation.name
                if proposition.financabilite_regle_calcule_situation
                else ''
            ),
            financabilite_regle_calcule_le=proposition.financabilite_regle_calcule_le,
            financabilite_regle=proposition.financabilite_regle.name if proposition.financabilite_regle else '',
            financabilite_etabli_par=proposition.financabilite_etabli_par,
            financabilite_etabli_le=proposition.financabilite_etabli_le,
            financabilite_derogation_statut=(
                proposition.financabilite_derogation_statut.name if proposition.financabilite_derogation_statut else ''
            ),
            financabilite_derogation_vrae=proposition.financabilite_derogation_vrae,
            financabilite_derogation_premiere_notification_le=(
                proposition.financabilite_derogation_premiere_notification_le
            ),
            financabilite_derogation_premiere_notification_par=(
                proposition.financabilite_derogation_premiere_notification_par
            ),
            financabilite_derogation_derniere_notification_le=(
                proposition.financabilite_derogation_derniere_notification_le
            ),
            financabilite_derogation_derniere_notification_par=(
                proposition.financabilite_derogation_derniere_notification_par
            ),
            doit_fournir_visa_etudes=proposition.doit_fournir_visa_etudes,
            visa_etudes_d=proposition.visa_etudes_d,
            certificat_autorisation_signe=proposition.certificat_autorisation_signe,
            type=proposition.type_demande.name if proposition.type_demande else '',
        )

    @classmethod
    def get_dto_for_gestionnaire(
        cls,
        entity_id: 'PropositionIdentity',
        unites_enseignement_translator: 'IUnitesEnseignementTranslator',
    ) -> 'PropositionGestionnaireDTO':
        proposition = cls.get(entity_id=entity_id)
        propositions = cls.search_dto(matricule_candidat=proposition.matricule_candidat)
        base_proposition = cls._load_dto(proposition)
        motifs_refus = [cls.motifs_refus.get(motif_refus.uuid) for motif_refus in proposition.motifs_refus]
        candidat = ProfilCandidatInMemoryTranslator.get_identification(proposition.matricule_candidat)
        formation_choisie_fac = (
            FormationGeneraleInMemoryTranslator.get_dto(
                proposition.autre_formation_choisie_fac_id.sigle,
                proposition.autre_formation_choisie_fac_id.annee,
            )
            if proposition.autre_formation_choisie_fac_id
            else None
        )

        return PropositionGestionnaireDTO(
            **dto_to_dict(base_proposition),
            date_changement_statut=base_proposition.modifiee_le,
            genre_candidat=candidat.genre,
            noma_candidat=candidat.noma_derniere_inscription_ucl,
            adresse_email_candidat=candidat.email,
            langue_contact_candidat=candidat.langue_contact,
            nationalite_candidat=candidat.pays_nationalite,
            nationalite_candidat_fr=candidat.nom_pays_nationalite,
            nationalite_candidat_en=candidat.nom_pays_nationalite,
            nationalite_ue_candidat=candidat.pays_nationalite_europeen,
            photo_identite_candidat=candidat.photo_identite,
            poursuite_de_cycle_a_specifier=proposition.poursuite_de_cycle_a_specifier,
            poursuite_de_cycle=proposition.poursuite_de_cycle if proposition.poursuite_de_cycle_a_specifier else '',
            candidat_a_plusieurs_demandes=any(
                proposition.statut == ChoixStatutPropositionGenerale.EN_BROUILLON for proposition in propositions
            ),
            titre_acces='',
            candidat_assimile=proposition.comptabilite.type_situation_assimilation
            and proposition.comptabilite.type_situation_assimilation != TypeSituationAssimilation.AUCUNE_ASSIMILATION,
            fraudeur_ares=False,
            non_financable=False,
            est_inscription_tardive=proposition.est_inscription_tardive,
            profil_soumis_candidat=(
                ProfilCandidatDTO(
                    prenom=proposition.profil_soumis_candidat.prenom,
                    nom=proposition.profil_soumis_candidat.nom,
                    genre=proposition.profil_soumis_candidat.genre,
                    nationalite=proposition.profil_soumis_candidat.nationalite,
                    nom_pays_nationalite=cls.countries.get(proposition.profil_soumis_candidat.nationalite, ''),
                    date_naissance=proposition.profil_soumis_candidat.date_naissance,
                    pays=proposition.profil_soumis_candidat.pays,
                    nom_pays=cls.countries.get(proposition.profil_soumis_candidat.pays, ''),
                    code_postal=proposition.profil_soumis_candidat.code_postal,
                    ville=proposition.profil_soumis_candidat.ville,
                    rue=proposition.profil_soumis_candidat.rue,
                    numero_rue=proposition.profil_soumis_candidat.numero_rue,
                    boite_postale=proposition.profil_soumis_candidat.boite_postale,
                )
                if proposition.profil_soumis_candidat
                else None
            ),
            type_de_refus=proposition.type_de_refus,
            motifs_refus=[MotifRefusDTO(motif=motif.intitule, categorie=motif.categorie) for motif in motifs_refus],
            autre_formation_choisie_fac=formation_choisie_fac
            and BaseFormationDTO(
                sigle=formation_choisie_fac.sigle,
                annee=formation_choisie_fac.annee,
                uuid='',
                intitule=formation_choisie_fac.intitule,
                lieu_enseignement=formation_choisie_fac.campus.name,
            ),
            avec_conditions_complementaires=proposition.avec_conditions_complementaires,
            conditions_complementaires=proposition.conditions_complementaires_libres,
            avec_complements_formation=proposition.avec_complements_formation,
            complements_formation=[],
            commentaire_complements_formation=proposition.commentaire_complements_formation,
            nombre_annees_prevoir_programme=proposition.nombre_annees_prevoir_programme,
            nom_personne_contact_programme_annuel_annuel=proposition.nom_personne_contact_programme_annuel_annuel,
            email_personne_contact_programme_annuel_annuel=proposition.email_personne_contact_programme_annuel_annuel,
            commentaire_programme_conjoint=proposition.commentaire_programme_conjoint,
            condition_acces=proposition.condition_acces.name if proposition.condition_acces else '',
            millesime_condition_acces=proposition.millesime_condition_acces,
            type_equivalence_titre_acces=(
                proposition.type_equivalence_titre_acces if proposition.type_equivalence_titre_acces else ''
            ),
            information_a_propos_de_la_restriction=proposition.information_a_propos_de_la_restriction,
            statut_equivalence_titre_acces=(
                proposition.statut_equivalence_titre_acces if proposition.statut_equivalence_titre_acces else ''
            ),
            etat_equivalence_titre_acces=(
                proposition.etat_equivalence_titre_acces if proposition.etat_equivalence_titre_acces else ''
            ),
            date_prise_effet_equivalence_titre_acces=proposition.date_prise_effet_equivalence_titre_acces,
            besoin_de_derogation=proposition.besoin_de_derogation,
            droits_inscription_montant=proposition.droits_inscription_montant,
            droits_inscription_montant_valeur=DROITS_INSCRIPTION_MONTANT_VALEURS.get(
                proposition.droits_inscription_montant
            ),
            droits_inscription_montant_autre=proposition.droits_inscription_montant_autre,
            dispense_ou_droits_majores=proposition.dispense_ou_droits_majores,
            tarif_particulier=proposition.tarif_particulier,
            refacturation_ou_tiers_payant=proposition.refacturation_ou_tiers_payant,
            annee_de_premiere_inscription_et_statut=proposition.annee_de_premiere_inscription_et_statut,
            est_mobilite=proposition.est_mobilite,
            nombre_de_mois_de_mobilite=proposition.nombre_de_mois_de_mobilite,
            doit_se_presenter_en_sic=proposition.doit_se_presenter_en_sic,
            communication_au_candidat=proposition.communication_au_candidat,
            nationalite_candidat_code_iso=candidat.pays_nationalite,
        )

    @classmethod
    def initialiser_checklist_proposition(cls, proposition_id: 'PropositionIdentity'):
        from admission.infrastructure.admission.formation_generale.domain.service.in_memory.question_specifique import (
            QuestionSpecifiqueInMemoryTranslator,
        )

        proposition = cls.get(proposition_id)
        Checklist.initialiser(
            proposition=proposition,
            formation=FormationGeneraleInMemoryTranslator.get(proposition.formation_id),
            profil_candidat_translator=ProfilCandidatInMemoryTranslator(),
            annee_courante=proposition.annee_calculee,
            questions_specifiques_translator=QuestionSpecifiqueInMemoryTranslator(),
        )

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
from dataclasses import dataclass
from typing import List, Optional

from admission.ddd.admission.doctorat.preparation.domain.model.enums import STATUTS_PROPOSITION_DOCTORALE_NON_SOUMISE
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.checklist import Checklist
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.doctorat.preparation.dtos import PropositionDTO
from admission.ddd.admission.doctorat.preparation.dtos import PropositionGestionnaireDTO
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionAdmissionECGE3DPMinimaleFactory,
    PropositionAdmissionESP3DPMinimaleFactory,
    PropositionAdmissionSC3DPAvecMembresEtCotutelleFactory,
    PropositionAdmissionSC3DPAvecMembresFactory,
    PropositionAdmissionSC3DPAvecMembresInvitesFactory,
    PropositionAdmissionSC3DPAvecPromoteurDejaApprouveFactory,
    PropositionAdmissionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactory,
    PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
    PropositionAdmissionSC3DPMinimaleCotutelleAvecPromoteurExterneFactory,
    PropositionAdmissionSC3DPMinimaleCotutelleSansPromoteurExterneFactory,
    PropositionAdmissionSC3DPMinimaleFactory,
    PropositionAdmissionSC3DPMinimaleSansCotutelleFactory,
    PropositionAdmissionSC3DPMinimaleSansDetailProjetFactory,
    PropositionAdmissionSC3DPMinimaleSansFinancementFactory,
    PropositionAdmissionSC3DPSansMembreCAFactory,
    PropositionAdmissionSC3DPSansPromoteurFactory,
    PropositionAdmissionSC3DPSansPromoteurReferenceFactory,
    PropositionPreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
    PropositionPreAdmissionSC3DPMinimaleFactory,
    PropositionAdmissionSC3DPConfirmeeFactory,
)
from admission.ddd.admission.domain.service.i_unites_enseignement_translator import IUnitesEnseignementTranslator
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.repository.i_proposition import formater_reference
from admission.infrastructure.admission.doctorat.preparation.domain.service.in_memory.doctorat import (
    DoctoratInMemoryTranslator,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.admission.domain.service.in_memory.bourse import BourseInMemoryTranslator
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator
from admission.infrastructure.admission.repository.in_memory.proposition import GlobalPropositionInMemoryRepository
from admission.infrastructure.utils import dto_to_dict
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


@dataclass
class _Candidat:
    prenom: str
    nom: str
    nationalite: str
    langue_contact: str


@dataclass
class _Institut:
    nom: str
    acronyme: str


@dataclass
class _Doctorat:
    intitule: str
    code_secteur: str
    intitule_secteur: str
    campus: str
    type: str
    campus_inscription: str


class PropositionInMemoryRepository(
    GlobalPropositionInMemoryRepository,
    InMemoryGenericRepository,
    IPropositionRepository,
):
    candidats = {
        "0123456789": _Candidat("Jean", "Dupont", "France", "FR"),
        "0000000001": _Candidat("Michel", "Durand", "Belgique", "FR"),
        "candidat": _Candidat("Pierre", "Dupond", "Belgique", "FR"),
    }
    instituts = {
        '06de0c3d-3c06-4c93-8eb4-c8648f04f140': _Institut("Institut de l'enseignement supérieur", "IES"),
        '06de0c3d-3c06-4c93-8eb4-c8648f04f141': _Institut("Institut du sport", "IS"),
    }
    documents_libres_sic_uclouvain = {
        'uuid-CERTIFICATE-SCI': ['24de0c3d-3c06-4c93-8eb4-c8648f04f142'],
    }
    documents_libres_fac_uclouvain = {
        'uuid-CERTIFICATE-SCI': ['24de0c3d-3c06-4c93-8eb4-c8648f04f143'],
    }
    entities: List['Proposition'] = []

    @classmethod
    def get(cls, entity_id: 'PropositionIdentity') -> 'Proposition':
        proposition = super().get(entity_id)
        if not proposition:
            raise PropositionNonTrouveeException
        return proposition

    @classmethod
    def reset(cls):
        cls.entities = [
            PropositionAdmissionSC3DPMinimaleFactory(),
            PropositionAdmissionSC3DPAvecMembresFactory(),
            PropositionAdmissionSC3DPAvecMembresEtCotutelleFactory(),
            PropositionAdmissionSC3DPAvecMembresInvitesFactory(),
            PropositionAdmissionECGE3DPMinimaleFactory(),
            PropositionPreAdmissionSC3DPMinimaleFactory(),
            PropositionAdmissionSC3DPMinimaleSansDetailProjetFactory(),
            PropositionAdmissionSC3DPMinimaleSansFinancementFactory(),
            PropositionAdmissionSC3DPMinimaleSansCotutelleFactory(),
            PropositionAdmissionSC3DPMinimaleCotutelleSansPromoteurExterneFactory(),
            PropositionAdmissionSC3DPMinimaleCotutelleAvecPromoteurExterneFactory(),
            PropositionAdmissionSC3DPSansPromoteurFactory(),
            PropositionAdmissionSC3DPSansPromoteurReferenceFactory(),
            PropositionAdmissionSC3DPSansMembreCAFactory(),
            PropositionAdmissionESP3DPMinimaleFactory(),
            PropositionAdmissionSC3DPAvecPromoteurDejaApprouveFactory(),
            PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(),
            PropositionPreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(),
            PropositionAdmissionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactory(),
            PropositionAdmissionSC3DPConfirmeeFactory(),
        ]

    @classmethod
    def save(cls, entity: 'Proposition') -> None:
        super().save(entity)

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
    def search_dto(
        cls,
        numero: Optional[int] = None,
        matricule_candidat: Optional[str] = '',
        etat: Optional[str] = '',
        nationalite: Optional[str] = '',
        type: Optional[str] = '',
        cdds: Optional[List[str]] = None,
        commission_proximite: Optional[str] = '',
        annee_academique: Optional[int] = None,
        sigles_formations: Optional[List[str]] = None,
        financement: Optional[str] = '',
        type_contrat_travail: Optional[str] = '',
        bourse_recherche: Optional[str] = '',
        matricule_promoteur: Optional[str] = '',
        cotutelle: Optional[bool] = None,
        entity_ids: Optional[List['PropositionIdentity']] = None,
    ) -> List['PropositionDTO']:
        returned = cls.entities
        if matricule_candidat:
            returned = filter(lambda p: p.matricule_candidat == matricule_candidat, returned)
        if numero is not None:
            returned = filter(lambda p: p.reference == numero, returned)
        if type:
            returned = filter(lambda p: p.type_admission.name == type, returned)
        if entity_ids is not None:
            returned = filter(lambda p: p.entity_id in entity_ids, returned)
        return list(cls._load_dto(proposition) for proposition in returned)

    @classmethod
    def get_dto(cls, entity_id: 'PropositionIdentity') -> 'PropositionDTO':
        return cls._load_dto(cls.get(entity_id))

    @classmethod
    def _load_dto(cls, proposition: 'Proposition'):
        candidat = cls.candidats[proposition.matricule_candidat]
        doctorat = DoctoratInMemoryTranslator.get_dto(
            sigle=proposition.formation_id.sigle,
            annee=proposition.formation_id.annee,
        )
        secteur_doctorat = DoctoratInMemoryTranslator.secteurs_par_doctorat.get(proposition.formation_id.sigle, '')
        intitule_secteur = (
            DoctoratInMemoryTranslator.intitules_secteurs.get(secteur_doctorat, '') if secteur_doctorat else ''
        )
        institut = (
            cls.instituts.get(str(proposition.projet.institut_these.uuid))
            if proposition.projet.institut_these
            else None
        )
        bourse_recherche_dto = (
            BourseInMemoryTranslator.get_dto(uuid=str(proposition.financement.bourse_recherche.uuid))
            if proposition.financement.bourse_recherche
            else None
        )
        return PropositionDTO(
            uuid=proposition.entity_id.uuid,
            type_admission=proposition.type_admission.name,
            reference=formater_reference(
                reference=proposition.reference,
                nom_campus_inscription=doctorat.campus_inscription.nom,
                sigle_entite_gestion=secteur_doctorat,
                annee=proposition.formation_id.annee,
            ),
            doctorat=DoctoratInMemoryTranslator.get_dto(
                sigle=proposition.formation_id.sigle,
                annee=proposition.formation_id.annee,
            ),
            annee_calculee=proposition.annee_calculee,
            type_demande=TypeDemande.ADMISSION.name,
            pot_calcule=proposition.pot_calcule and proposition.pot_calcule.name or '',
            date_fin_pot=None,
            matricule_candidat=proposition.matricule_candidat,
            justification=proposition.justification,
            code_secteur_formation=secteur_doctorat,
            commission_proximite=proposition.commission_proximite and proposition.commission_proximite.name or '',
            type_financement=proposition.financement.type and proposition.financement.type.name or '',
            type_contrat_travail=proposition.financement.type_contrat_travail,
            eft=proposition.financement.eft,
            autre_bourse_recherche=proposition.financement.autre_bourse_recherche,
            bourse_recherche=bourse_recherche_dto,
            bourse_date_debut=proposition.financement.bourse_date_debut,
            bourse_date_fin=proposition.financement.bourse_date_fin,
            bourse_preuve=proposition.financement.bourse_preuve,
            duree_prevue=proposition.financement.duree_prevue,
            temps_consacre=proposition.financement.temps_consacre,
            est_lie_fnrs_fria_fresh_csc=(
                proposition.financement.est_lie_fnrs_fria_fresh_csc if proposition.financement else None
            ),
            commentaire_financement=proposition.financement.commentaire if proposition.financement else '',
            titre_projet=proposition.projet.titre,
            resume_projet=proposition.projet.resume,
            documents_projet=proposition.projet.documents,
            graphe_gantt=proposition.projet.graphe_gantt,
            proposition_programme_doctoral=proposition.projet.proposition_programme_doctoral,
            projet_formation_complementaire=proposition.projet.projet_formation_complementaire,
            lettres_recommandation=proposition.projet.lettres_recommandation,
            langue_redaction_these=proposition.projet.langue_redaction_these.name,
            institut_these=proposition.projet.institut_these.uuid if proposition.projet.institut_these else None,
            nom_institut_these=institut.nom if institut else '',
            sigle_institut_these=institut.acronyme if institut else '',
            lieu_these=proposition.projet.lieu_these,
            projet_doctoral_deja_commence=proposition.projet.deja_commence if proposition.projet else None,
            projet_doctoral_institution=proposition.projet.deja_commence_institution if proposition.projet else '',
            projet_doctoral_date_debut=proposition.projet.date_debut if proposition.projet else None,
            doctorat_deja_realise=proposition.experience_precedente_recherche.doctorat_deja_realise.name,
            institution=proposition.experience_precedente_recherche.institution,
            domaine_these=proposition.experience_precedente_recherche.domaine_these,
            date_soutenance=proposition.experience_precedente_recherche.date_soutenance,
            raison_non_soutenue=proposition.experience_precedente_recherche.raison_non_soutenue,
            statut=proposition.statut.name,
            creee_le=proposition.creee_le,
            fiche_archive_signatures_envoyees=proposition.fiche_archive_signatures_envoyees,
            intitule_secteur_formation=intitule_secteur,
            nom_candidat=candidat.nom,
            prenom_candidat=candidat.prenom,
            nationalite_candidat=candidat.nationalite,
            langue_contact_candidat=candidat.langue_contact,
            modifiee_le=proposition.modifiee_le,
            erreurs=[],
            reponses_questions_specifiques=proposition.reponses_questions_specifiques,
            curriculum=proposition.curriculum,
            elements_confirmation=proposition.elements_confirmation,
            pdf_recapitulatif=['recap.pdf'],
            soumise_le=None,
            documents_demandes=proposition.documents_demandes,
            documents_libres_fac_uclouvain=cls.documents_libres_fac_uclouvain.get(proposition.entity_id.uuid, []),
            documents_libres_sic_uclouvain=cls.documents_libres_sic_uclouvain.get(proposition.entity_id.uuid, []),
            financabilite_regle_calcule=proposition.financabilite_regle_calcule.name
            if proposition.financabilite_regle_calcule
            else '',
            financabilite_regle_calcule_situation=proposition.financabilite_regle_calcule_situation.name
            if proposition.financabilite_regle_calcule_situation
            else '',
            financabilite_regle_calcule_le=proposition.financabilite_regle_calcule_le,
            financabilite_regle=proposition.financabilite_regle.name if proposition.financabilite_regle else '',
            financabilite_etabli_par=proposition.financabilite_etabli_par,
            financabilite_etabli_le=proposition.financabilite_etabli_le,
            financabilite_derogation_statut=proposition.financabilite_derogation_statut.name
            if proposition.financabilite_derogation_statut
            else '',
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
            certificat_refus_fac=proposition.certificat_refus_fac,
            certificat_approbation_fac=proposition.certificat_approbation_fac,
            certificat_approbation_sic=proposition.certificat_approbation_sic,
            certificat_approbation_sic_annexe=proposition.certificat_approbation_sic_annexe,
            certificat_refus_sic=proposition.certificat_refus_sic,
            doit_fournir_visa_etudes=proposition.doit_fournir_visa_etudes,
            visa_etudes_d=proposition.visa_etudes_d,
            certificat_autorisation_signe=proposition.certificat_autorisation_signe,
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
        candidat = ProfilCandidatInMemoryTranslator.get_identification(proposition.matricule_candidat)

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
            candidat_a_plusieurs_demandes=any(
                other_proposition.statut not in STATUTS_PROPOSITION_DOCTORALE_NON_SOUMISE
                and other_proposition.uuid != entity_id.uuid
                for other_proposition in propositions
            ),
            cotutelle=GroupeDeSupervisionInMemoryRepository.get_cotutelle_dto(uuid_proposition=entity_id.uuid),
            profil_soumis_candidat=None,
        )

    @classmethod
    def initialiser_checklist_proposition(cls, proposition_id: 'PropositionIdentity'):
        proposition = cls.get(proposition_id)
        Checklist.initialiser(
            proposition=proposition,
            profil_candidat_translator=ProfilCandidatInMemoryTranslator(),
            annee_courante=proposition.annee_calculee,
        )

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
import datetime
import uuid
from typing import Dict, List, Optional, Union

import attr

from admission.ddd.admission.doctorat.preparation.domain.model._comptabilite import (
    Comptabilite,
    comptabilite_non_remplie,
)
from admission.ddd.admission.doctorat.preparation.domain.model._detail_projet import (
    DetailProjet,
)
from admission.ddd.admission.doctorat.preparation.domain.model._experience_precedente_recherche import (
    ExperiencePrecedenteRecherche,
    aucune_experience_precedente_recherche,
)
from admission.ddd.admission.doctorat.preparation.domain.model._financement import (
    Financement,
    financement_non_rempli,
)
from admission.ddd.admission.doctorat.preparation.domain.model._institut import InstitutIdentity
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import Doctorat
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixDoctoratDejaRealise,
    ChoixSousDomaineSciences,
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
    ChoixTypeFinancement,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.validator_by_business_action import (
    CompletionPropositionValidatorList,
    ModifierTypeAdmissionValidatorList,
    PropositionProjetDoctoralValidatorList,
)
from admission.ddd.admission.domain.model._profil_candidat import ProfilCandidat
from admission.ddd.admission.domain.model.bourse import BourseIdentity
from admission.ddd.admission.domain.model.enums.type_gestionnaire import TypeGestionnaire
from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.enums import (
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    ChoixAssimilation6,
    ChoixTypeCompteBancaire,
    LienParente,
    TypeSituationAssimilation,
)
from admission.ddd.admission.enums.type_demande import TypeDemande
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class PropositionIdentity(interface.EntityIdentity):
    uuid: str


@attr.dataclass(slots=True, hash=False, eq=False)
class Proposition(interface.RootEntity):
    entity_id: 'PropositionIdentity'
    type_admission: ChoixTypeAdmission
    formation_id: 'FormationIdentity'
    matricule_candidat: str
    reference: int
    projet: 'DetailProjet'
    auteur_derniere_modification: str = ''
    annee_calculee: Optional[int] = None
    type_demande: 'TypeDemande' = TypeDemande.ADMISSION
    pot_calcule: Optional[AcademicCalendarTypes] = None
    justification: Optional[str] = ''
    statut: ChoixStatutPropositionDoctorale = ChoixStatutPropositionDoctorale.EN_BROUILLON
    commission_proximite: Optional[
        Union[
            ChoixCommissionProximiteCDEouCLSM,
            ChoixCommissionProximiteCDSS,
            ChoixSousDomaineSciences,
        ]
    ] = None
    financement: 'Financement' = financement_non_rempli
    experience_precedente_recherche: 'ExperiencePrecedenteRecherche' = aucune_experience_precedente_recherche

    creee_le: Optional[datetime.datetime] = None
    modifiee_le: Optional[datetime.datetime] = None

    profil_soumis_candidat: ProfilCandidat = None

    fiche_archive_signatures_envoyees: List[str] = attr.Factory(list)
    comptabilite: 'Comptabilite' = comptabilite_non_remplie
    reponses_questions_specifiques: Dict = attr.Factory(dict)
    curriculum: List[str] = attr.Factory(list)
    elements_confirmation: Dict[str, str] = attr.Factory(dict)
    documents_demandes: Dict = attr.Factory(dict)

    @property
    def sigle_formation(self):
        return self.formation_id.sigle

    @property
    def annee(self):
        return self.formation_id.annee

    valeur_reference_base = 300000

    @property
    def est_verrouillee_pour_signature(self) -> bool:
        return self.statut == ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE

    def est_en_cours(self):
        return self.statut != ChoixStatutPropositionDoctorale.ANNULEE

    def completer(
        self,
        doctorat: Doctorat,
        justification: Optional[str],
        commission_proximite: Optional[str],
        type_financement: Optional[str],
        type_contrat_travail: Optional[str],
        eft: Optional[int],
        bourse_recherche: Optional[BourseIdentity],
        autre_bourse_recherche: Optional[str],
        bourse_date_debut: Optional[datetime.date],
        bourse_date_fin: Optional[datetime.date],
        bourse_preuve: List[str],
        duree_prevue: Optional[int],
        temps_consacre: Optional[int],
        est_lie_fnrs_fria_fresh_csc: Optional[bool],
        commentaire_financement: Optional[str],
        langue_redaction_these: str,
        institut_these: Optional[str],
        lieu_these: Optional[str],
        titre: Optional[str],
        resume: Optional[str],
        doctorat_deja_realise: str,
        institution: Optional[str],
        domaine_these: Optional[str],
        date_soutenance: Optional[datetime.date],
        raison_non_soutenue: Optional[str],
        projet_doctoral_deja_commence: Optional[bool],
        projet_doctoral_institution: Optional[str],
        projet_doctoral_date_debut: Optional[datetime.date],
        documents: List[str] = None,
        graphe_gantt: List[str] = None,
        proposition_programme_doctoral: List[str] = None,
        projet_formation_complementaire: List[str] = None,
        lettres_recommandation: List[str] = None,
    ) -> None:
        CompletionPropositionValidatorList(
            type_admission=self.type_admission.name,
            type_financement=type_financement,
            justification=justification,
            type_contrat_travail=type_contrat_travail,
            doctorat_deja_realise=doctorat_deja_realise,
            institution=institution,
            domaine_these=domaine_these,
            doctorat=doctorat,
            commission_proximite=commission_proximite,
        ).validate()
        self._completer_proposition(justification, commission_proximite)
        self._completer_financement(
            type=type_financement,
            type_contrat_travail=type_contrat_travail,
            eft=eft,
            bourse_recherche=bourse_recherche,
            autre_bourse_recherche=autre_bourse_recherche,
            bourse_date_debut=bourse_date_debut,
            bourse_date_fin=bourse_date_fin,
            bourse_preuve=bourse_preuve,
            duree_prevue=duree_prevue,
            temps_consacre=temps_consacre,
            est_lie_fnrs_fria_fresh_csc=est_lie_fnrs_fria_fresh_csc,
            commentaire=commentaire_financement,
        )
        self._completer_projet(
            titre=titre,
            resume=resume,
            langue_redaction_these=langue_redaction_these,
            institut_these=institut_these,
            lieu_these=lieu_these,
            deja_commence=projet_doctoral_deja_commence,
            deja_commence_institution=projet_doctoral_institution,
            date_debut=projet_doctoral_date_debut,
            documents=documents,
            graphe_gantt=graphe_gantt,
            proposition_programme_doctoral=proposition_programme_doctoral,
            projet_formation_complementaire=projet_formation_complementaire,
            lettres_recommandation=lettres_recommandation,
        )
        self._completer_experience_precedente(
            doctorat_deja_realise=doctorat_deja_realise,
            institution=institution,
            domaine_these=domaine_these,
            date_soutenance=date_soutenance,
            raison_non_soutenue=raison_non_soutenue,
        )

    def _completer_proposition(
        self,
        justification: Optional[str],
        commission_proximite: Optional[str],
    ):
        self.justification = justification or ''
        self._definir_commission(commission_proximite)

    def _definir_commission(self, commission_proximite):
        self.commission_proximite = None
        if commission_proximite and commission_proximite in ChoixCommissionProximiteCDEouCLSM.get_names():
            self.commission_proximite = ChoixCommissionProximiteCDEouCLSM[commission_proximite]
        elif commission_proximite and commission_proximite in ChoixCommissionProximiteCDSS.get_names():
            self.commission_proximite = ChoixCommissionProximiteCDSS[commission_proximite]
        elif commission_proximite and commission_proximite in ChoixSousDomaineSciences.get_names():
            self.commission_proximite = ChoixSousDomaineSciences[commission_proximite]

    def _completer_financement(
        self,
        type: Optional[str],
        type_contrat_travail: Optional[str],
        eft: Optional[int],
        bourse_recherche: Optional[BourseIdentity],
        autre_bourse_recherche: Optional[str],
        bourse_date_debut: Optional[datetime.date],
        bourse_date_fin: Optional[datetime.date],
        bourse_preuve: List[str],
        duree_prevue: Optional[int],
        temps_consacre: Optional[int],
        est_lie_fnrs_fria_fresh_csc: Optional[bool],
        commentaire: Optional[str],
    ):
        if type:
            self.financement = Financement(
                type=ChoixTypeFinancement[type],
                type_contrat_travail=type_contrat_travail or '',
                eft=eft,
                bourse_recherche=bourse_recherche,
                autre_bourse_recherche=autre_bourse_recherche or '',
                bourse_date_debut=bourse_date_debut,
                bourse_date_fin=bourse_date_fin,
                bourse_preuve=bourse_preuve or [],
                duree_prevue=duree_prevue,
                temps_consacre=temps_consacre,
                est_lie_fnrs_fria_fresh_csc=est_lie_fnrs_fria_fresh_csc,
                commentaire=commentaire,
            )
        else:
            self.financement = financement_non_rempli

    def _completer_projet(
        self,
        titre: Optional[str],
        resume: Optional[str],
        langue_redaction_these: str,
        institut_these: Optional[str],
        lieu_these: Optional[str],
        deja_commence: Optional[bool] = None,
        deja_commence_institution: Optional[str] = '',
        date_debut: Optional[datetime.date] = None,
        documents: List[str] = None,
        graphe_gantt: List[str] = None,
        proposition_programme_doctoral: List[str] = None,
        projet_formation_complementaire: List[str] = None,
        lettres_recommandation: List[str] = None,
    ):
        self.projet = DetailProjet(
            titre=titre or '',
            resume=resume or '',
            langue_redaction_these=langue_redaction_these,
            institut_these=InstitutIdentity(uuid.UUID(institut_these)) if institut_these else None,
            lieu_these=lieu_these or '',
            documents=documents or [],
            graphe_gantt=graphe_gantt or [],
            proposition_programme_doctoral=proposition_programme_doctoral or [],
            projet_formation_complementaire=projet_formation_complementaire or [],
            lettres_recommandation=lettres_recommandation or [],
            deja_commence=deja_commence,
            deja_commence_institution=deja_commence_institution,
            date_debut=date_debut,
        )

    def _completer_experience_precedente(
        self,
        doctorat_deja_realise: str,
        institution: Optional[str],
        domaine_these: Optional[str],
        date_soutenance: Optional[datetime.date],
        raison_non_soutenue: Optional[str],
    ):
        if doctorat_deja_realise == ChoixDoctoratDejaRealise.NO.name:
            self.experience_precedente_recherche = aucune_experience_precedente_recherche
        else:
            self.experience_precedente_recherche = ExperiencePrecedenteRecherche(
                doctorat_deja_realise=ChoixDoctoratDejaRealise[doctorat_deja_realise],
                institution=institution or '',
                domaine_these=domaine_these or '',
                date_soutenance=date_soutenance,
                raison_non_soutenue=raison_non_soutenue or '',
            )

    def completer_curriculum(
        self,
        curriculum: List[str],
        reponses_questions_specifiques: Dict,
        auteur_modification: str,
    ):
        self.curriculum = curriculum
        self.reponses_questions_specifiques = reponses_questions_specifiques
        self.auteur_derniere_modification = auteur_modification

    def completer_comptabilite(
        self,
        auteur_modification: str,
        attestation_absence_dette_etablissement: List[str],
        type_situation_assimilation: Optional[str],
        sous_type_situation_assimilation_1: Optional[str],
        carte_resident_longue_duree: List[str],
        carte_cire_sejour_illimite_etranger: List[str],
        carte_sejour_membre_ue: List[str],
        carte_sejour_permanent_membre_ue: List[str],
        sous_type_situation_assimilation_2: Optional[str],
        carte_a_b_refugie: List[str],
        annexe_25_26_refugies_apatrides: List[str],
        attestation_immatriculation: List[str],
        preuve_statut_apatride: List[str],
        carte_a_b: List[str],
        decision_protection_subsidiaire: List[str],
        decision_protection_temporaire: List[str],
        carte_a: List[str],
        sous_type_situation_assimilation_3: Optional[str],
        titre_sejour_3_mois_professionel: List[str],
        fiches_remuneration: List[str],
        titre_sejour_3_mois_remplacement: List[str],
        preuve_allocations_chomage_pension_indemnite: List[str],
        attestation_cpas: List[str],
        relation_parente: Optional[str],
        sous_type_situation_assimilation_5: Optional[str],
        composition_menage_acte_naissance: List[str],
        acte_tutelle: List[str],
        composition_menage_acte_mariage: List[str],
        attestation_cohabitation_legale: List[str],
        carte_identite_parent: List[str],
        titre_sejour_longue_duree_parent: List[str],
        annexe_25_26_protection_parent: List[str],
        titre_sejour_3_mois_parent: List[str],
        fiches_remuneration_parent: List[str],
        attestation_cpas_parent: List[str],
        sous_type_situation_assimilation_6: Optional[str],
        decision_bourse_cfwb: List[str],
        attestation_boursier: List[str],
        titre_identite_sejour_longue_duree_ue: List[str],
        titre_sejour_belgique: List[str],
        etudiant_solidaire: Optional[bool],
        type_numero_compte: Optional[str],
        numero_compte_iban: Optional[str],
        iban_valide: Optional[bool],
        numero_compte_autre_format: Optional[str],
        code_bic_swift_banque: Optional[str],
        prenom_titulaire_compte: Optional[str],
        nom_titulaire_compte: Optional[str],
    ):
        self.auteur_derniere_modification = auteur_modification
        self.comptabilite = Comptabilite(
            attestation_absence_dette_etablissement=attestation_absence_dette_etablissement,
            type_situation_assimilation=TypeSituationAssimilation[type_situation_assimilation]
            if type_situation_assimilation
            else None,
            sous_type_situation_assimilation_1=ChoixAssimilation1[sous_type_situation_assimilation_1]
            if sous_type_situation_assimilation_1
            else None,
            carte_resident_longue_duree=carte_resident_longue_duree,
            carte_cire_sejour_illimite_etranger=carte_cire_sejour_illimite_etranger,
            carte_sejour_membre_ue=carte_sejour_membre_ue,
            carte_sejour_permanent_membre_ue=carte_sejour_permanent_membre_ue,
            sous_type_situation_assimilation_2=ChoixAssimilation2[sous_type_situation_assimilation_2]
            if sous_type_situation_assimilation_2
            else None,
            carte_a_b_refugie=carte_a_b_refugie,
            annexe_25_26_refugies_apatrides=annexe_25_26_refugies_apatrides,
            attestation_immatriculation=attestation_immatriculation,
            preuve_statut_apatride=preuve_statut_apatride,
            carte_a_b=carte_a_b,
            decision_protection_subsidiaire=decision_protection_subsidiaire,
            decision_protection_temporaire=decision_protection_temporaire,
            carte_a=carte_a,
            sous_type_situation_assimilation_3=ChoixAssimilation3[sous_type_situation_assimilation_3]
            if sous_type_situation_assimilation_3
            else None,
            titre_sejour_3_mois_professionel=titre_sejour_3_mois_professionel,
            fiches_remuneration=fiches_remuneration,
            titre_sejour_3_mois_remplacement=titre_sejour_3_mois_remplacement,
            preuve_allocations_chomage_pension_indemnite=preuve_allocations_chomage_pension_indemnite,
            attestation_cpas=attestation_cpas,
            relation_parente=LienParente[relation_parente] if relation_parente else None,
            sous_type_situation_assimilation_5=ChoixAssimilation5[sous_type_situation_assimilation_5]
            if sous_type_situation_assimilation_5
            else None,
            composition_menage_acte_naissance=composition_menage_acte_naissance,
            acte_tutelle=acte_tutelle,
            composition_menage_acte_mariage=composition_menage_acte_mariage,
            attestation_cohabitation_legale=attestation_cohabitation_legale,
            carte_identite_parent=carte_identite_parent,
            titre_sejour_longue_duree_parent=titre_sejour_longue_duree_parent,
            annexe_25_26_refugies_apatrides_decision_protection_parent=annexe_25_26_protection_parent,
            titre_sejour_3_mois_parent=titre_sejour_3_mois_parent,
            fiches_remuneration_parent=fiches_remuneration_parent,
            attestation_cpas_parent=attestation_cpas_parent,
            sous_type_situation_assimilation_6=ChoixAssimilation6[sous_type_situation_assimilation_6]
            if sous_type_situation_assimilation_6
            else None,
            decision_bourse_cfwb=decision_bourse_cfwb,
            attestation_boursier=attestation_boursier,
            titre_identite_sejour_longue_duree_ue=titre_identite_sejour_longue_duree_ue,
            titre_sejour_belgique=titre_sejour_belgique,
            etudiant_solidaire=etudiant_solidaire,
            type_numero_compte=ChoixTypeCompteBancaire[type_numero_compte] if type_numero_compte else None,
            numero_compte_iban=numero_compte_iban,
            iban_valide=iban_valide,
            numero_compte_autre_format=numero_compte_autre_format,
            code_bic_swift_banque=code_bic_swift_banque,
            prenom_titulaire_compte=prenom_titulaire_compte,
            nom_titulaire_compte=nom_titulaire_compte,
        )

    def reinitialiser_archive(self):
        self.fiche_archive_signatures_envoyees = []

    def verrouiller_proposition_pour_signature(self):
        self.statut = ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE

    def deverrouiller_projet_doctoral(self):
        self.statut = ChoixStatutPropositionDoctorale.EN_BROUILLON

    def verifier_projet_doctoral(self):
        """Vérification de la validité du projet doctoral avant demande des signatures"""
        PropositionProjetDoctoralValidatorList(
            self.type_admission,
            self.projet,
            self.financement,
            self.experience_precedente_recherche,
        ).validate()

    def finaliser(
        self,
        formation_id: FormationIdentity,
        type_demande: 'TypeDemande',
        pool: 'AcademicCalendarTypes',
        elements_confirmation: Dict[str, str],
    ):
        self.statut = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC
        self.type_demande = type_demande
        self.annee_calculee = formation_id.annee
        self.formation_id = formation_id
        self.pot_calcule = pool
        self.elements_confirmation = elements_confirmation

    def supprimer(self):
        self.statut = ChoixStatutPropositionDoctorale.ANNULEE

    def valider_inscription(self):
        self.statut = ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE

    def definir_institut_these(self, institut_these: Optional[str]):
        if institut_these:
            self.projet = attr.evolve(
                self.projet,
                institut_these=InstitutIdentity(uuid.UUID(institut_these)),
            )

    def modifier_type_admission(
        self,
        doctorat: Doctorat,
        type_admission: str,
        justification: Optional[str],
        reponses_questions_specifiques: Dict,
        commission_proximite: Optional[str],
    ):
        ModifierTypeAdmissionValidatorList(
            type_admission=type_admission,
            justification=justification,
            commission_proximite=commission_proximite,
            doctorat=doctorat,
        ).validate()
        self._definir_commission(commission_proximite)
        self.formation_id = doctorat.entity_id
        self.type_admission = ChoixTypeAdmission[type_admission]
        self.justification = justification or ''
        self.reponses_questions_specifiques = reponses_questions_specifiques
        self.auteur_derniere_modification = self.matricule_candidat

    def modifier_choix_formation_gestionnaire(
        self,
        doctorat: Doctorat,
        type_admission: str,
        justification: Optional[str],
        reponses_questions_specifiques: Dict,
        commission_proximite: Optional[str],
        auteur: str,
    ):
        ModifierTypeAdmissionValidatorList(
            type_admission=type_admission,
            justification=justification,
            commission_proximite=commission_proximite,
            doctorat=doctorat,
        ).validate()

        self._definir_commission(commission_proximite)
        self.type_admission = ChoixTypeAdmission[type_admission]
        self.justification = justification or ''
        self.reponses_questions_specifiques = reponses_questions_specifiques
        self.auteur_derniere_modification = auteur

    def reclamer_documents(self, auteur_modification: str, type_gestionnaire: str):
        self.statut = {
            TypeGestionnaire.FAC.name: ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC,
            TypeGestionnaire.SIC.name: ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_SIC,
        }[type_gestionnaire]
        self.auteur_derniere_modification = auteur_modification

    def annuler_reclamation_documents(self, auteur_modification: str, type_gestionnaire: str):
        self.statut = {
            TypeGestionnaire.FAC.name: ChoixStatutPropositionDoctorale.TRAITEMENT_FAC,
            TypeGestionnaire.SIC.name: ChoixStatutPropositionDoctorale.CONFIRMEE,
        }[type_gestionnaire]
        self.auteur_derniere_modification = auteur_modification

    def completer_documents_par_candidat(self):
        self.statut = {
            ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_SIC: ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC,
            ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC: ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC,
        }.get(self.statut)
        self.auteur_derniere_modification = self.matricule_candidat

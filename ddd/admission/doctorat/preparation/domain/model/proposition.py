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
import datetime
import uuid
from decimal import Decimal
from typing import Dict, List, Optional, Union

import attr
from django.utils.translation import gettext_noop as __

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
from admission.ddd.admission.doctorat.preparation.domain.model._institut import (
    InstitutIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import (
    DoctoratFormation,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixDoctoratDejaRealise,
    ChoixSousDomaineSciences,
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
    ChoixTypeFinancement,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    BesoinDeDerogation,
    ChoixStatutChecklist,
    DecisionCDDEnum,
    DerogationFinancement,
    DispenseOuDroitsMajores,
    DroitsInscriptionMontant,
    MobiliteNombreDeMois,
    OngletsChecklist,
)
from admission.ddd.admission.doctorat.preparation.domain.model.statut_checklist import (
    StatutChecklist,
    StatutsChecklistDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    CurriculumNonCompletePourAcceptationException,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.validator_by_business_action import (
    ApprouverAdmissionParSicValidatorList,
    ApprouverInscriptionParSicValidatorList,
    ApprouverParCDDValidatorList,
    ApprouverParSicAValiderValidatorList,
    CompletionPropositionValidatorList,
    GestionnairePeutSoumettreAuSicLorsDeLaDecisionCDDValidatorList,
    ModifierStatutChecklistParcoursAnterieurValidatorList,
    ModifierTypeAdmissionValidatorList,
    PropositionProjetDoctoralValidatorList,
    RedonnerLaMainAuCandidatValidatorList,
    DemanderCandidatModificationCaValidatorList,
    RefuserParCDDValidatorList,
    SICPeutSoumettreAuCDDLorsDeLaDecisionCDDValidatorList,
    SoumettreCAValidatorList,
    SpecifierConditionAccesParcoursAnterieurValidatorList,
    SpecifierInformationsApprobationInscriptionValidatorList,
    SpecifierNouvellesInformationsDecisionCDDValidatorList,
)
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import (
    CurriculumAdmissionDTO,
)
from admission.ddd.admission.domain.model._profil_candidat import ProfilCandidat
from admission.ddd.admission.domain.model.complement_formation import (
    ComplementFormationIdentity,
)
from admission.ddd.admission.domain.model.enums.equivalence import (
    EtatEquivalenceTitreAcces,
    StatutEquivalenceTitreAcces,
    TypeEquivalenceTitreAcces,
)
from admission.ddd.admission.domain.model.enums.type_gestionnaire import (
    TypeGestionnaire,
)
from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.domain.model.motif_refus import MotifRefusIdentity
from admission.ddd.admission.domain.model.question_specifique import QuestionSpecifique
from admission.ddd.admission.domain.model.titre_acces_selectionnable import (
    TitreAccesSelectionnable,
)
from admission.ddd.admission.domain.repository.i_titre_acces_selectionnable import (
    ITitreAccesSelectionnableRepository,
)
from admission.ddd.admission.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)
from admission.ddd.admission.domain.service.i_question_specifique import (
    ISuperQuestionSpecifiqueTranslator,
)
from admission.ddd.admission.domain.service.profil_candidat import (
    ProfilCandidat as ProfilCandidatService,
)
from admission.ddd.admission.domain.validator.exceptions import (
    ExperienceNonTrouveeException,
)
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
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
from admission.ddd.admission.utils import initialiser_checklist_experience
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from ddd.logic.financabilite.domain.model.enums.etat import EtatFinancabilite
from ddd.logic.financabilite.domain.model.enums.situation import (
    SITUATION_FINANCABILITE_PAR_ETAT,
    SituationFinancabilite,
)
from ddd.logic.reference.domain.model.bourse import BourseIdentity
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import (
    IAcademicYearRepository,
)
from ddd.logic.shared_kernel.profil.domain.service.parcours_interne import (
    IExperienceParcoursInterneTranslator,
)
from epc.models.enums.condition_acces import ConditionAcces
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
    soumise_le: Optional[datetime.datetime] = None

    profil_soumis_candidat: ProfilCandidat = None

    fiche_archive_signatures_envoyees: List[str] = attr.Factory(list)
    comptabilite: 'Comptabilite' = comptabilite_non_remplie
    reponses_questions_specifiques: Dict = attr.Factory(dict)
    curriculum: List[str] = attr.Factory(list)

    elements_confirmation: Dict[str, str] = attr.Factory(dict)
    documents_demandes: Dict = attr.Factory(dict)

    # Checklist
    checklist_initiale: Optional[StatutsChecklistDoctorale] = None
    checklist_actuelle: Optional[StatutsChecklistDoctorale] = None

    # Financabilite
    financabilite_regle_calcule: Optional[EtatFinancabilite] = None
    financabilite_regle_calcule_situation: Optional[SituationFinancabilite] = None
    financabilite_regle_calcule_le: Optional[datetime.datetime] = None
    financabilite_regle: Optional[SituationFinancabilite] = None
    financabilite_etabli_par: str = ''
    financabilite_etabli_le: Optional[datetime.datetime] = None

    financabilite_derogation_statut: Optional[DerogationFinancement] = None
    financabilite_derogation_premiere_notification_le: Optional[datetime.datetime] = None
    financabilite_derogation_premiere_notification_par: str = ''
    financabilite_derogation_derniere_notification_le: Optional[datetime.datetime] = None
    financabilite_derogation_derniere_notification_par: str = ''

    # Décision facultaire & sic
    certificat_approbation_cdd: List[str] = attr.Factory(list)
    certificat_approbation_sic: List[str] = attr.Factory(list)
    certificat_approbation_sic_annexe: List[str] = attr.Factory(list)

    motifs_refus: List[MotifRefusIdentity] = attr.Factory(list)
    autres_motifs_refus: List[str] = attr.Factory(list)

    complements_formation: Optional[List[ComplementFormationIdentity]] = attr.Factory(list)
    avec_complements_formation: Optional[bool] = None
    commentaire_complements_formation: str = ''
    nombre_annees_prevoir_programme: Optional[int] = None
    nom_personne_contact_programme_annuel_annuel: str = ''
    email_personne_contact_programme_annuel_annuel: str = ''
    commentaire_programme_conjoint: str = ''
    besoin_de_derogation: Optional['BesoinDeDerogation'] = None

    droits_inscription_montant: Optional['DroitsInscriptionMontant'] = None
    droits_inscription_montant_autre: Optional[Decimal] = None
    dispense_ou_droits_majores: Optional['DispenseOuDroitsMajores'] = None
    est_mobilite: Optional[bool] = None
    nombre_de_mois_de_mobilite: Optional['MobiliteNombreDeMois'] = None
    doit_se_presenter_en_sic: Optional[bool] = None
    communication_au_candidat: str = ''
    doit_fournir_visa_etudes: Optional[bool] = None
    visa_etudes_d: List[str] = attr.Factory(list)
    certificat_autorisation_signe: List[str] = attr.Factory(list)

    condition_acces: Optional[ConditionAcces] = None
    millesime_condition_acces: Optional[int] = None

    type_equivalence_titre_acces: Optional[TypeEquivalenceTitreAcces] = None
    statut_equivalence_titre_acces: Optional[StatutEquivalenceTitreAcces] = None
    information_a_propos_de_la_restriction: str = ''
    etat_equivalence_titre_acces: Optional[EtatEquivalenceTitreAcces] = None
    date_prise_effet_equivalence_titre_acces: Optional[datetime.date] = None

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
        doctorat: DoctoratFormation,
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
            type_situation_assimilation=(
                TypeSituationAssimilation[type_situation_assimilation] if type_situation_assimilation else None
            ),
            sous_type_situation_assimilation_1=(
                ChoixAssimilation1[sous_type_situation_assimilation_1] if sous_type_situation_assimilation_1 else None
            ),
            carte_resident_longue_duree=carte_resident_longue_duree,
            carte_cire_sejour_illimite_etranger=carte_cire_sejour_illimite_etranger,
            carte_sejour_membre_ue=carte_sejour_membre_ue,
            carte_sejour_permanent_membre_ue=carte_sejour_permanent_membre_ue,
            sous_type_situation_assimilation_2=(
                ChoixAssimilation2[sous_type_situation_assimilation_2] if sous_type_situation_assimilation_2 else None
            ),
            carte_a_b_refugie=carte_a_b_refugie,
            annexe_25_26_refugies_apatrides=annexe_25_26_refugies_apatrides,
            attestation_immatriculation=attestation_immatriculation,
            preuve_statut_apatride=preuve_statut_apatride,
            carte_a_b=carte_a_b,
            decision_protection_subsidiaire=decision_protection_subsidiaire,
            decision_protection_temporaire=decision_protection_temporaire,
            carte_a=carte_a,
            sous_type_situation_assimilation_3=(
                ChoixAssimilation3[sous_type_situation_assimilation_3] if sous_type_situation_assimilation_3 else None
            ),
            titre_sejour_3_mois_professionel=titre_sejour_3_mois_professionel,
            fiches_remuneration=fiches_remuneration,
            titre_sejour_3_mois_remplacement=titre_sejour_3_mois_remplacement,
            preuve_allocations_chomage_pension_indemnite=preuve_allocations_chomage_pension_indemnite,
            attestation_cpas=attestation_cpas,
            relation_parente=LienParente[relation_parente] if relation_parente else None,
            sous_type_situation_assimilation_5=(
                ChoixAssimilation5[sous_type_situation_assimilation_5] if sous_type_situation_assimilation_5 else None
            ),
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
            sous_type_situation_assimilation_6=(
                ChoixAssimilation6[sous_type_situation_assimilation_6] if sous_type_situation_assimilation_6 else None
            ),
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
        if self.statut == ChoixStatutPropositionDoctorale.CA_A_COMPLETER:
            self.statut = ChoixStatutPropositionDoctorale.CA_EN_ATTENTE_DE_SIGNATURE
        else:
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
        self.auteur_derniere_modification = self.matricule_candidat

    def supprimer(self):
        self.statut = ChoixStatutPropositionDoctorale.ANNULEE
        self.auteur_derniere_modification = self.matricule_candidat

    def valider_inscription(self):
        self.statut = ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE

    def redonner_la_main_au_candidat(self):
        RedonnerLaMainAuCandidatValidatorList(
            statut=self.statut,
        ).validate()
        self.statut = ChoixStatutPropositionDoctorale.EN_BROUILLON

    def definir_institut_these(self, institut_these: Optional[str]):
        if institut_these:
            self.projet = attr.evolve(
                self.projet,
                institut_these=InstitutIdentity(uuid.UUID(institut_these)),
            )

    def modifier_type_admission(
        self,
        doctorat: DoctoratFormation,
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
        doctorat: DoctoratFormation,
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

    def specifier_statut_checklist_parcours_anterieur(
        self,
        statut_checklist_cible: str,
        titres_acces_selectionnes: List[TitreAccesSelectionnable],
        auteur_modification: str,
    ):
        ModifierStatutChecklistParcoursAnterieurValidatorList(
            statut=ChoixStatutChecklist[statut_checklist_cible],
            titres_acces_selectionnes=titres_acces_selectionnes,
            condition_acces=self.condition_acces,
            millesime_condition_acces=self.millesime_condition_acces,
        ).validate()

        self.checklist_actuelle.parcours_anterieur.statut = ChoixStatutChecklist[statut_checklist_cible]
        self.auteur_derniere_modification = auteur_modification

    def specifier_statut_checklist_experience_parcours_anterieur(
        self,
        statut_checklist_cible: str,
        statut_checklist_authentification: Optional[bool],
        uuid_experience: str,
        auteur_modification: str,
    ):
        try:
            experience = self.checklist_actuelle.recuperer_enfant(
                OngletsChecklist.parcours_anterieur.name,
                uuid_experience,
            )
        except StopIteration:
            # Si l'expérience n'existe pas dans la checklist, on l'initialise
            experience = initialiser_checklist_experience(experience_uuid=uuid_experience)
            self.checklist_actuelle.parcours_anterieur.enfants.append(experience)

        experience.statut = ChoixStatutChecklist[statut_checklist_cible]

        if statut_checklist_authentification is None:
            experience.extra.pop('authentification', None)
        else:
            experience.extra['authentification'] = '1' if statut_checklist_authentification else '0'

        self.auteur_derniere_modification = auteur_modification

    def specifier_authentification_experience_parcours_anterieur(
        self,
        uuid_experience: str,
        auteur_modification: str,
        etat_authentification: str,
    ):
        try:
            experience = self.checklist_actuelle.recuperer_enfant('parcours_anterieur', uuid_experience)
        except StopIteration:
            raise ExperienceNonTrouveeException

        experience.extra['etat_authentification'] = etat_authentification
        self.auteur_derniere_modification = auteur_modification

    def specifier_condition_acces(
        self,
        auteur_modification: str,
        condition_acces: str,
        millesime_condition_acces: Optional[int],
        avec_complements_formation: Optional[bool],
        titre_acces_selectionnable_repository: 'ITitreAccesSelectionnableRepository',
        experience_parcours_interne_translator: IExperienceParcoursInterneTranslator,
    ):
        nouveau_millesime_condition_acces = millesime_condition_acces
        nouvelle_condition_acces = getattr(ConditionAcces, condition_acces, None)

        # Si la condition d'accès a changé
        if nouvelle_condition_acces and nouvelle_condition_acces != self.condition_acces:
            # Si un seul titre d'accès a été sélectionné,  le millésime correspond à l'année de ce titre
            titres_selectionnes = titre_acces_selectionnable_repository.search_by_proposition(
                proposition_identity=self.entity_id,
                experience_parcours_interne_translator=experience_parcours_interne_translator,
                seulement_selectionnes=True,
            )

            if len(titres_selectionnes) == 1:
                nouveau_millesime_condition_acces = titres_selectionnes[0].annee

            # Si la condition d'accès est "SNU Type Court", des compléments de formation sont demandés par défaut
            if nouvelle_condition_acces == ConditionAcces.SNU_TYPE_COURT:
                avec_complements_formation = True

        SpecifierConditionAccesParcoursAnterieurValidatorList(
            avec_complements_formation=avec_complements_formation,
            complements_formation=self.complements_formation,
            commentaire_complements_formation=self.commentaire_complements_formation,
        ).validate()

        self.auteur_derniere_modification = auteur_modification
        self.condition_acces = nouvelle_condition_acces
        self.millesime_condition_acces = nouveau_millesime_condition_acces
        self.avec_complements_formation = avec_complements_formation

        if not avec_complements_formation:
            self.complements_formation = []
            self.commentaire_complements_formation = ''

    def specifier_equivalence_titre_acces(
        self,
        auteur_modification: str,
        type_equivalence_titre_acces: str,
        statut_equivalence_titre_acces: str,
        information_a_propos_de_la_restriction: str,
        etat_equivalence_titre_acces: str,
        date_prise_effet_equivalence_titre_acces: Optional[datetime.date],
    ):
        self.auteur_derniere_modification = auteur_modification
        self.type_equivalence_titre_acces = getattr(TypeEquivalenceTitreAcces, type_equivalence_titre_acces, None)
        self.statut_equivalence_titre_acces = getattr(StatutEquivalenceTitreAcces, statut_equivalence_titre_acces, None)
        self.information_a_propos_de_la_restriction = information_a_propos_de_la_restriction
        self.etat_equivalence_titre_acces = getattr(EtatEquivalenceTitreAcces, etat_equivalence_titre_acces, None)
        self.date_prise_effet_equivalence_titre_acces = date_prise_effet_equivalence_titre_acces

    def specifier_financabilite_resultat_calcul(
        self,
        financabilite_regle_calcule: EtatFinancabilite,
        financabilite_regle_calcule_situation: str,
        auteur_modification: Optional[str] = '',
    ):
        self.financabilite_regle_calcule = financabilite_regle_calcule
        self.financabilite_regle_calcule_situation = (
            SituationFinancabilite[financabilite_regle_calcule_situation]
            if financabilite_regle_calcule_situation
            else None
        )
        self.financabilite_regle_calcule_le = datetime.datetime.now()
        if auteur_modification:
            self.auteur_derniere_modification = auteur_modification

    def specifier_financabilite_regle(
        self,
        financabilite_regle: SituationFinancabilite,
        auteur_modification: str,
    ):
        self.financabilite_regle = financabilite_regle
        self.financabilite_etabli_par = auteur_modification
        self.financabilite_etabli_le = datetime.datetime.now()
        self.auteur_derniere_modification = auteur_modification

        if financabilite_regle in SITUATION_FINANCABILITE_PAR_ETAT[EtatFinancabilite.FINANCABLE]:
            self.checklist_actuelle.financabilite = StatutChecklist(
                statut=ChoixStatutChecklist.GEST_REUSSITE,
                libelle=__('Approval'),
                extra={'reussite': 'financable'},
            )
        elif financabilite_regle in SITUATION_FINANCABILITE_PAR_ETAT[EtatFinancabilite.NON_FINANCABLE]:
            self.checklist_actuelle.financabilite = StatutChecklist(
                statut=ChoixStatutChecklist.GEST_BLOCAGE,
                libelle=__('Not financeable'),
                extra={'to_be_completed': '0'},
            )

    def specifier_financabilite_non_concernee(
        self,
        auteur_modification: str,
    ):
        self.financabilite_regle = None
        self.financabilite_etabli_par = auteur_modification
        self.financabilite_etabli_le = datetime.datetime.now()
        self.auteur_derniere_modification = auteur_modification
        self.checklist_actuelle.financabilite = StatutChecklist(
            statut=ChoixStatutChecklist.INITIAL_NON_CONCERNE,
            libelle='',
        )

    def specifier_derogation_financabilite(
        self,
        statut: DerogationFinancement,
        refus_uuids_motifs: Optional[List[str]],
        refus_autres_motifs: Optional[List[str]],
        auteur_modification: str,
    ):
        self.financabilite_etabli_par = auteur_modification
        self.financabilite_etabli_le = datetime.datetime.now()
        self.auteur_derniere_modification = auteur_modification
        self.financabilite_derogation_statut = statut
        if statut == DerogationFinancement.REFUS_DE_DEROGATION_FACULTAIRE:
            self.motifs_refus = [MotifRefusIdentity(uuid=uuid_motif) for uuid_motif in refus_uuids_motifs]
            self.autres_motifs_refus = refus_autres_motifs

    def notifier_candidat_derogation_financabilite(self, gestionnaire: str):
        self.financabilite_derogation_statut = DerogationFinancement.CANDIDAT_NOTIFIE
        if not self.financabilite_derogation_premiere_notification_le:
            self.financabilite_derogation_premiere_notification_le = datetime.datetime.now()
            self.financabilite_derogation_premiere_notification_par = gestionnaire
        else:
            self.financabilite_derogation_derniere_notification_le = datetime.datetime.now()
            self.financabilite_derogation_derniere_notification_par = gestionnaire

    def specifier_besoin_de_derogation(self, besoin_de_derogation: BesoinDeDerogation, auteur_modification: str):
        self.besoin_de_derogation = besoin_de_derogation
        self.auteur_derniere_modification = auteur_modification

    def _specifier_informations_de_base_acceptation_par_sic(
        self,
        auteur_modification: str,
        avec_complements_formation: Optional[bool],
        uuids_complements_formation: Optional[List[str]],
        commentaire_complements_formation: str,
        nombre_annees_prevoir_programme: Optional[int],
        nom_personne_contact_programme_annuel: str,
        email_personne_contact_programme_annuel: str,
    ):
        """Spécifier les informations d'acceptation par SIC communes entre les admissions et les inscriptions."""
        self.auteur_derniere_modification = auteur_modification

        self.avec_complements_formation = avec_complements_formation
        self.complements_formation = (
            [ComplementFormationIdentity(uuid=uuid_complement) for uuid_complement in uuids_complements_formation]
            if uuids_complements_formation
            else []
        )
        self.commentaire_complements_formation = commentaire_complements_formation

        self.nombre_annees_prevoir_programme = nombre_annees_prevoir_programme

        self.nom_personne_contact_programme_annuel_annuel = nom_personne_contact_programme_annuel
        self.email_personne_contact_programme_annuel_annuel = email_personne_contact_programme_annuel

    def specifier_informations_acceptation_par_sic(
        self,
        auteur_modification: str,
        documents_dto: List[EmplacementDocumentDTO],
        avec_complements_formation: Optional[bool],
        uuids_complements_formation: Optional[List[str]],
        commentaire_complements_formation: str,
        nombre_annees_prevoir_programme: Optional[int],
        nom_personne_contact_programme_annuel: str,
        email_personne_contact_programme_annuel: str,
        droits_inscription_montant: str,
        droits_inscription_montant_autre: Optional[float],
        dispense_ou_droits_majores: str,
        est_mobilite: Optional[bool],
        nombre_de_mois_de_mobilite: str,
        doit_se_presenter_en_sic: Optional[bool],
        communication_au_candidat: str,
        doit_fournir_visa_etudes: Optional[bool],
    ):
        ApprouverParSicAValiderValidatorList(
            statut=self.statut,
            statut_checklist_parcours_anterieur=self.checklist_actuelle.parcours_anterieur,
            documents_dto=documents_dto,
            type_demande=self.type_demande,
        ).validate()
        self.statut = ChoixStatutPropositionDoctorale.ATTENTE_VALIDATION_DIRECTION
        self.checklist_actuelle.decision_sic = StatutChecklist(
            statut=ChoixStatutChecklist.GEST_EN_COURS,
            libelle=__('Approval'),
            extra={'en_cours': "approval"},
        )

        self._specifier_informations_de_base_acceptation_par_sic(
            auteur_modification=auteur_modification,
            avec_complements_formation=avec_complements_formation,
            uuids_complements_formation=uuids_complements_formation,
            commentaire_complements_formation=commentaire_complements_formation,
            nombre_annees_prevoir_programme=nombre_annees_prevoir_programme,
            nom_personne_contact_programme_annuel=nom_personne_contact_programme_annuel,
            email_personne_contact_programme_annuel=email_personne_contact_programme_annuel,
        )

        self.droits_inscription_montant = (
            DroitsInscriptionMontant[droits_inscription_montant] if droits_inscription_montant else None
        )
        self.droits_inscription_montant_autre = droits_inscription_montant_autre
        self.dispense_ou_droits_majores = (
            DispenseOuDroitsMajores[dispense_ou_droits_majores] if dispense_ou_droits_majores else None
        )
        self.est_mobilite = est_mobilite
        self.nombre_de_mois_de_mobilite = (
            MobiliteNombreDeMois[nombre_de_mois_de_mobilite] if nombre_de_mois_de_mobilite else None
        )
        self.doit_se_presenter_en_sic = doit_se_presenter_en_sic
        self.communication_au_candidat = communication_au_candidat
        self.doit_fournir_visa_etudes = doit_fournir_visa_etudes

    def specifier_informations_acceptation_inscription_par_sic(
        self,
        auteur_modification: str,
        avec_complements_formation: Optional[bool],
        uuids_complements_formation: Optional[List[str]],
        commentaire_complements_formation: str,
        nombre_annees_prevoir_programme: Optional[int],
        nom_personne_contact_programme_annuel: str,
        email_personne_contact_programme_annuel: str,
    ):
        SpecifierInformationsApprobationInscriptionValidatorList(
            statut=self.statut,
        ).validate()

        self._specifier_informations_de_base_acceptation_par_sic(
            auteur_modification=auteur_modification,
            avec_complements_formation=avec_complements_formation,
            uuids_complements_formation=uuids_complements_formation,
            commentaire_complements_formation=commentaire_complements_formation,
            nombre_annees_prevoir_programme=nombre_annees_prevoir_programme,
            nom_personne_contact_programme_annuel=nom_personne_contact_programme_annuel,
            email_personne_contact_programme_annuel=email_personne_contact_programme_annuel,
        )

    def approuver_par_sic(
        self,
        auteur_modification: str,
        documents_dto: List[EmplacementDocumentDTO],
        curriculum_dto: CurriculumAdmissionDTO,
        academic_year_repository: IAcademicYearRepository,
        profil_candidat_translator: IProfilCandidatTranslator,
        experience_parcours_interne_translator: IExperienceParcoursInterneTranslator,
    ):
        if self.type_demande == TypeDemande.INSCRIPTION:
            ApprouverInscriptionParSicValidatorList(
                statut=self.statut,
                checklist=self.checklist_actuelle,
                besoin_de_derogation=self.besoin_de_derogation,
                documents_dto=documents_dto,
            ).validate()

        else:
            ApprouverAdmissionParSicValidatorList(
                statut=self.statut,
                avec_complements_formation=self.avec_complements_formation,
                complements_formation=self.complements_formation,
                nombre_annees_prevoir_programme=self.nombre_annees_prevoir_programme,
                checklist=self.checklist_actuelle,
                documents_dto=documents_dto,
            ).validate()

        try:
            ProfilCandidatService.verifier_curriculum_formation_doctorale_apres_soumission(
                proposition=self,
                curriculum_dto=curriculum_dto,
                academic_year_repository=academic_year_repository,
                profil_candidat_translator=profil_candidat_translator,
                experience_parcours_interne_translator=experience_parcours_interne_translator,
            )
        except MultipleBusinessExceptions:
            raise MultipleBusinessExceptions(exceptions=[CurriculumNonCompletePourAcceptationException()])

        ProfilCandidatService.verifier_quarantaine(
            proposition=self,
            profil_candidat_translator=profil_candidat_translator,
        )

        self.checklist_actuelle.decision_sic = StatutChecklist(
            statut=ChoixStatutChecklist.GEST_REUSSITE,
            libelle=__('Approval'),
        )
        self.statut = ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE
        self.auteur_derniere_modification = auteur_modification

    def soumettre_au_cdd_lors_de_la_decision_cdd(self, auteur_modification: str):
        SICPeutSoumettreAuCDDLorsDeLaDecisionCDDValidatorList(
            statut=self.statut,
        ).validate()
        self.auteur_derniere_modification = auteur_modification
        self.statut = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC

    def specifier_acceptation_par_cdd(self):
        self.checklist_actuelle.decision_cdd = StatutChecklist(
            statut=ChoixStatutChecklist.GEST_REUSSITE,
            libelle=__('Approval'),
        )

    def specifier_refus_par_cdd(self):
        self.checklist_actuelle.decision_cdd = StatutChecklist(
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            libelle=__('Refusal'),
            extra={
                'decision': DecisionCDDEnum.EN_DECISION.name,
            },
        )

    def approuver_par_cdd(self, auteur_modification: str, titres_selectionnes: List[TitreAccesSelectionnable]):
        ApprouverParCDDValidatorList(
            statut=self.statut,
            nombre_annees_prevoir_programme=self.nombre_annees_prevoir_programme,
            titres_selectionnes=titres_selectionnes,
        ).validate()

        self.specifier_acceptation_par_cdd()
        self.statut = ChoixStatutPropositionDoctorale.RETOUR_DE_FAC
        self.auteur_derniere_modification = auteur_modification

    def refuser_par_cdd(self, auteur_modification: str):
        RefuserParCDDValidatorList(
            statut=self.statut,
        ).validate()

        self.specifier_refus_par_cdd()
        self.statut = ChoixStatutPropositionDoctorale.INSCRIPTION_REFUSEE
        self.auteur_derniere_modification = auteur_modification

    def soumettre_au_sic_lors_de_la_decision_cdd(self, auteur_modification: str):
        GestionnairePeutSoumettreAuSicLorsDeLaDecisionCDDValidatorList(statut=self.statut).validate()
        self.statut = ChoixStatutPropositionDoctorale.RETOUR_DE_FAC
        self.auteur_derniere_modification = auteur_modification

    def specifier_informations_acceptation_par_cdd(
        self,
        auteur_modification: str,
        avec_complements_formation: Optional[bool],
        uuids_complements_formation: Optional[List[str]],
        commentaire_complements_formation: str,
        nombre_annees_prevoir_programme: Optional[int],
        nom_personne_contact_programme_annuel: str,
        email_personne_contact_programme_annuel: str,
        commentaire_programme_conjoint: str,
    ):
        SpecifierNouvellesInformationsDecisionCDDValidatorList(
            statut=self.statut,
        ).validate()
        self.auteur_derniere_modification = auteur_modification

        self.avec_complements_formation = avec_complements_formation
        self.complements_formation = (
            [ComplementFormationIdentity(uuid=uuid_complement) for uuid_complement in uuids_complements_formation]
            if uuids_complements_formation
            else []
        )
        self.commentaire_complements_formation = commentaire_complements_formation

        self.nombre_annees_prevoir_programme = nombre_annees_prevoir_programme

        self.nom_personne_contact_programme_annuel_annuel = nom_personne_contact_programme_annuel
        self.email_personne_contact_programme_annuel_annuel = email_personne_contact_programme_annuel

        self.commentaire_programme_conjoint = commentaire_programme_conjoint

    def modifier_checklist_choix_formation(
        self,
        auteur_modification: str,
        type_demande: 'TypeDemande',
        formation_id: FormationIdentity,
    ):
        self.auteur_derniere_modification = auteur_modification
        self.type_demande = type_demande
        self.formation_id = formation_id
        self.annee_calculee = formation_id.annee

    def nettoyer_reponses_questions_specifiques(self, questions_specifiques: List[QuestionSpecifique]):
        self.reponses_questions_specifiques = ISuperQuestionSpecifiqueTranslator.clean_specific_question_answers(
            questions_specifiques,
            self.reponses_questions_specifiques,
        )

    def demander_candidat_modification_ca(self):
        DemanderCandidatModificationCaValidatorList(
            statut=self.statut,
        ).validate()
        self.statut = ChoixStatutPropositionDoctorale.CA_A_COMPLETER

    def soumettre_ca(self):
        SoumettreCAValidatorList(
            statut=self.statut,
        ).validate()
        self.statut = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC

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
from decimal import Decimal
from typing import Dict, List, Optional

import attr
from django.utils.timezone import now
from django.utils.translation import gettext_noop as __

from admission.ddd.admission.doctorat.preparation.dtos.curriculum import (
    CurriculumAdmissionDTO,
)
from admission.ddd.admission.domain.model._profil_candidat import ProfilCandidat
from admission.ddd.admission.domain.model.complement_formation import (
    ComplementFormationIdentity,
)
from admission.ddd.admission.domain.model.condition_complementaire_approbation import (
    ConditionComplementaireApprobationIdentity,
    ConditionComplementaireLibreApprobation,
)
from admission.ddd.admission.domain.model.enums.equivalence import (
    EtatEquivalenceTitreAcces,
    StatutEquivalenceTitreAcces,
    TypeEquivalenceTitreAcces,
)
from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.domain.model.motif_refus import MotifRefusIdentity
from admission.ddd.admission.domain.model.poste_diplomatique import (
    PosteDiplomatiqueIdentity,
)
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
    ChoixAffiliationSport,
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
from admission.ddd.admission.formation_generale.domain.model._comptabilite import (
    Comptabilite,
    comptabilite_non_remplie,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    BesoinDeDerogation,
    BesoinDeDerogationDelegueVrae,
    ChoixStatutChecklist,
    ChoixStatutPropositionGenerale,
    DecisionFacultaireEnum,
    DerogationFinancement,
    PoursuiteDeCycle,
    TypeDeRefus,
)
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    StatutChecklist,
    StatutsChecklistGenerale,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    CurriculumNonCompletePourAcceptationException,
)
from admission.ddd.admission.formation_generale.domain.validator.validator_by_business_actions import (
    ApprouverAdmissionParSicValidatorList,
    ApprouverInscriptionParSicValidatorList,
    ApprouverInscriptionTardiveParFacValidatorList,
    ApprouverParFacValidatorList,
    ApprouverParSicAValiderValidatorList,
    ApprouverReorientationExterneParFacValidatorList,
    FacPeutSoumettreAuSicLorsDeLaDecisionFacultaireValidatorList,
    ModifierStatutChecklistParcoursAnterieurValidatorList,
    RefuserParFacValidatorList,
    RefuserParSicAValiderValidatorList,
    RefuserParSicValidatorList,
    SICPeutSoumettreAFacLorsDeLaDecisionFacultaireValidatorList,
    SicPeutSoumettreAuSicLorsDeLaDecisionFacultaireValidatorList,
    SpecifierConditionAccesParcoursAnterieurValidatorList,
    SpecifierInformationsApprobationInscriptionValidatorList,
    SpecifierNouvellesInformationsDecisionFacultaireValidatorList,
)
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
    formation_id: 'FormationIdentity'
    matricule_candidat: str
    reference: int
    auteur_derniere_modification: str = ''
    annee_calculee: Optional[int] = None
    pot_calcule: Optional[AcademicCalendarTypes] = None
    statut: ChoixStatutPropositionGenerale = ChoixStatutPropositionGenerale.EN_BROUILLON
    type_demande: 'TypeDemande' = TypeDemande.ADMISSION

    creee_le: Optional[datetime.datetime] = None
    modifiee_le: Optional[datetime.datetime] = None
    soumise_le: Optional[datetime.datetime] = None

    comptabilite: 'Comptabilite' = comptabilite_non_remplie

    bourse_double_diplome_id: Optional[BourseIdentity] = None
    avec_bourse_double_diplome: Optional[bool] = None
    bourse_internationale_id: Optional[BourseIdentity] = None
    avec_bourse_internationale: Optional[bool] = None
    bourse_erasmus_mundus_id: Optional[BourseIdentity] = None
    avec_bourse_erasmus_mundus: Optional[bool] = None

    est_bachelier_belge: Optional[bool] = None
    est_reorientation_inscription_externe: Optional[bool] = None
    attestation_inscription_reguliere: List[str] = attr.Factory(list)
    formulaire_reorientation: List[str] = attr.Factory(list)

    est_modification_inscription_externe: Optional[bool] = None
    formulaire_modification_inscription: List[str] = attr.Factory(list)
    attestation_inscription_reguliere_pour_modification_inscription: List[str] = attr.Factory(list)

    est_non_resident_au_sens_decret: Optional[bool] = None

    reponses_questions_specifiques: Dict = attr.Factory(dict)

    curriculum: List[str] = attr.Factory(list)
    equivalence_diplome: List[str] = attr.Factory(list)
    elements_confirmation: Dict[str, str] = attr.Factory(dict)

    est_inscription_tardive: bool = False
    checklist_initiale: Optional[StatutsChecklistGenerale] = None
    checklist_actuelle: Optional[StatutsChecklistGenerale] = None

    profil_soumis_candidat: ProfilCandidat = None

    financabilite_regle_calcule: EtatFinancabilite = ''
    financabilite_regle_calcule_situation: SituationFinancabilite = ''
    financabilite_regle_calcule_le: Optional[datetime.datetime] = None
    financabilite_regle: SituationFinancabilite = ''
    financabilite_etabli_par: str = ''
    financabilite_etabli_le: Optional[datetime.datetime] = None

    financabilite_derogation_statut: DerogationFinancement = ''
    financabilite_derogation_vrae: bool = False
    financabilite_derogation_premiere_notification_le: Optional[datetime.datetime] = None
    financabilite_derogation_premiere_notification_par: str = ''
    financabilite_derogation_derniere_notification_le: Optional[datetime.datetime] = None
    financabilite_derogation_derniere_notification_par: str = ''

    documents_additionnels: List[str] = attr.Factory(list)

    documents_demandes: Dict = attr.Factory(dict)
    echeance_demande_documents: Optional[datetime.date] = None

    poursuite_de_cycle_a_specifier: bool = False
    poursuite_de_cycle: PoursuiteDeCycle = PoursuiteDeCycle.TO_BE_DETERMINED

    poste_diplomatique: Optional[PosteDiplomatiqueIdentity] = None

    # Décision facultaire & sic
    certificat_approbation_fac: List[str] = attr.Factory(list)
    certificat_refus_fac: List[str] = attr.Factory(list)
    derogation_delegue_vrae: Optional[BesoinDeDerogationDelegueVrae] = None
    derogation_delegue_vrae_commentaire: str = ''
    justificatif_derogation_delegue_vrae: List[str] = attr.Factory(list)
    certificat_approbation_sic: List[str] = attr.Factory(list)
    certificat_approbation_sic_annexe: List[str] = attr.Factory(list)
    certificat_refus_sic: List[str] = attr.Factory(list)

    type_de_refus: Optional['TypeDeRefus'] = ''
    motifs_refus: List[MotifRefusIdentity] = attr.Factory(list)
    autres_motifs_refus: List[str] = attr.Factory(list)

    autre_formation_choisie_fac_id: Optional['FormationIdentity'] = None
    avec_conditions_complementaires: Optional[bool] = None
    conditions_complementaires_existantes: List[ConditionComplementaireApprobationIdentity] = attr.Factory(list)
    conditions_complementaires_libres: List[ConditionComplementaireLibreApprobation] = attr.Factory(list)
    complements_formation: Optional[List[ComplementFormationIdentity]] = attr.Factory(list)
    avec_complements_formation: Optional[bool] = None
    commentaire_complements_formation: str = ''
    nombre_annees_prevoir_programme: Optional[int] = None
    nom_personne_contact_programme_annuel_annuel: str = ''
    email_personne_contact_programme_annuel_annuel: str = ''
    commentaire_programme_conjoint: str = ''
    besoin_de_derogation: Optional['BesoinDeDerogation'] = ''

    droits_inscription_montant: Optional['DroitsInscriptionMontant'] = ''
    droits_inscription_montant_autre: Optional[Decimal] = None
    dispense_ou_droits_majores: Optional['DispenseOuDroitsMajores'] = ''
    tarif_particulier: str = ''
    refacturation_ou_tiers_payant: str = ''
    annee_de_premiere_inscription_et_statut: str = ''
    est_mobilite: Optional[bool] = None
    nombre_de_mois_de_mobilite: Optional['MobiliteNombreDeMois'] = ''
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
    def premiere_annee_de_bachelier(self) -> bool:
        return bool(self.poursuite_de_cycle_a_specifier and self.poursuite_de_cycle != PoursuiteDeCycle.YES)

    def modifier_choix_formation(
        self,
        formation_id: FormationIdentity,
        bourses_ids: Dict[str, BourseIdentity],
        avec_bourse_double_diplome: Optional[bool],
        bourse_double_diplome: Optional[str],
        avec_bourse_internationale: Optional[bool],
        bourse_internationale: Optional[str],
        avec_bourse_erasmus_mundus: Optional[bool],
        bourse_erasmus_mundus: Optional[str],
        reponses_questions_specifiques: Dict,
    ):
        self.formation_id = formation_id
        self.reponses_questions_specifiques = reponses_questions_specifiques
        self.bourse_double_diplome_id = bourses_ids.get(bourse_double_diplome) if bourse_double_diplome else None
        self.avec_bourse_double_diplome = avec_bourse_double_diplome
        self.bourse_internationale_id = bourses_ids.get(bourse_internationale) if bourse_internationale else None
        self.avec_bourse_internationale = avec_bourse_internationale
        self.bourse_erasmus_mundus_id = bourses_ids.get(bourse_erasmus_mundus) if bourse_erasmus_mundus else None
        self.avec_bourse_erasmus_mundus = avec_bourse_erasmus_mundus
        self.auteur_derniere_modification = self.matricule_candidat

        self.comptabilite.affiliation_sport = None  # Ce choix dépend du campus de formation

    def modifier_choix_formation_par_gestionnaire(
        self,
        auteur_modification: str,
        bourses_ids: Dict[str, BourseIdentity],
        avec_bourse_double_diplome: Optional[bool],
        bourse_double_diplome: Optional[str],
        avec_bourse_internationale: Optional[bool],
        bourse_internationale: Optional[str],
        avec_bourse_erasmus_mundus: Optional[bool],
        bourse_erasmus_mundus: Optional[str],
        reponses_questions_specifiques: Dict,
    ):
        self.auteur_derniere_modification = auteur_modification
        self.reponses_questions_specifiques = reponses_questions_specifiques
        self.bourse_double_diplome_id = bourses_ids.get(bourse_double_diplome) if bourse_double_diplome else None
        self.avec_bourse_double_diplome = avec_bourse_double_diplome
        self.bourse_internationale_id = bourses_ids.get(bourse_internationale) if bourse_internationale else None
        self.avec_bourse_internationale = avec_bourse_internationale
        self.bourse_erasmus_mundus_id = bourses_ids.get(bourse_erasmus_mundus) if bourse_erasmus_mundus else None
        self.avec_bourse_erasmus_mundus = avec_bourse_erasmus_mundus

    def modifier_checklist_choix_formation(
        self,
        auteur_modification: str,
        type_demande: 'TypeDemande',
        formation_id: FormationIdentity,
        poursuite_de_cycle: 'PoursuiteDeCycle',
        est_inscription_tardive: bool,
    ):
        self.auteur_derniere_modification = auteur_modification
        self.type_demande = type_demande
        self.formation_id = formation_id
        self.annee_calculee = formation_id.annee
        self.poursuite_de_cycle = poursuite_de_cycle
        self.est_inscription_tardive = est_inscription_tardive

    def supprimer(self):
        self.statut = ChoixStatutPropositionGenerale.ANNULEE
        self.auteur_derniere_modification = self.matricule_candidat

    def soumettre(
        self,
        formation_id: FormationIdentity,
        pool: 'AcademicCalendarTypes',
        elements_confirmation: Dict[str, str],
        type_demande: TypeDemande,
        est_inscription_tardive: bool,
        profil_candidat_soumis: ProfilCandidat,
        doit_payer_frais_dossier: bool,
    ):
        if doit_payer_frais_dossier:
            self.statut = ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE
        else:
            self.statut = ChoixStatutPropositionGenerale.CONFIRMEE
        self.type_demande = type_demande
        self.annee_calculee = formation_id.annee
        self.formation_id = formation_id
        self.pot_calcule = pool
        self.elements_confirmation = elements_confirmation
        self.soumise_le = now()
        if pool != AcademicCalendarTypes.ADMISSION_POOL_EXTERNAL_REORIENTATION:
            self.attestation_inscription_reguliere = []
            self.formulaire_reorientation = []
        if pool != AcademicCalendarTypes.ADMISSION_POOL_EXTERNAL_ENROLLMENT_CHANGE:
            self.formulaire_modification_inscription = []
            self.attestation_inscription_reguliere_pour_modification_inscription = []
        self.est_inscription_tardive = est_inscription_tardive
        self.profil_soumis_candidat = profil_candidat_soumis
        self.auteur_derniere_modification = self.matricule_candidat

    def payer_frais_dossier(self):
        self.statut = ChoixStatutPropositionGenerale.CONFIRMEE
        self.auteur_derniere_modification = self.matricule_candidat

        self.checklist_actuelle.frais_dossier = StatutChecklist(
            libelle=__('Payed'),
            statut=ChoixStatutChecklist.SYST_REUSSITE,
        )

    def reclamer_documents_par_sic(self, auteur_modification: str, a_echeance_le: datetime.date):
        self.statut = ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC
        self.auteur_derniere_modification = auteur_modification
        self.echeance_demande_documents = a_echeance_le

    def reclamer_documents_par_fac(self, auteur_modification: str, a_echeance_le: datetime.date):
        self.statut = ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC
        self.auteur_derniere_modification = auteur_modification
        self.echeance_demande_documents = a_echeance_le

    def specifier_refus_par_fac(self):
        self.checklist_actuelle.decision_facultaire = StatutChecklist(
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            libelle=__('Refusal'),
            extra={
                'decision': DecisionFacultaireEnum.EN_DECISION.value,
            },
        )

    def specifier_acceptation_par_fac(self):
        self.checklist_actuelle.decision_facultaire = StatutChecklist(
            statut=ChoixStatutChecklist.GEST_REUSSITE,
            libelle=__('Approval'),
        )

    def specifier_motifs_refus_par_fac(
        self,
        uuids_motifs: List[str],
        autres_motifs: List[str],
        auteur_modification: str,
    ):
        SpecifierNouvellesInformationsDecisionFacultaireValidatorList(
            statut=self.statut,
        ).validate()
        self.specifier_refus_par_fac()
        self.motifs_refus = [MotifRefusIdentity(uuid=uuid_motif) for uuid_motif in uuids_motifs]
        self.autres_motifs_refus = autres_motifs
        self.auteur_derniere_modification = auteur_modification

    def specifier_informations_acceptation_par_fac(
        self,
        auteur_modification: str,
        sigle_autre_formation: str,
        avec_conditions_complementaires: Optional[bool],
        uuids_conditions_complementaires_existantes: Optional[List[str]],
        conditions_complementaires_libres: Optional[List[Dict]],
        avec_complements_formation: Optional[bool],
        uuids_complements_formation: Optional[List[str]],
        commentaire_complements_formation: str,
        nombre_annees_prevoir_programme: Optional[int],
        nom_personne_contact_programme_annuel: str,
        email_personne_contact_programme_annuel: str,
        commentaire_programme_conjoint: str,
    ):
        SpecifierNouvellesInformationsDecisionFacultaireValidatorList(
            statut=self.statut,
        ).validate()
        self.specifier_acceptation_par_fac()
        self.auteur_derniere_modification = auteur_modification
        self.autre_formation_choisie_fac_id = (
            FormationIdentity(
                sigle=sigle_autre_formation,
                annee=self.annee_calculee,
            )
            if sigle_autre_formation
            else None
        )

        self.avec_conditions_complementaires = avec_conditions_complementaires
        self.conditions_complementaires_existantes = (
            [
                ConditionComplementaireApprobationIdentity(uuid=uuid_condition)
                for uuid_condition in uuids_conditions_complementaires_existantes
            ]
            if uuids_conditions_complementaires_existantes
            else []
        )

        self.conditions_complementaires_libres = [
            ConditionComplementaireLibreApprobation(
                nom_fr=condition_libre.get('name_fr', ''),
                nom_en=condition_libre.get('name_en', ''),
                uuid_experience=condition_libre.get('related_experience_id', ''),
            )
            for condition_libre in conditions_complementaires_libres
        ]

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

    def refuser_par_fac(self, auteur_modification: str):
        RefuserParFacValidatorList(
            statut=self.statut,
            motifs_refus=self.motifs_refus,
            autres_motifs_refus=self.autres_motifs_refus,
        ).validate()

        self.specifier_refus_par_fac()
        self.statut = ChoixStatutPropositionGenerale.RETOUR_DE_FAC
        self.auteur_derniere_modification = auteur_modification

    def approuver_par_fac(self, auteur_modification: str, titres_selectionnes: List[TitreAccesSelectionnable]):
        ApprouverParFacValidatorList(
            statut=self.statut,
            avec_conditions_complementaires=self.avec_conditions_complementaires,
            conditions_complementaires_existantes=self.conditions_complementaires_existantes,
            conditions_complementaires_libres=self.conditions_complementaires_libres,
            avec_complements_formation=self.avec_complements_formation,
            complements_formation=self.complements_formation,
            nombre_annees_prevoir_programme=self.nombre_annees_prevoir_programme,
            titres_selectionnes=titres_selectionnes,
        ).validate()

        self.specifier_acceptation_par_fac()
        self.statut = ChoixStatutPropositionGenerale.RETOUR_DE_FAC
        self.auteur_derniere_modification = auteur_modification

    def approuver_inscription_tardive_par_fac(
        self,
        auteur_modification: str,
        titres_selectionnes: List[TitreAccesSelectionnable],
    ):
        ApprouverInscriptionTardiveParFacValidatorList(
            statut=self.statut,
            condition_acces=self.condition_acces,
            est_inscription_tardive=self.est_inscription_tardive,
            titres_selectionnes=titres_selectionnes,
        ).validate()

        self.specifier_acceptation_par_fac()
        self.statut = ChoixStatutPropositionGenerale.RETOUR_DE_FAC
        self.auteur_derniere_modification = auteur_modification

    def approuver_reorientation_externe_par_fac(
        self,
        auteur_modification: str,
        titres_selectionnes: List[TitreAccesSelectionnable],
    ):
        ApprouverReorientationExterneParFacValidatorList(
            statut=self.statut,
            condition_acces=self.condition_acces,
            est_reorientation_inscription_externe=self.est_reorientation_inscription_externe,
            titres_selectionnes=titres_selectionnes,
        ).validate()

        self.specifier_acceptation_par_fac()
        self.statut = ChoixStatutPropositionGenerale.RETOUR_DE_FAC
        self.auteur_derniere_modification = auteur_modification

    def soumettre_a_fac_lors_de_la_decision_facultaire(self, auteur_modification: str):
        SICPeutSoumettreAFacLorsDeLaDecisionFacultaireValidatorList(
            statut=self.statut,
        ).validate()
        self.auteur_derniere_modification = auteur_modification
        self.statut = ChoixStatutPropositionGenerale.TRAITEMENT_FAC

    def soumettre_au_sic_lors_de_la_decision_facultaire(self, envoi_par_fac: bool, auteur_modification: str):
        if envoi_par_fac:
            FacPeutSoumettreAuSicLorsDeLaDecisionFacultaireValidatorList(
                statut=self.statut,
                checklist_actuelle=self.checklist_actuelle,
            ).validate()
        else:
            SicPeutSoumettreAuSicLorsDeLaDecisionFacultaireValidatorList(statut=self.statut).validate()
        self.statut = ChoixStatutPropositionGenerale.RETOUR_DE_FAC
        self.auteur_derniere_modification = auteur_modification

    def specifier_paiement_frais_dossier_necessaire_par_gestionnaire(self, auteur_modification: str):
        self.statut = ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE
        self.checklist_actuelle.frais_dossier = StatutChecklist(
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            libelle=__('Must pay'),
        )
        self.auteur_derniere_modification = auteur_modification

    def specifier_paiement_frais_dossier_plus_necessaire_par_gestionnaire(
        self,
        statut_checklist_cible: str,
        auteur_modification: str,
    ):
        self.statut = ChoixStatutPropositionGenerale.CONFIRMEE
        self.checklist_actuelle.frais_dossier = {
            ChoixStatutChecklist.INITIAL_NON_CONCERNE.name: StatutChecklist(
                statut=ChoixStatutChecklist.INITIAL_NON_CONCERNE,
                libelle=__('Not concerned'),
            ),
            ChoixStatutChecklist.GEST_REUSSITE.name: StatutChecklist(
                statut=ChoixStatutChecklist.GEST_REUSSITE,
                libelle=__('Dispensed'),
            ),
        }[statut_checklist_cible]
        self.auteur_derniere_modification = auteur_modification

    def completer_documents_par_candidat(self):
        self.statut = {
            ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC: ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC,
            ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC: ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC,
        }.get(self.statut)
        self.auteur_derniere_modification = self.matricule_candidat
        self.echeance_demande_documents = None

    def completer_curriculum(
        self,
        curriculum: List[str],
        equivalence_diplome: List[str],
        reponses_questions_specifiques: Dict,
        auteur_modification: str,
    ):
        self.curriculum = curriculum
        self.equivalence_diplome = equivalence_diplome
        self.reponses_questions_specifiques = reponses_questions_specifiques
        self.auteur_derniere_modification = auteur_modification

    def completer_comptabilite(
        self,
        auteur_modification: str,
        attestation_absence_dette_etablissement: List[str],
        demande_allocation_etudes_fr_be: Optional[bool],
        enfant_personnel: Optional[bool],
        attestation_enfant_personnel: List[str],
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
        affiliation_sport: Optional[str],
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
            demande_allocation_d_etudes_communaute_francaise_belgique=demande_allocation_etudes_fr_be,
            enfant_personnel=enfant_personnel,
            attestation_enfant_personnel=attestation_enfant_personnel,
            preuve_statut_apatride=preuve_statut_apatride,
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
            affiliation_sport=ChoixAffiliationSport[affiliation_sport] if affiliation_sport else None,
            etudiant_solidaire=etudiant_solidaire,
            type_numero_compte=ChoixTypeCompteBancaire[type_numero_compte] if type_numero_compte else None,
            numero_compte_iban=numero_compte_iban,
            iban_valide=iban_valide,
            numero_compte_autre_format=numero_compte_autre_format,
            code_bic_swift_banque=code_bic_swift_banque,
            prenom_titulaire_compte=prenom_titulaire_compte,
            nom_titulaire_compte=nom_titulaire_compte,
        )

    def specifier_statut_checklist_parcours_anterieur(
        self,
        statut_checklist_cible: str,
        titres_acces_selectionnes: List[TitreAccesSelectionnable],
        auteur_modification: str,
        uuids_experiences_valorisees: set[str],
    ):
        ModifierStatutChecklistParcoursAnterieurValidatorList(
            checklist=self.checklist_actuelle,
            uuids_experiences_valorisees=uuids_experiences_valorisees,
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
        type_experience: str,
        profil_candidat_translator: IProfilCandidatTranslator,
        grade_academique_formation_proposition: str,
    ):
        if statut_checklist_cible == ChoixStatutChecklist.GEST_REUSSITE.name:
            # Une expérience académique ne peut passer à l'état "Validé" que si elle est complète
            ProfilCandidatService.verifier_experience_curriculum_formation_generale_apres_soumission(
                proposition=self,
                uuid_experience=uuid_experience,
                type_experience=type_experience,
                profil_candidat_translator=profil_candidat_translator,
                grade_academique_formation_proposition=grade_academique_formation_proposition,
            )

        try:
            experience = self.checklist_actuelle.recuperer_enfant('parcours_anterieur', uuid_experience)
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

    def completer_informations_complementaires(
        self,
        reponses_questions_specifiques: Dict,
        documents_additionnels: List[str],
        poste_diplomatique: Optional[PosteDiplomatiqueIdentity],
    ):
        self.auteur_derniere_modification = self.matricule_candidat
        self.reponses_questions_specifiques = reponses_questions_specifiques
        self.documents_additionnels = documents_additionnels
        self.poste_diplomatique = poste_diplomatique

    def completer_informations_complementaires_par_gestionnaire(
        self,
        auteur_modification: str,
        reponses_questions_specifiques: Dict,
        documents_additionnels: List[str],
        poste_diplomatique: Optional[PosteDiplomatiqueIdentity],
        est_bachelier_belge: Optional[bool],
        est_reorientation_inscription_externe: Optional[bool],
        attestation_inscription_reguliere: List[str],
        formulaire_reorientation: List[str],
        est_modification_inscription_externe: Optional[bool],
        formulaire_modification_inscription: List[str],
        attestation_inscription_reguliere_pour_modification_inscription: List[str],
        est_non_resident_au_sens_decret: Optional[bool],
    ):
        self.auteur_derniere_modification = auteur_modification
        self.reponses_questions_specifiques = reponses_questions_specifiques
        self.documents_additionnels = documents_additionnels

        self.poste_diplomatique = poste_diplomatique

        self.est_non_resident_au_sens_decret = est_non_resident_au_sens_decret
        self.est_bachelier_belge = est_bachelier_belge
        self.est_reorientation_inscription_externe = est_reorientation_inscription_externe
        self.attestation_inscription_reguliere = attestation_inscription_reguliere
        self.formulaire_reorientation = formulaire_reorientation
        self.est_modification_inscription_externe = est_modification_inscription_externe
        self.formulaire_modification_inscription = formulaire_modification_inscription
        self.attestation_inscription_reguliere_pour_modification_inscription = (
            attestation_inscription_reguliere_pour_modification_inscription
        )
        if self.est_modification_inscription_externe:
            self.est_inscription_tardive = False

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
            else ''
        )
        self.financabilite_regle_calcule_le = now()
        if auteur_modification:
            self.auteur_derniere_modification = auteur_modification

    def specifier_financabilite_regle(
        self,
        financabilite_regle: SituationFinancabilite,
        auteur_modification: str,
    ):
        self.financabilite_regle = financabilite_regle
        self.financabilite_etabli_par = auteur_modification
        self.financabilite_etabli_le = now()
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
        self.financabilite_etabli_le = now()
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
        self.auteur_derniere_modification = auteur_modification
        self.financabilite_derogation_statut = statut
        if statut == DerogationFinancement.REFUS_DE_DEROGATION_FACULTAIRE:
            self.motifs_refus = [MotifRefusIdentity(uuid=uuid_motif) for uuid_motif in refus_uuids_motifs]
            self.autres_motifs_refus = refus_autres_motifs

    def specifier_derogation_vrae_financabilite(
        self,
        derogation_vrae: bool,
        auteur_modification: str,
    ):
        self.auteur_derniere_modification = auteur_modification
        self.financabilite_derogation_vrae = derogation_vrae

    def notifier_candidat_derogation_financabilite(self, gestionnaire: str):
        self.financabilite_derogation_statut = DerogationFinancement.CANDIDAT_NOTIFIE
        if not self.financabilite_derogation_premiere_notification_le:
            self.financabilite_derogation_premiere_notification_le = now()
            self.financabilite_derogation_premiere_notification_par = gestionnaire
        else:
            self.financabilite_derogation_derniere_notification_le = now()
            self.financabilite_derogation_derniere_notification_par = gestionnaire

    def specifier_besoin_de_derogation(self, besoin_de_derogation: BesoinDeDerogation, auteur_modification: str):
        self.besoin_de_derogation = besoin_de_derogation
        self.auteur_derniere_modification = auteur_modification

    def specifier_derogation_delegue_vrae(
        self,
        derogation: BesoinDeDerogationDelegueVrae,
        commentaire: str,
        justificatif: List[str],
        auteur_modification: str,
    ):
        self.derogation_delegue_vrae = derogation
        if derogation == BesoinDeDerogationDelegueVrae.PAS_DE_DEROGATION:
            self.derogation_delegue_vrae_commentaire = ''
            self.justificatif_derogation_delegue_vrae = []
        else:
            self.derogation_delegue_vrae_commentaire = commentaire
            self.justificatif_derogation_delegue_vrae = justificatif
        self.auteur_derniere_modification = auteur_modification
        self.checklist_actuelle.decision_sic = StatutChecklist(
            statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
            libelle=__('To be processed'),
        )

    def _specifier_informations_de_base_acceptation_par_sic(
        self,
        auteur_modification: str,
        avec_conditions_complementaires: Optional[bool],
        uuids_conditions_complementaires_existantes: Optional[List[str]],
        conditions_complementaires_libres: Optional[List[Dict]],
        avec_complements_formation: Optional[bool],
        uuids_complements_formation: Optional[List[str]],
        commentaire_complements_formation: str,
        nombre_annees_prevoir_programme: Optional[int],
        nom_personne_contact_programme_annuel: str,
        email_personne_contact_programme_annuel: str,
    ):
        """Spécifier les informations d'acceptation par SIC communes entre les admissions et les inscriptions."""
        self.auteur_derniere_modification = auteur_modification

        self.avec_conditions_complementaires = avec_conditions_complementaires
        self.conditions_complementaires_existantes = (
            [
                ConditionComplementaireApprobationIdentity(uuid=uuid_condition)
                for uuid_condition in uuids_conditions_complementaires_existantes
            ]
            if uuids_conditions_complementaires_existantes
            else []
        )
        self.conditions_complementaires_libres = [
            ConditionComplementaireLibreApprobation(
                nom_fr=condition_libre.get('name_fr', ''),
                nom_en=condition_libre.get('name_en', ''),
                uuid_experience=condition_libre.get('related_experience_id', ''),
            )
            for condition_libre in conditions_complementaires_libres
        ]

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
        avec_conditions_complementaires: Optional[bool],
        uuids_conditions_complementaires_existantes: Optional[List[str]],
        conditions_complementaires_libres: Optional[List[Dict]],
        avec_complements_formation: Optional[bool],
        uuids_complements_formation: Optional[List[str]],
        commentaire_complements_formation: str,
        nombre_annees_prevoir_programme: Optional[int],
        nom_personne_contact_programme_annuel: str,
        email_personne_contact_programme_annuel: str,
        droits_inscription_montant: str,
        droits_inscription_montant_autre: Optional[float],
        dispense_ou_droits_majores: str,
        tarif_particulier: str,
        refacturation_ou_tiers_payant: str,
        annee_de_premiere_inscription_et_statut: str,
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
        self.statut = ChoixStatutPropositionGenerale.ATTENTE_VALIDATION_DIRECTION
        self.checklist_actuelle.decision_sic = StatutChecklist(
            statut=ChoixStatutChecklist.GEST_EN_COURS,
            libelle=__('Approval'),
            extra={'en_cours': "approval"},
        )

        self._specifier_informations_de_base_acceptation_par_sic(
            auteur_modification=auteur_modification,
            avec_conditions_complementaires=avec_conditions_complementaires,
            uuids_conditions_complementaires_existantes=uuids_conditions_complementaires_existantes,
            conditions_complementaires_libres=conditions_complementaires_libres,
            avec_complements_formation=avec_complements_formation,
            uuids_complements_formation=uuids_complements_formation,
            commentaire_complements_formation=commentaire_complements_formation,
            nombre_annees_prevoir_programme=nombre_annees_prevoir_programme,
            nom_personne_contact_programme_annuel=nom_personne_contact_programme_annuel,
            email_personne_contact_programme_annuel=email_personne_contact_programme_annuel,
        )

        self.droits_inscription_montant = droits_inscription_montant
        self.droits_inscription_montant_autre = droits_inscription_montant_autre
        self.dispense_ou_droits_majores = dispense_ou_droits_majores
        self.tarif_particulier = tarif_particulier
        self.refacturation_ou_tiers_payant = refacturation_ou_tiers_payant
        self.annee_de_premiere_inscription_et_statut = annee_de_premiere_inscription_et_statut
        self.est_mobilite = est_mobilite
        self.nombre_de_mois_de_mobilite = nombre_de_mois_de_mobilite
        self.doit_se_presenter_en_sic = doit_se_presenter_en_sic
        self.communication_au_candidat = communication_au_candidat
        self.doit_fournir_visa_etudes = doit_fournir_visa_etudes

    def specifier_informations_acceptation_inscription_par_sic(
        self,
        auteur_modification: str,
        avec_conditions_complementaires: Optional[bool],
        uuids_conditions_complementaires_existantes: Optional[List[str]],
        conditions_complementaires_libres: Optional[List[Dict]],
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
            avec_conditions_complementaires=avec_conditions_complementaires,
            uuids_conditions_complementaires_existantes=uuids_conditions_complementaires_existantes,
            conditions_complementaires_libres=conditions_complementaires_libres,
            avec_complements_formation=avec_complements_formation,
            uuids_complements_formation=uuids_complements_formation,
            commentaire_complements_formation=commentaire_complements_formation,
            nombre_annees_prevoir_programme=nombre_annees_prevoir_programme,
            nom_personne_contact_programme_annuel=nom_personne_contact_programme_annuel,
            email_personne_contact_programme_annuel=email_personne_contact_programme_annuel,
        )

    def specifier_motifs_refus_par_sic(
        self,
        auteur_modification: str,
        type_de_refus: TypeDeRefus,
        uuids_motifs: List[str],
        autres_motifs: List[str],
    ):
        RefuserParSicAValiderValidatorList(statut=self.statut).validate()
        self.statut = ChoixStatutPropositionGenerale.ATTENTE_VALIDATION_DIRECTION
        self.checklist_actuelle.decision_sic = StatutChecklist(
            statut=ChoixStatutChecklist.GEST_EN_COURS,
            libelle=__('Refusal'),
            extra={'en_cours': "refusal"},
        )
        self.auteur_derniere_modification = auteur_modification
        self.type_de_refus = type_de_refus
        self.motifs_refus = [MotifRefusIdentity(uuid=uuid_motif) for uuid_motif in uuids_motifs]
        self.autres_motifs_refus = autres_motifs

    def refuser_par_sic(self, auteur_modification: str):
        RefuserParSicValidatorList(
            statut=self.statut,
            motifs_refus=self.motifs_refus,
            autres_motifs_refus=self.autres_motifs_refus,
        ).validate()

        self.checklist_actuelle.decision_sic = StatutChecklist(
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            libelle=__('Refusal'),
            extra={'blocage': 'refusal'},
        )
        self.statut = ChoixStatutPropositionGenerale.INSCRIPTION_REFUSEE
        self.auteur_derniere_modification = auteur_modification

    def approuver_par_sic(
        self,
        auteur_modification: str,
        documents_dto: List[EmplacementDocumentDTO],
        curriculum_dto: CurriculumAdmissionDTO,
        profil_candidat_translator: IProfilCandidatTranslator,
        experience_parcours_interne_translator: IExperienceParcoursInterneTranslator,
        grade_academique_formation_proposition: str,
    ):
        if self.type_demande == TypeDemande.INSCRIPTION:
            ApprouverInscriptionParSicValidatorList(
                statut=self.statut,
                checklist=self.checklist_actuelle,
                besoin_de_derogation=self.besoin_de_derogation,
                avec_conditions_complementaires=self.avec_conditions_complementaires,
                conditions_complementaires_existantes=self.conditions_complementaires_existantes,
                conditions_complementaires_libres=self.conditions_complementaires_libres,
                documents_dto=documents_dto,
            ).validate()

        else:
            ApprouverAdmissionParSicValidatorList(
                statut=self.statut,
                avec_conditions_complementaires=self.avec_conditions_complementaires,
                conditions_complementaires_existantes=self.conditions_complementaires_existantes,
                conditions_complementaires_libres=self.conditions_complementaires_libres,
                avec_complements_formation=self.avec_complements_formation,
                complements_formation=self.complements_formation,
                nombre_annees_prevoir_programme=self.nombre_annees_prevoir_programme,
                checklist=self.checklist_actuelle,
                documents_dto=documents_dto,
            ).validate()

        try:
            ProfilCandidatService.verifier_curriculum_formation_generale_apres_soumission(
                proposition=self,
                curriculum_dto=curriculum_dto,
                profil_candidat_translator=profil_candidat_translator,
                experience_parcours_interne_translator=experience_parcours_interne_translator,
                verification_experiences_completees=False,
                grade_academique_formation_proposition=grade_academique_formation_proposition,
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
        self.statut = ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE
        self.auteur_derniere_modification = auteur_modification

    def annuler_reclamation_documents(self, auteur_modification: str, par_fac: bool):
        self.statut = (
            ChoixStatutPropositionGenerale.TRAITEMENT_FAC if par_fac else ChoixStatutPropositionGenerale.CONFIRMEE
        )
        self.auteur_derniere_modification = auteur_modification
        self.echeance_demande_documents = None

    def nettoyer_reponses_questions_specifiques(self, questions_specifiques: List[QuestionSpecifique]):
        self.reponses_questions_specifiques = ISuperQuestionSpecifiqueTranslator.clean_specific_question_answers(
            questions_specifiques,
            self.reponses_questions_specifiques,
        )

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
import datetime
import uuid
from typing import List, Optional, Union

import attr

from admission.ddd.projet_doctoral.preparation.domain.model._comptabilite import (
    Comptabilite,
    comptabilite_non_remplie,
    TypeSituationAssimilation,
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    ChoixAssimilation6,
    ChoixAffiliationSport,
    ChoixTypeCompteBancaire,
    LienParente,
)
from admission.ddd.projet_doctoral.preparation.domain.model._detail_projet import (
    ChoixLangueRedactionThese,
    DetailProjet,
)
from admission.ddd.projet_doctoral.preparation.domain.model._enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
    ChoixStatutProposition,
    ChoixTypeAdmission,
)
from admission.ddd.projet_doctoral.preparation.domain.model._experience_precedente_recherche import (
    ChoixDoctoratDejaRealise,
    ExperiencePrecedenteRecherche,
    aucune_experience_precedente_recherche,
)
from admission.ddd.projet_doctoral.preparation.domain.model._financement import (
    ChoixTypeFinancement,
    Financement,
    financement_non_rempli,
)
from admission.ddd.projet_doctoral.preparation.domain.model._institut import InstitutIdentity
from admission.ddd.projet_doctoral.preparation.domain.model.doctorat import DoctoratIdentity
from admission.ddd.projet_doctoral.preparation.domain.validator.validator_by_business_action import (
    CompletionPropositionValidatorList,
    ProjetDoctoralValidatorList,
)
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class PropositionIdentity(interface.EntityIdentity):
    uuid: str


@attr.dataclass(slots=True, hash=False, eq=False)
class Proposition(interface.RootEntity):
    entity_id: 'PropositionIdentity'
    type_admission: ChoixTypeAdmission
    doctorat_id: 'DoctoratIdentity'
    matricule_candidat: str
    projet: 'DetailProjet'
    reference: Optional[str] = None
    justification: Optional[str] = ''
    statut: ChoixStatutProposition = ChoixStatutProposition.IN_PROGRESS
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
    fiche_archive_signatures_envoyees: List[str] = attr.Factory(list)
    comptabilite: 'Comptabilite' = comptabilite_non_remplie

    @property
    def sigle_formation(self):
        return self.doctorat_id.sigle

    @property
    def annee(self):
        return self.doctorat_id.annee

    valeur_reference_base = 300000

    @property
    def est_verrouillee_pour_signature(self) -> bool:
        return self.statut == ChoixStatutProposition.SIGNING_IN_PROGRESS

    def est_en_cours(self):
        return self.statut != ChoixStatutProposition.CANCELLED

    def completer(
        self,
        type_admission: str,
        justification: Optional[str],
        commission_proximite: Optional[str],
        type_financement: Optional[str],
        type_contrat_travail: Optional[str],
        eft: Optional[int],
        bourse_recherche: Optional[str],
        bourse_date_debut: Optional[datetime.date],
        bourse_date_fin: Optional[datetime.date],
        bourse_preuve: List[str],
        duree_prevue: Optional[int],
        temps_consacre: Optional[int],
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
        documents: List[str] = None,
        graphe_gantt: List[str] = None,
        proposition_programme_doctoral: List[str] = None,
        projet_formation_complementaire: List[str] = None,
        lettres_recommandation: List[str] = None,
    ) -> None:
        CompletionPropositionValidatorList(
            type_admission=type_admission,
            type_financement=type_financement,
            justification=justification,
            type_contrat_travail=type_contrat_travail,
            doctorat_deja_realise=doctorat_deja_realise,
            institution=institution,
            domaine_these=domaine_these,
        ).validate()
        self._completer_proposition(type_admission, justification, commission_proximite)
        self._completer_financement(
            type=type_financement,
            type_contrat_travail=type_contrat_travail,
            eft=eft,
            bourse_recherche=bourse_recherche,
            bourse_date_debut=bourse_date_debut,
            bourse_date_fin=bourse_date_fin,
            bourse_preuve=bourse_preuve,
            duree_prevue=duree_prevue,
            temps_consacre=temps_consacre,
        )
        self._completer_projet(
            titre=titre,
            resume=resume,
            langue_redaction_these=langue_redaction_these,
            institut_these=institut_these,
            lieu_these=lieu_these,
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
        type_admission: str,
        justification: Optional[str],
        commission_proximite: Optional[str],
    ):
        self.type_admission = ChoixTypeAdmission[type_admission]
        self.justification = justification or ''
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
        bourse_recherche: Optional[str],
        bourse_date_debut: Optional[datetime.date],
        bourse_date_fin: Optional[datetime.date],
        bourse_preuve: List[str],
        duree_prevue: Optional[int],
        temps_consacre: Optional[int],
    ):
        if type:
            self.financement = Financement(
                type=ChoixTypeFinancement[type],
                type_contrat_travail=type_contrat_travail or '',
                eft=eft,
                bourse_recherche=bourse_recherche or '',
                bourse_date_debut=bourse_date_debut,
                bourse_date_fin=bourse_date_fin,
                bourse_preuve=bourse_preuve or [],
                duree_prevue=duree_prevue,
                temps_consacre=temps_consacre,
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
        documents: List[str] = None,
        graphe_gantt: List[str] = None,
        proposition_programme_doctoral: List[str] = None,
        projet_formation_complementaire: List[str] = None,
        lettres_recommandation: List[str] = None,
    ):
        self.projet = DetailProjet(
            titre=titre or '',
            resume=resume or '',
            langue_redaction_these=(
                ChoixLangueRedactionThese[langue_redaction_these]
                if langue_redaction_these
                else ChoixLangueRedactionThese.UNDECIDED
            ),
            institut_these=InstitutIdentity(uuid.UUID(institut_these)) if institut_these else None,
            lieu_these=lieu_these or '',
            documents=documents or [],
            graphe_gantt=graphe_gantt or [],
            proposition_programme_doctoral=proposition_programme_doctoral or [],
            projet_formation_complementaire=projet_formation_complementaire or [],
            lettres_recommandation=lettres_recommandation or [],
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

    def completer_comptabilite(
        self,
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
        carte_a_b: List[str],
        decision_protection_subsidiaire: List[str],
        decision_protection_temporaire: List[str],
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
        numero_compte_autre_format: Optional[str],
        code_bic_swift_banque: Optional[str],
        prenom_titulaire_compte: Optional[str],
        nom_titulaire_compte: Optional[str],
    ):
        self.comptabilite = Comptabilite(
            attestation_absence_dette_etablissement=attestation_absence_dette_etablissement,
            demande_allocation_d_etudes_communaute_francaise_belgique=demande_allocation_etudes_fr_be,
            enfant_personnel=enfant_personnel,
            attestation_enfant_personnel=attestation_enfant_personnel,
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
            carte_a_b=carte_a_b,
            decision_protection_subsidiaire=decision_protection_subsidiaire,
            decision_protection_temporaire=decision_protection_temporaire,
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
            affiliation_sport=ChoixAffiliationSport[affiliation_sport] if affiliation_sport else None,
            etudiant_solidaire=etudiant_solidaire,
            type_numero_compte=ChoixTypeCompteBancaire[type_numero_compte] if type_numero_compte else None,
            numero_compte_iban=numero_compte_iban,
            numero_compte_autre_format=numero_compte_autre_format,
            code_bic_swift_banque=code_bic_swift_banque,
            prenom_titulaire_compte=prenom_titulaire_compte,
            nom_titulaire_compte=nom_titulaire_compte,
        )

    def reinitialiser_archive(self):
        self.fiche_archive_signatures_envoyees = []

    def verrouiller_proposition_pour_signature(self):
        self.statut = ChoixStatutProposition.SIGNING_IN_PROGRESS

    def deverrouiller_projet_doctoral(self):
        self.statut = ChoixStatutProposition.IN_PROGRESS

    def verifier_projet_doctoral(self):
        """Vérification de la validité du projet doctoral avant demande des signatures"""
        ProjetDoctoralValidatorList(self.type_admission, self.projet, self.financement).validate()

    def finaliser(self):
        self.statut = ChoixStatutProposition.SUBMITTED

    def supprimer(self):
        self.statut = ChoixStatutProposition.CANCELLED

    def valider_inscription(self):
        self.statut = ChoixStatutProposition.ENROLLED

    def definir_institut_these(self, institut_these: Optional[str]):
        if institut_these:
            self.projet = attr.evolve(
                self.projet,
                institut_these=InstitutIdentity(uuid.UUID(institut_these)),
            )

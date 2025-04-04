##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Optional, Union

from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.doctorat.preparation.commands import (
    InitierPropositionCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model._detail_projet import (
    projet_non_rempli,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
)
from admission.ddd.admission.doctorat.preparation.domain.model.parcours_doctoral import (
    ParcoursDoctoral,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    Proposition,
    PropositionIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_doctorat import (
    IDoctoratTranslator,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.validator_by_business_action import (
    InitierPropositionValidatorList,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import (
    IPropositionRepository,
)
from osis_common.ddd import interface


class PropositionBuilder(interface.RootEntityBuilder):
    @classmethod
    def build_from_repository_dto(cls, dto_object: 'interface.DTO') -> 'Proposition':
        raise NotImplementedError

    @classmethod
    def build_from_command(cls, cmd: 'InitierPropositionCommand'):  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    def initier_proposition(
        cls,
        cmd: 'InitierPropositionCommand',
        doctorat_translator: 'IDoctoratTranslator',
        proposition_repository: 'IPropositionRepository',
        parcours_doctoral_pre_admission_associee: 'Optional[ParcoursDoctoral]',
    ) -> 'Proposition':
        if cmd.pre_admission_associee and parcours_doctoral_pre_admission_associee:
            return cls.initier_nouvelle_proposition_attachee_a_pre_admission(
                cmd=cmd,
                proposition_repository=proposition_repository,
                parcours_doctoral_pre_admission=parcours_doctoral_pre_admission_associee,
            )
        else:
            return cls.initier_nouvelle_proposition_non_attachee_a_pre_admission(
                cmd,
                doctorat_translator,
                proposition_repository,
            )

    @classmethod
    def initier_nouvelle_proposition_non_attachee_a_pre_admission(
        cls,
        cmd: 'InitierPropositionCommand',
        doctorat_translator: 'IDoctoratTranslator',
        proposition_repository: 'IPropositionRepository',
    ) -> 'Proposition':
        doctorat = doctorat_translator.get(cmd.sigle_formation, cmd.annee_formation)
        InitierPropositionValidatorList(
            type_admission=cmd.type_admission,
            justification=cmd.justification,
            commission_proximite=cmd.commission_proximite,
            doctorat=doctorat,
        ).validate()
        commission_proximite: Optional[
            Union[ChoixCommissionProximiteCDEouCLSM, ChoixCommissionProximiteCDSS, ChoixSousDomaineSciences]
        ] = None
        if cmd.commission_proximite and cmd.commission_proximite in ChoixCommissionProximiteCDEouCLSM.get_names():
            commission_proximite = ChoixCommissionProximiteCDEouCLSM[cmd.commission_proximite]
        elif cmd.commission_proximite and cmd.commission_proximite in ChoixCommissionProximiteCDSS.get_names():
            commission_proximite = ChoixCommissionProximiteCDSS[cmd.commission_proximite]
        elif cmd.commission_proximite and cmd.commission_proximite in ChoixSousDomaineSciences.get_names():
            commission_proximite = ChoixSousDomaineSciences[cmd.commission_proximite]
        reference = proposition_repository.recuperer_reference_suivante()

        return Proposition(
            entity_id=PropositionIdentityBuilder.build(),
            reference=reference,
            statut=ChoixStatutPropositionDoctorale.EN_BROUILLON,
            justification=cmd.justification,
            type_admission=ChoixTypeAdmission[cmd.type_admission],
            formation_id=doctorat.entity_id,
            matricule_candidat=cmd.matricule_candidat,
            commission_proximite=commission_proximite,
            projet=projet_non_rempli,
            auteur_derniere_modification=cmd.matricule_candidat,
        )

    @classmethod
    def initier_nouvelle_proposition_attachee_a_pre_admission(
        cls,
        cmd: 'InitierPropositionCommand',
        proposition_repository: 'IPropositionRepository',
        parcours_doctoral_pre_admission: 'ParcoursDoctoral',
    ) -> 'Proposition':
        pre_admission = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.pre_admission_associee))

        reference = proposition_repository.recuperer_reference_suivante()

        proposition = Proposition(
            entity_id=PropositionIdentityBuilder.build(),
            reference=reference,
            statut=ChoixStatutPropositionDoctorale.EN_BROUILLON,
            type_admission=ChoixTypeAdmission[cmd.type_admission],
            formation_id=pre_admission.formation_id,
            matricule_candidat=parcours_doctoral_pre_admission.matricule_doctorant,
            projet=projet_non_rempli,
            auteur_derniere_modification=parcours_doctoral_pre_admission.matricule_doctorant,
            pre_admission_associee=pre_admission.entity_id,
            curriculum=pre_admission.curriculum,
        )

        proposition.definir_commission(parcours_doctoral_pre_admission.commission_proximite)

        proposition.completer(
            justification=parcours_doctoral_pre_admission.justification,
            type_financement=parcours_doctoral_pre_admission.financement_type,
            type_contrat_travail=parcours_doctoral_pre_admission.financement_type_contrat_travail,
            eft=parcours_doctoral_pre_admission.financement_eft,
            bourse_recherche=parcours_doctoral_pre_admission.financement_bourse_recherche,
            autre_bourse_recherche=parcours_doctoral_pre_admission.financement_autre_bourse_recherche,
            bourse_date_debut=parcours_doctoral_pre_admission.financement_bourse_date_debut,
            bourse_date_fin=parcours_doctoral_pre_admission.financement_bourse_date_fin,
            bourse_preuve=parcours_doctoral_pre_admission.financement_bourse_preuve,
            duree_prevue=parcours_doctoral_pre_admission.financement_duree_prevue,
            temps_consacre=parcours_doctoral_pre_admission.financement_temps_consacre,
            est_lie_fnrs_fria_fresh_csc=parcours_doctoral_pre_admission.financement_est_lie_fnrs_fria_fresh_csc,
            commentaire_financement=parcours_doctoral_pre_admission.financement_commentaire,
            langue_redaction_these=parcours_doctoral_pre_admission.projet_langue_redaction_these,
            institut_these=parcours_doctoral_pre_admission.projet_institut_these,
            lieu_these=parcours_doctoral_pre_admission.projet_lieu_these,
            titre=parcours_doctoral_pre_admission.projet_titre,
            resume=parcours_doctoral_pre_admission.projet_resume,
            doctorat_deja_realise=parcours_doctoral_pre_admission.projet_doctorat_deja_realise,
            institution=parcours_doctoral_pre_admission.projet_institution,
            domaine_these=parcours_doctoral_pre_admission.projet_domaine_these,
            date_soutenance=parcours_doctoral_pre_admission.projet_date_soutenance,
            raison_non_soutenue=parcours_doctoral_pre_admission.projet_raison_non_soutenue,
            projet_doctoral_deja_commence=parcours_doctoral_pre_admission.projet_projet_doctoral_deja_commence,
            projet_doctoral_institution=parcours_doctoral_pre_admission.projet_projet_doctoral_institution,
            projet_doctoral_date_debut=parcours_doctoral_pre_admission.projet_projet_doctoral_date_debut,
            documents=parcours_doctoral_pre_admission.projet_documents_projet,
            graphe_gantt=parcours_doctoral_pre_admission.projet_graphe_gantt,
            proposition_programme_doctoral=parcours_doctoral_pre_admission.projet_proposition_programme_doctoral,
            projet_formation_complementaire=parcours_doctoral_pre_admission.projet_projet_formation_complementaire,
            lettres_recommandation=parcours_doctoral_pre_admission.projet_lettres_recommandation,
        )

        proposition.completer_comptabilite(
            auteur_modification=parcours_doctoral_pre_admission.matricule_doctorant,
            attestation_absence_dette_etablissement=pre_admission.comptabilite.attestation_absence_dette_etablissement,
            type_situation_assimilation=(
                pre_admission.comptabilite.type_situation_assimilation.name
                if pre_admission.comptabilite.type_situation_assimilation
                else ''
            ),
            sous_type_situation_assimilation_1=(
                pre_admission.comptabilite.sous_type_situation_assimilation_1.name
                if pre_admission.comptabilite.sous_type_situation_assimilation_1
                else ''
            ),
            carte_resident_longue_duree=pre_admission.comptabilite.carte_resident_longue_duree,
            carte_cire_sejour_illimite_etranger=pre_admission.comptabilite.carte_cire_sejour_illimite_etranger,
            carte_sejour_membre_ue=pre_admission.comptabilite.carte_sejour_membre_ue,
            carte_sejour_permanent_membre_ue=pre_admission.comptabilite.carte_sejour_permanent_membre_ue,
            sous_type_situation_assimilation_2=(
                pre_admission.comptabilite.sous_type_situation_assimilation_2.name
                if pre_admission.comptabilite.sous_type_situation_assimilation_2
                else ''
            ),
            carte_a_b_refugie=pre_admission.comptabilite.carte_a_b_refugie,
            annexe_25_26_refugies_apatrides=pre_admission.comptabilite.annexe_25_26_refugies_apatrides,
            attestation_immatriculation=pre_admission.comptabilite.attestation_immatriculation,
            preuve_statut_apatride=pre_admission.comptabilite.preuve_statut_apatride,
            carte_a_b=pre_admission.comptabilite.carte_a_b,
            decision_protection_subsidiaire=pre_admission.comptabilite.decision_protection_subsidiaire,
            decision_protection_temporaire=pre_admission.comptabilite.decision_protection_temporaire,
            carte_a=pre_admission.comptabilite.carte_a,
            sous_type_situation_assimilation_3=(
                pre_admission.comptabilite.sous_type_situation_assimilation_3.name
                if pre_admission.comptabilite.sous_type_situation_assimilation_3
                else ''
            ),
            titre_sejour_3_mois_professionel=pre_admission.comptabilite.titre_sejour_3_mois_professionel,
            fiches_remuneration=pre_admission.comptabilite.fiches_remuneration,
            titre_sejour_3_mois_remplacement=pre_admission.comptabilite.titre_sejour_3_mois_remplacement,
            preuve_allocations_chomage_pension_indemnite=(
                pre_admission.comptabilite.preuve_allocations_chomage_pension_indemnite
            ),
            attestation_cpas=pre_admission.comptabilite.attestation_cpas,
            relation_parente=(
                pre_admission.comptabilite.relation_parente.name if pre_admission.comptabilite.relation_parente else ''
            ),
            sous_type_situation_assimilation_5=(
                pre_admission.comptabilite.sous_type_situation_assimilation_5.name
                if pre_admission.comptabilite.sous_type_situation_assimilation_5
                else ''
            ),
            composition_menage_acte_naissance=pre_admission.comptabilite.composition_menage_acte_naissance,
            acte_tutelle=pre_admission.comptabilite.acte_tutelle,
            composition_menage_acte_mariage=pre_admission.comptabilite.composition_menage_acte_mariage,
            attestation_cohabitation_legale=pre_admission.comptabilite.attestation_cohabitation_legale,
            carte_identite_parent=pre_admission.comptabilite.carte_identite_parent,
            titre_sejour_longue_duree_parent=pre_admission.comptabilite.titre_sejour_longue_duree_parent,
            annexe_25_26_protection_parent=(
                pre_admission.comptabilite.annexe_25_26_refugies_apatrides_decision_protection_parent
            ),
            titre_sejour_3_mois_parent=pre_admission.comptabilite.titre_sejour_3_mois_parent,
            fiches_remuneration_parent=pre_admission.comptabilite.fiches_remuneration_parent,
            attestation_cpas_parent=pre_admission.comptabilite.attestation_cpas_parent,
            sous_type_situation_assimilation_6=(
                pre_admission.comptabilite.sous_type_situation_assimilation_6.name
                if pre_admission.comptabilite.sous_type_situation_assimilation_6
                else ''
            ),
            decision_bourse_cfwb=pre_admission.comptabilite.decision_bourse_cfwb,
            attestation_boursier=pre_admission.comptabilite.attestation_boursier,
            titre_identite_sejour_longue_duree_ue=pre_admission.comptabilite.titre_identite_sejour_longue_duree_ue,
            titre_sejour_belgique=pre_admission.comptabilite.titre_sejour_belgique,
            etudiant_solidaire=pre_admission.comptabilite.etudiant_solidaire,
            type_numero_compte=(
                pre_admission.comptabilite.type_numero_compte.name
                if pre_admission.comptabilite.type_numero_compte
                else ''
            ),
            numero_compte_iban=pre_admission.comptabilite.numero_compte_iban,
            iban_valide=pre_admission.comptabilite.iban_valide,
            numero_compte_autre_format=pre_admission.comptabilite.numero_compte_autre_format,
            code_bic_swift_banque=pre_admission.comptabilite.code_bic_swift_banque,
            prenom_titulaire_compte=pre_admission.comptabilite.prenom_titulaire_compte,
            nom_titulaire_compte=pre_admission.comptabilite.nom_titulaire_compte,
        )

        return proposition

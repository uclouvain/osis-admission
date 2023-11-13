# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import string
import uuid

import factory
from factory.fuzzy import FuzzyText

from admission.ddd import DUREE_MINIMALE_PROGRAMME, DUREE_MAXIMALE_PROGRAMME
from admission.ddd.admission.domain.model.complement_formation import ComplementFormationIdentity
from admission.ddd.admission.domain.model.condition_complementaire_approbation import (
    ConditionComplementaireApprobationIdentity,
)
from admission.ddd.admission.domain.model.motif_refus import MotifRefusIdentity
from admission.ddd.admission.enums import (
    TypeSituationAssimilation,
    ChoixAffiliationSport,
    ChoixTypeCompteBancaire,
    ChoixAssimilation1,
    LienParente,
    ChoixAssimilation6,
    ChoixAssimilation5,
    ChoixAssimilation3,
    ChoixAssimilation2,
)
from admission.ddd.admission.formation_generale.domain.model._comptabilite import Comptabilite
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    StatutsChecklistGenerale,
    StatutChecklist,
)
from admission.ddd.admission.test.factory.bourse import BourseIdentityFactory
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.ddd.admission.test.factory.poste_diplomatique import PosteDiplomatiqueIdentityFactory
from admission.ddd.admission.test.factory.reference import REFERENCE_MEMORY_ITERATOR


class StatutChecklistFactory(factory.Factory):
    class Meta:
        model = StatutChecklist
        abstract = False

    libelle = FuzzyText(length=10, chars=string.digits)
    enfants = factory.List([])
    statut = ChoixStatutChecklist.INITIAL_CANDIDAT.name
    extra = factory.Dict({})


class StatutsChecklistGeneraleFactory(factory.Factory):
    class Meta:
        model = StatutsChecklistGenerale
        abstract = False

    donnees_personnelles = factory.SubFactory(StatutChecklistFactory)
    frais_dossier = factory.SubFactory(StatutChecklistFactory)
    assimilation = factory.SubFactory(StatutChecklistFactory)
    choix_formation = factory.SubFactory(StatutChecklistFactory)
    parcours_anterieur = factory.SubFactory(StatutChecklistFactory)
    financabilite = factory.SubFactory(StatutChecklistFactory)
    specificites_formation = factory.SubFactory(StatutChecklistFactory)
    decision_facultaire = factory.SubFactory(StatutChecklistFactory)
    decision_sic = factory.SubFactory(StatutChecklistFactory)


class _ComptabiliteFactory(factory.Factory):
    class Meta:
        model = Comptabilite
        abstract = False

    demande_allocation_d_etudes_communaute_francaise_belgique = False
    enfant_personnel = False
    type_situation_assimilation = TypeSituationAssimilation.AUCUNE_ASSIMILATION
    affiliation_sport = ChoixAffiliationSport.NON
    etudiant_solidaire = False
    type_numero_compte = ChoixTypeCompteBancaire.NON

    attestation_absence_dette_etablissement = ['file_token.pdf']

    attestation_enfant_personnel = ['file_token.pdf']
    sous_type_situation_assimilation_1 = ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER
    sous_type_situation_assimilation_2 = ChoixAssimilation2.PROTECTION_SUBSIDIAIRE
    sous_type_situation_assimilation_3 = ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS
    relation_parente = LienParente.MERE
    sous_type_situation_assimilation_5 = ChoixAssimilation5.PRIS_EN_CHARGE_OU_DESIGNE_CPAS
    sous_type_situation_assimilation_6 = ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT
    carte_a = ['file_token.pdf']
    preuve_statut_apatride = ['file_token.pdf']

    carte_resident_longue_duree = ['file_token.pdf']
    carte_cire_sejour_illimite_etranger = ['file_token.pdf']
    carte_sejour_membre_ue = ['file_token.pdf']
    carte_sejour_permanent_membre_ue = ['file_token.pdf']

    carte_a_b_refugie = ['file_token.pdf']
    annexe_25_26_refugies_apatrides = ['file_token.pdf']
    attestation_immatriculation = ['file_token.pdf']
    carte_a_b = ['file_token.pdf']
    decision_protection_subsidiaire = ['file_token.pdf']
    decision_protection_temporaire = ['file_token.pdf']

    titre_sejour_3_mois_professionel = ['file_token.pdf']
    fiches_remuneration = ['file_token.pdf']
    titre_sejour_3_mois_remplacement = ['file_token.pdf']
    preuve_allocations_chomage_pension_indemnite = ['file_token.pdf']

    attestation_cpas = ['file_token.pdf']

    composition_menage_acte_naissance = ['file_token.pdf']
    acte_tutelle = ['file_token.pdf']
    composition_menage_acte_mariage = ['file_token.pdf']
    attestation_cohabitation_legale = ['file_token.pdf']
    carte_identite_parent = ['file_token.pdf']
    titre_sejour_longue_duree_parent = ['file_token.pdf']
    annexe_25_26_refugies_apatrides_decision_protection_parent = ['file_token.pdf']
    titre_sejour_3_mois_parent = ['file_token.pdf']
    fiches_remuneration_parent = ['file_token.pdf']
    attestation_cpas_parent = ['file_token.pdf']

    decision_bourse_cfwb = ['file_token.pdf']
    attestation_boursier = ['file_token.pdf']

    titre_identite_sejour_longue_duree_ue = ['file_token.pdf']
    titre_sejour_belgique = ['file_token.pdf']

    numero_compte_iban = 'BE43068999999501'
    iban_valide = True
    numero_compte_autre_format = '123456'
    code_bic_swift_banque = 'GKCCBEBB'
    prenom_titulaire_compte = 'John'
    nom_titulaire_compte = 'Doe'


class MotifRefusIdentityFactory(factory.Factory):
    class Meta:
        model = MotifRefusIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class ConditionComplementaireApprobationIdentityFactory(factory.Factory):
    class Meta:
        model = ConditionComplementaireApprobationIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class ComplementFormationIdentityFactory(factory.Factory):
    class Meta:
        model = ComplementFormationIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class _PropositionIdentityFactory(factory.Factory):
    class Meta:
        model = PropositionIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class PropositionFactory(factory.Factory):
    class Meta:
        model = Proposition
        abstract = False

    reference = factory.Iterator(REFERENCE_MEMORY_ITERATOR)
    entity_id = factory.SubFactory(_PropositionIdentityFactory)
    matricule_candidat = FuzzyText(length=10, chars=string.digits)
    formation_id = factory.SubFactory(FormationIdentityFactory)
    comptabilite = factory.SubFactory(_ComptabiliteFactory)

    creee_le = factory.Faker('past_datetime')
    modifiee_le = factory.Faker('past_datetime')

    bourse_double_diplome_id = factory.SubFactory(BourseIdentityFactory, uuid='a0e94dd5-3715-49a1-8953-8cc0f99372cb')
    bourse_internationale_id = factory.SubFactory(BourseIdentityFactory, uuid='c0e94dd5-3715-49a1-8953-8cc0f99372cb')
    bourse_erasmus_mundus_id = factory.SubFactory(BourseIdentityFactory, uuid='e0e94dd5-3715-49a1-8953-8cc0f99372cb')
    est_reorientation_inscription_externe = False
    est_modification_inscription_externe = False
    checklist_initiale = None
    checklist_actuelle = None
    poste_diplomatique = factory.SubFactory(
        PosteDiplomatiqueIdentityFactory,
        code=1,
    )

    class Params:
        est_bachelier_en_reorientation = factory.Trait(
            est_bachelier_belge=True,
            est_reorientation_inscription_externe=True,
            attestation_inscription_reguliere=['uuid-attestation_inscription_reguliere'],
        )
        est_bachelier_en_modification = factory.Trait(
            est_bachelier_belge=True,
            est_modification_inscription_externe=True,
            formulaire_modification_inscription=['uuid-formulaire_modification_inscription'],
        )
        est_confirmee = factory.Trait(
            statut=ChoixStatutPropositionGenerale.CONFIRMEE,
            checklist_initiale=factory.SubFactory(StatutsChecklistGeneraleFactory),
            checklist_actuelle=factory.SubFactory(StatutsChecklistGeneraleFactory),
        )
        est_refusee_par_fac_raison_libre = factory.Trait(
            autres_motifs_refus=['Ma raison'],
            certificat_refus_fac=['uuid-certificat_refus_fac'],
        )
        est_refusee_par_fac_raison_connue = factory.Trait(
            motifs_refus=[factory.SubFactory(MotifRefusIdentityFactory)],
            certificat_refus_fac=['uuid-certificat_refus_fac'],
        )
        est_approuvee_par_fac = factory.Trait(
            certificat_approbation_fac=['uuid-certificat_approbation_fac'],
            autre_formation_choisie_fac_id=factory.SubFactory(FormationIdentityFactory),
            avec_conditions_complementaires=True,
            conditions_complementaires_existantes=factory.List(
                params=[
                    ConditionComplementaireApprobationIdentityFactory(),
                    ConditionComplementaireApprobationIdentityFactory(),
                ]
            ),
            conditions_complementaires_libres=factory.List(
                params=[
                    factory.fuzzy.FuzzyText(),
                    factory.fuzzy.FuzzyText(),
                ]
            ),
            complements_formation=factory.List(
                params=[
                    ComplementFormationIdentityFactory(),
                    ComplementFormationIdentityFactory(),
                ]
            ),
            avec_complements_formation=True,
            commentaire_complements_formation=factory.fuzzy.FuzzyText(),
            nombre_annees_prevoir_programme=factory.fuzzy.FuzzyInteger(
                low=DUREE_MINIMALE_PROGRAMME,
                high=DUREE_MAXIMALE_PROGRAMME,
            ),
            nom_personne_contact_programme_annuel_annuel=factory.Faker('last_name'),
            email_personne_contact_programme_annuel_annuel=factory.Faker('email'),
            commentaire_programme_conjoint=factory.fuzzy.FuzzyText(),
        )

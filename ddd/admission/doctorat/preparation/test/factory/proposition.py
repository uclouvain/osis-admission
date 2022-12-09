# ##############################################################################
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
# ##############################################################################
import string
import uuid

import factory

from admission.ddd.admission.doctorat.preparation.domain.model._comptabilite import (
    Comptabilite,
)
from admission.ddd.admission.doctorat.preparation.domain.model._detail_projet import (
    DetailProjet,
    projet_non_rempli,
)
from admission.ddd.admission.doctorat.preparation.domain.model._experience_precedente_recherche import (
    aucune_experience_precedente_recherche,
)
from admission.ddd.admission.doctorat.preparation.domain.model._financement import (
    Financement,
    financement_non_rempli,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    BourseRecherche,
    ChoixAffiliationSport,
    ChoixLangueRedactionThese,
    ChoixSousDomaineSciences,
    ChoixStatutProposition,
    ChoixTypeAdmission,
    ChoixTypeCompteBancaire,
    ChoixTypeFinancement,
    TypeSituationAssimilation,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory


class _PropositionIdentityFactory(factory.Factory):
    class Meta:
        model = PropositionIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class _FinancementFactory(factory.Factory):
    class Meta:
        model = Financement
        abstract = False

    type = ChoixTypeFinancement.SELF_FUNDING
    duree_prevue = 10
    temps_consacre = 10


class _DetailProjetFactory(factory.Factory):
    class Meta:
        model = DetailProjet
        abstract = False

    titre = 'Mon projet'
    resume = factory.Faker('sentence')
    documents = factory.LazyFunction(lambda: [str(uuid.uuid4())])
    langue_redaction_these = ChoixLangueRedactionThese.FRENCH
    graphe_gantt = factory.LazyFunction(lambda: [str(uuid.uuid4())])
    proposition_programme_doctoral = factory.LazyFunction(lambda: [str(uuid.uuid4())])


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


class _PropositionFactory(factory.Factory):
    class Meta:
        model = Proposition
        abstract = False

    entity_id = factory.SubFactory(_PropositionIdentityFactory)
    reference = factory.Faker('pystr_format', string_format='2#-300###')
    matricule_candidat = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    doctorat_id = factory.SubFactory(FormationIdentityFactory)
    statut = ChoixStatutProposition.IN_PROGRESS
    projet = factory.SubFactory(_DetailProjetFactory)
    creee_le = factory.Faker('past_datetime')
    financement = factory.SubFactory(_FinancementFactory)
    experience_precedente_recherche = aucune_experience_precedente_recherche
    modifiee_le = factory.Faker('past_datetime')
    comptabilite = factory.SubFactory(_ComptabiliteFactory)
    reponses_questions_specifiques = {
        '06de0c3d-3c06-4c93-8eb4-c8648f04f140': 'My response 1',
        '06de0c3d-3c06-4c93-8eb4-c8648f04f142': 'My response 2',
        '06de0c3d-3c06-4c93-8eb4-c8648f04f143': 'My response 3',
    }
    curriculum = ['file_token.pdf']


class PropositionAdmissionSC3DPMinimaleFactory(_PropositionFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP')
    type_admission = ChoixTypeAdmission.ADMISSION
    commission_proximite = ChoixSousDomaineSciences.BIOLOGY
    doctorat_id = factory.SubFactory(FormationIdentityFactory, sigle='SC3DP', annee=2020)
    matricule_candidat = '0000000001'


class PropositionAdmissionECGE3DPMinimaleFactory(_PropositionFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-ECGE3DP')
    type_admission = ChoixTypeAdmission.ADMISSION
    doctorat_id = factory.SubFactory(FormationIdentityFactory, sigle='ECGE3DP', annee=2020)
    matricule_candidat = '0123456789'


class PropositionAdmissionESP3DPMinimaleFactory(_PropositionFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-ESP3DP')
    type_admission = ChoixTypeAdmission.ADMISSION
    doctorat_id = factory.SubFactory(FormationIdentityFactory, sigle='ESP3DP', annee=2020)
    matricule_candidat = '0123456789'


class PropositionAdmissionSC3DPMinimaleAnnuleeFactory(PropositionAdmissionSC3DPMinimaleFactory):
    statut = ChoixStatutProposition.CANCELLED
    matricule_candidat = '0123456789'


class PropositionAdmissionSC3DPMinimaleSansDetailProjetFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-no-project')
    projet = projet_non_rempli


class PropositionAdmissionSC3DPMinimaleSansFinancementFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-no-financement')
    financement = financement_non_rempli


class PropositionAdmissionSC3DPMinimaleSansCotutelleFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-cotutelle-indefinie')


class PropositionAdmissionSC3DPMinimaleCotutelleSansPromoteurExterneFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-cotutelle-sans-promoteur-externe')


class PropositionAdmissionSC3DPMinimaleCotutelleAvecPromoteurExterneFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-cotutelle-avec-promoteur-externe')


class PropositionPreAdmissionSC3DPMinimaleFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-pre-admission')
    type_admission = ChoixTypeAdmission.PRE_ADMISSION


class PropositionAdmissionSC3DPAvecMembresFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-promoteur-membre')


class PropositionAdmissionSC3DPAvecMembresEtCotutelleFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-promoteur-membre-cotutelle')
    matricule_candidat = 'candidat'


class PropositionAdmissionSC3DPAvecMembresInvitesFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-membres-invites')


class PropositionAdmissionSC3DPSansPromoteurFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-sans-promoteur')


class PropositionAdmissionSC3DPSansPromoteurReferenceFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-sans-promoteur-reference')


class PropositionAdmissionSC3DPSansMembreCAFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-sans-membre_CA')
    matricule_candidat = '0123456789'


class PropositionAdmissionSC3DPAvecPromoteurDejaApprouveFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-promoteur-deja-approuve')


class PropositionAdmissionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactory(
    PropositionAdmissionSC3DPMinimaleFactory
):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-promoteur-refus-membre-deja-approuve')
    matricule_candidat = 'candidat'


class PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-promoteurs-membres-deja-approuves')
    matricule_candidat = '0123456789'
    statut = ChoixStatutProposition.SIGNING_IN_PROGRESS


class PropositionPreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(
    PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-pre-SC3DP-promoteurs-membres-deja-approuves')
    type_admission = ChoixTypeAdmission.PRE_ADMISSION
    financement = factory.SubFactory(
        _FinancementFactory,
        type=ChoixTypeFinancement.SEARCH_SCHOLARSHIP,
        autre_bourse_recherche=BourseRecherche.ARC.name,
    )

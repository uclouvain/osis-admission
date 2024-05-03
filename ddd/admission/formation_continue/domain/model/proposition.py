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
from typing import Optional, Dict, List

import attr
from django.utils.timezone import now
from django.utils.translation import gettext_noop as __

from admission.ddd.admission.domain.model._profil_candidat import ProfilCandidat
from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.formation_continue.domain.model._adresse import Adresse
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
    ChoixInscriptionATitre,
    ChoixTypeAdresseFacturation,
    ChoixMoyensDecouverteFormation,
    ChoixEdition,
    ChoixMotifAttente,
    ChoixMotifRefus,
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_continue.domain.model.statut_checklist import (
    StatutsChecklistContinue,
    StatutChecklist,
)
from admission.ddd.admission.formation_continue.domain.validator.validator_by_business_action import (
    InformationsComplementairesValidatorList,
    ChoixFormationValidatorList,
)
from admission.ddd.admission.formation_continue.domain.validator.validator_by_business_actions import (
    MettreEnAttenteValidatorList,
    ApprouverParFacValidatorList,
    RefuserPropositionValidatorList,
    AnnulerPropositionValidatorList,
    ApprouverPropositionValidatorList,
    CloturerPropositionValidatorList,
)
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from ddd.logic.formation_catalogue.formation_continue.dtos.informations_specifiques import InformationsSpecifiquesDTO
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
    annee_calculee: Optional[int] = None
    pot_calcule: Optional[AcademicCalendarTypes] = None
    statut: ChoixStatutPropositionContinue = ChoixStatutPropositionContinue.EN_BROUILLON
    auteur_derniere_modification: str = ''

    creee_le: Optional[datetime.datetime] = None
    modifiee_le: Optional[datetime.datetime] = None
    soumise_le: Optional[datetime.datetime] = None

    reponses_questions_specifiques: Dict = attr.Factory(dict)

    curriculum: List[str] = attr.Factory(list)
    equivalence_diplome: List[str] = attr.Factory(list)
    copie_titre_sejour: List[str] = attr.Factory(list)
    elements_confirmation: Dict[str, str] = attr.Factory(dict)

    inscription_a_titre: Optional[ChoixInscriptionATitre] = None
    nom_siege_social: Optional[str] = ''
    numero_unique_entreprise: Optional[str] = ''
    numero_tva_entreprise: Optional[str] = ''
    adresse_mail_professionnelle: Optional[str] = ''
    type_adresse_facturation: Optional[ChoixTypeAdresseFacturation] = None
    adresse_facturation: Optional[Adresse] = None

    documents_additionnels: List[str] = attr.Factory(list)

    motivations: Optional[str] = ''
    moyens_decouverte_formation: List[ChoixMoyensDecouverteFormation] = attr.Factory(list)

    checklist_initiale: Optional[StatutsChecklistContinue] = None
    checklist_actuelle: Optional[StatutsChecklistContinue] = None

    profil_soumis_candidat: Optional[ProfilCandidat] = None

    marque_d_interet: Optional[bool] = None
    edition: Optional[ChoixEdition] = None
    en_ordre_de_paiement: Optional[bool] = None
    droits_reduits: Optional[bool] = None
    paye_par_cheque_formation: Optional[bool] = None
    cep: Optional[bool] = None
    etalement_des_paiments: Optional[bool] = None
    etalement_de_la_formation: Optional[bool] = None
    valorisation_des_acquis_d_experience: Optional[bool] = None
    a_presente_l_epreuve_d_evaluation: Optional[bool] = None
    a_reussi_l_epreuve_d_evaluation: Optional[bool] = None
    diplome_produit: Optional[bool] = None
    intitule_du_tff: Optional[str] = ''

    # Decision
    decision_dernier_mail_envoye_le: Optional[datetime.datetime] = None
    decision_dernier_mail_envoye_par: Optional[str] = ''
    motif_de_mise_en_attente: Optional[ChoixMotifAttente] = None
    motif_de_mise_en_attente_autre: Optional[str] = ''
    condition_d_approbation_par_la_faculte: Optional[str] = ''
    motif_de_refus: Optional[ChoixMotifRefus] = None
    motif_de_refus_autre: Optional[str] = ''
    motif_d_annulation: Optional[str] = ''

    def modifier_choix_formation(
        self,
        formation_id: FormationIdentity,
        reponses_questions_specifiques: Dict,
        motivations: str,
        moyens_decouverte_formation: List[str],
        marque_d_interet: Optional[bool],
    ):
        self.formation_id = formation_id
        self.reponses_questions_specifiques = reponses_questions_specifiques
        self.motivations = motivations
        self.moyens_decouverte_formation = [
            ChoixMoyensDecouverteFormation[moyen] for moyen in moyens_decouverte_formation
        ]
        self.marque_d_interet = marque_d_interet
        self.auteur_derniere_modification = self.matricule_candidat

    def supprimer(self):
        self.statut = ChoixStatutPropositionContinue.ANNULEE
        self.auteur_derniere_modification = self.matricule_candidat

    def soumettre(
        self,
        formation_id: FormationIdentity,
        pool: 'AcademicCalendarTypes',
        elements_confirmation: Dict[str, str],
        profil_candidat_soumis: ProfilCandidat,
    ):
        self.statut = ChoixStatutPropositionContinue.CONFIRMEE
        self.annee_calculee = formation_id.annee
        self.formation_id = formation_id
        self.pot_calcule = pool
        self.elements_confirmation = elements_confirmation
        self.soumise_le = now()
        self.auteur_derniere_modification = self.matricule_candidat
        self.profil_soumis_candidat = profil_candidat_soumis

    def completer_curriculum(
        self,
        curriculum: List[str],
        equivalence_diplome: List[str],
        reponses_questions_specifiques: Dict,
    ):
        self.curriculum = curriculum
        self.equivalence_diplome = equivalence_diplome
        self.reponses_questions_specifiques = reponses_questions_specifiques
        self.auteur_derniere_modification = self.matricule_candidat

    def completer_informations_complementaires(
        self,
        inscription_a_titre: Optional[str],
        nom_siege_social: Optional[str],
        numero_unique_entreprise: Optional[str],
        numero_tva_entreprise: Optional[str],
        adresse_mail_professionnelle: Optional[str],
        type_adresse_facturation: Optional[str],
        adresse_facturation_rue: Optional[str],
        adresse_facturation_numero_rue: Optional[str],
        adresse_facturation_code_postal: Optional[str],
        adresse_facturation_ville: Optional[str],
        adresse_facturation_pays: Optional[str],
        adresse_facturation_destinataire: Optional[str],
        adresse_facturation_boite_postale: Optional[str],
        reponses_questions_specifiques: Dict,
        copie_titre_sejour: List[str],
        documents_additionnels: List[str],
    ):
        self.inscription_a_titre = ChoixInscriptionATitre[inscription_a_titre] if inscription_a_titre else None
        self.nom_siege_social = nom_siege_social or ''
        self.numero_unique_entreprise = numero_unique_entreprise or ''
        self.numero_tva_entreprise = numero_tva_entreprise or ''
        self.adresse_mail_professionnelle = adresse_mail_professionnelle or ''
        self.type_adresse_facturation = (
            ChoixTypeAdresseFacturation[type_adresse_facturation] if type_adresse_facturation else None
        )
        self.adresse_facturation = (
            Adresse(
                rue=adresse_facturation_rue or '',
                numero_rue=adresse_facturation_numero_rue or '',
                code_postal=adresse_facturation_code_postal or '',
                ville=adresse_facturation_ville or '',
                pays=adresse_facturation_pays or '',
                destinataire=adresse_facturation_destinataire,
                boite_postale=adresse_facturation_boite_postale,
            )
            if self.type_adresse_facturation == ChoixTypeAdresseFacturation.AUTRE
            else None
        )
        self.reponses_questions_specifiques = reponses_questions_specifiques
        self.copie_titre_sejour = copie_titre_sejour
        self.documents_additionnels = documents_additionnels
        self.auteur_derniere_modification = self.matricule_candidat

    def verifier_informations_complementaires(self):
        """Vérification de la validité des informations complémentaires."""
        InformationsComplementairesValidatorList(self.inscription_a_titre).validate()

    def verifier_choix_de_formation(self, informations_specifiques_formation: Optional[InformationsSpecifiquesDTO]):
        """Vérification de la validité des informations saisies dans l'onglet du choix de formation."""
        ChoixFormationValidatorList(
            motivations=self.motivations,
            moyens_decouverte_formation=self.moyens_decouverte_formation,
            informations_specifiques_formation=informations_specifiques_formation,
        ).validate()

    def mettre_en_attente(
        self,
        gestionnaire: str,
        motif: str,
        autre_motif: Optional[str] = '',
    ):
        MettreEnAttenteValidatorList(
            checklist_statut=self.checklist_actuelle.decision,
        ).validate()

        self.statut = ChoixStatutPropositionContinue.EN_ATTENTE
        self.checklist_actuelle.decision = StatutChecklist(
            statut=ChoixStatutChecklist.GEST_EN_COURS,
            libelle=__('On hold'),
            extra={'en_cours': "on_hold"},
        )
        self.decision_dernier_mail_envoye_le = now()
        self.decision_dernier_mail_envoye_par = gestionnaire
        self.motif_de_mise_en_attente = ChoixMotifAttente[motif]
        self.motif_de_mise_en_attente_autre = autre_motif
        self.auteur_derniere_modification = gestionnaire

    def approuver_par_fac(
        self,
        gestionnaire: str,
        condition: str,
    ):
        ApprouverParFacValidatorList(
            checklist_statut=self.checklist_actuelle.decision,
        ).validate()

        self.checklist_actuelle.decision = StatutChecklist(
            statut=ChoixStatutChecklist.GEST_EN_COURS,
            libelle=__('Fac approval'),
            extra={'en_cours': "fac_approval"},
        )
        self.decision_dernier_mail_envoye_le = now()
        self.decision_dernier_mail_envoye_par = gestionnaire
        self.condition_d_approbation_par_la_faculte = condition
        self.statut = ChoixStatutPropositionContinue.CONFIRMEE
        self.auteur_derniere_modification = gestionnaire

    def refuser_proposition(
        self,
        gestionnaire: str,
        motif: str,
        autre_motif: Optional[str] = '',
    ):
        RefuserPropositionValidatorList(
            checklist_statut=self.checklist_actuelle.decision,
        ).validate()

        self.statut = ChoixStatutPropositionContinue.INSCRIPTION_REFUSEE
        self.checklist_actuelle.decision = StatutChecklist(
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            libelle=__('Denied'),
            extra={'blocage': "denied"},
        )
        self.decision_dernier_mail_envoye_le = now()
        self.decision_dernier_mail_envoye_par = gestionnaire
        self.motif_de_refus = ChoixMotifRefus[motif]
        self.motif_de_refus_autre = autre_motif
        self.auteur_derniere_modification = gestionnaire

    def annuler_proposition(
        self,
        gestionnaire: str,
        motif: str,
    ):
        AnnulerPropositionValidatorList(
            checklist_statut=self.checklist_actuelle.decision,
        ).validate()

        self.statut = ChoixStatutPropositionContinue.ANNULEE_PAR_GESTIONNAIRE
        self.checklist_actuelle.decision = StatutChecklist(
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            libelle=__('Canceled'),
            extra={'blocage': "canceled"},
        )
        self.decision_dernier_mail_envoye_le = now()
        self.decision_dernier_mail_envoye_par = gestionnaire
        self.motif_d_annulation = motif
        self.auteur_derniere_modification = gestionnaire

    def approuver_proposition(
        self,
        gestionnaire: str,
    ):
        ApprouverPropositionValidatorList(
            checklist_statut=self.checklist_actuelle.decision,
        ).validate()

        self.statut = ChoixStatutPropositionContinue.INSCRIPTION_AUTORISEE
        self.checklist_actuelle.decision = StatutChecklist(
            statut=ChoixStatutChecklist.GEST_REUSSITE,
            libelle=__('Validated'),
        )
        self.decision_dernier_mail_envoye_le = now()
        self.decision_dernier_mail_envoye_par = gestionnaire
        self.auteur_derniere_modification = gestionnaire

    def cloturer_proposition(
        self,
        gestionnaire: str,
    ):
        CloturerPropositionValidatorList(
            checklist_statut=self.checklist_actuelle.decision,
        ).validate()

        self.statut = ChoixStatutPropositionContinue.CLOTUREE
        self.checklist_actuelle.decision = StatutChecklist(
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            libelle=__('Validated'),
            extra={'blocage': "closed"},
        )
        self.auteur_derniere_modification = gestionnaire

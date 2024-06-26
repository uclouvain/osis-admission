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

import factory

from admission.ddd.admission.dtos import AdressePersonnelleDTO
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    StatutEmplacementDocument,
    StatutReclamationEmplacementDocument,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.admission.formation_continue.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.formation_continue.dtos import PropositionDTO
from admission.ddd.admission.formation_continue.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.formation_continue.test.factory.proposition import (
    PropositionFactory,
    _PropositionIdentityFactory,
)
from admission.ddd.admission.repository.i_proposition import formater_reference
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.infrastructure.admission.formation_continue.domain.service.in_memory.formation import (
    FormationContinueInMemoryTranslator,
)
from admission.infrastructure.admission.repository.in_memory.proposition import GlobalPropositionInMemoryRepository
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


@dataclass
class _Candidat:
    prenom: str
    nom: str
    nationalite: str
    nationalite_ue: bool
    noma_candidat: str = ''
    adresse_email_candidat: str = ''
    langue_contact_candidat: str = ''


class PropositionInMemoryRepository(
    GlobalPropositionInMemoryRepository,
    InMemoryGenericRepository,
    IPropositionRepository,
):
    candidats = {
        "0123456789": _Candidat("Jean", "Dupont", "France", True, '476284', 'jdupont@example.be'),
        "0000000001": _Candidat("Michel", "Durand", "Belgique", True, '154893', 'mdurand@example.be'),
        "candidat": _Candidat("Pierre", "Dupond", "Belgique", True, '545805', 'pdupond@example.be'),
        "candidat_checklist": _Candidat("Pierre", "Dupond", "Belgique", True, '545805', 'pdupond@example.be'),
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
            returned = filter(lambda p: p.matricule == matricule_candidat, returned)
        if entity_ids:  # pragma: no cover
            returned = filter(lambda p: p.entity_id in entity_ids, returned)
        return list(returned)

    @classmethod
    def reset(cls):
        cls.entities = [
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-USCC4'),
                matricule_candidat='0123456789',
                formation_id=FormationIdentityFactory(sigle="USCC4", annee=2020),
                documents_demandes={
                    'CURRICULUM.CURRICULUM': {
                        'last_actor': '00321234',
                        'reason': 'Le document est à mettre à jour.',
                        'type': TypeEmplacementDocument.NON_LIBRE.name,
                        'last_action_at': '2023-01-02T00:00:00',
                        'status': StatutEmplacementDocument.RECLAME.name,
                        'requested_at': '2023-01-02T00:00:00',
                        'deadline_at': '2023-01-19',
                        'automatically_required': False,
                        'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
                    },
                    'LIBRE_CANDIDAT.26de0c3d-3c06-4c93-8eb4-c8648f04f146': {
                        'last_actor': '00987890',
                        'reason': 'Ce nouveau document pourrait être intéressant.',
                        'type': TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
                        'last_action_at': '2023-01-03T00:00:00',
                        'status': StatutEmplacementDocument.RECLAME.name,
                        'requested_at': '2023-01-03T00:00:00',
                        'deadline_at': '2023-01-19',
                        'automatically_required': False,
                        'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT.name,
                    },
                },
                curriculum=['file1.pdf'],
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-USCC3'),
                matricule_candidat='0000000001',
                formation_id=FormationIdentityFactory(sigle="USCC3", annee=2020),
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-USCC32'),
                matricule_candidat='0000000001',
                formation_id=FormationIdentityFactory(sigle="USCC3", annee=2022),
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-USCC42'),
                matricule_candidat='0123456789',
                formation_id=FormationIdentityFactory(sigle="USCC4", annee=2020),
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-USCC43'),
                matricule_candidat='0123456789',
                formation_id=FormationIdentityFactory(sigle="USCC4", annee=2020),
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-USCC1'),
                matricule_candidat='0000000001',
                formation_id=FormationIdentityFactory(sigle="USCC1", annee=2020),
                reponses_questions_specifiques={
                    '26de0c3d-3c06-4c93-8eb4-c8648f04f140': 'My response 0',
                    '26de0c3d-3c06-4c93-8eb4-c8648f04f143': 'My response 3',
                    '26de0c3d-3c06-4c93-8eb4-c8648f04f144': 'My response 4',
                    '26de0c3d-3c06-4c93-8eb4-c8648f04f145': 'My response 5',
                },
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-USCC2'),
                matricule_candidat='candidat_checklist',
                formation_id=FormationIdentityFactory(sigle="USCC2", annee=2020),
                est_confirmee=True,
            ),
            PropositionFactory(
                entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-USCC22'),
                matricule_candidat='candidat_checklist',
                formation_id=FormationIdentityFactory(sigle="USCC2", annee=2020),
                est_acceptee=True,
            ),
        ]

    @classmethod
    def get_dto(cls, entity_id: 'PropositionIdentity') -> 'PropositionDTO':
        return cls._load_dto(cls.get(entity_id))

    @classmethod
    def _load_dto(cls, proposition: Proposition) -> PropositionDTO:
        candidat = cls.candidats[proposition.matricule_candidat]
        formation = FormationContinueInMemoryTranslator.get_dto(
            proposition.formation_id.sigle,
            proposition.formation_id.annee,
        )
        infos_specifiques_iufc = FormationContinueInMemoryTranslator.get_informations_specifiques_dto(
            entity_id=proposition.formation_id,
        )

        return PropositionDTO(
            uuid=proposition.entity_id.uuid,
            reference=formater_reference(
                reference=proposition.reference,
                nom_campus_inscription=formation.campus_inscription.nom,
                sigle_entite_gestion=formation.sigle_entite_gestion,
                annee=proposition.formation_id.annee,
            ),
            langue_contact_candidat=candidat.langue_contact_candidat,
            matricule_candidat=proposition.matricule_candidat,
            prenom_candidat=candidat.prenom,
            nom_candidat=candidat.nom,
            pays_nationalite_candidat=candidat.nationalite,
            pays_nationalite_ue_candidat=candidat.nationalite_ue,
            nom_pays_nationalite_candidat=candidat.nationalite,
            noma_candidat=candidat.noma_candidat,
            adresse_email_candidat=candidat.adresse_email_candidat,
            statut=proposition.statut.name,
            creee_le=proposition.creee_le,
            modifiee_le=proposition.modifiee_le,
            erreurs=[],
            formation=formation,
            annee_calculee=proposition.annee_calculee,
            pot_calcule=proposition.pot_calcule and proposition.pot_calcule.name or '',
            soumise_le=None,
            date_fin_pot=None,
            reponses_questions_specifiques=proposition.reponses_questions_specifiques,
            equivalence_diplome=proposition.equivalence_diplome,
            curriculum=proposition.curriculum,
            copie_titre_sejour=proposition.copie_titre_sejour,
            inscription_a_titre=proposition.inscription_a_titre,
            nom_siege_social=proposition.nom_siege_social,
            numero_unique_entreprise=proposition.numero_unique_entreprise,
            numero_tva_entreprise=proposition.numero_tva_entreprise,
            adresse_mail_professionnelle=proposition.adresse_mail_professionnelle,
            type_adresse_facturation=proposition.type_adresse_facturation,
            adresse_facturation=proposition.adresse_facturation
            and AdressePersonnelleDTO(
                rue=proposition.adresse_facturation.rue,
                numero_rue=proposition.adresse_facturation.numero_rue,
                code_postal=proposition.adresse_facturation.code_postal,
                ville=proposition.adresse_facturation.ville,
                pays=proposition.adresse_facturation.pays,
                destinataire=proposition.adresse_facturation.destinataire,
                boite_postale=proposition.adresse_facturation.boite_postale,
                nom_pays='',
            ),
            elements_confirmation=proposition.elements_confirmation,
            pdf_recapitulatif=[],
            documents_additionnels=proposition.documents_additionnels,
            motivations=proposition.motivations,
            moyens_decouverte_formation=[way.name for way in proposition.moyens_decouverte_formation],
            aide_a_la_formation=infos_specifiques_iufc.aide_a_la_formation if infos_specifiques_iufc else None,
            inscription_au_role_obligatoire=infos_specifiques_iufc.inscription_au_role_obligatoire
            if infos_specifiques_iufc
            else None,
            etat_formation=infos_specifiques_iufc.etat.name if infos_specifiques_iufc else '',
            documents_demandes=proposition.documents_demandes,
            documents_libres_sic_uclouvain=cls.documents_libres_sic_uclouvain.get(proposition.entity_id.uuid, []),
            documents_libres_fac_uclouvain=cls.documents_libres_fac_uclouvain.get(proposition.entity_id.uuid, []),
            marque_d_interet=proposition.marque_d_interet,
            edition=proposition.edition,
            en_ordre_de_paiement=proposition.en_ordre_de_paiement,
            droits_reduits=proposition.droits_reduits,
            paye_par_cheque_formation=proposition.paye_par_cheque_formation,
            cep=proposition.cep,
            etalement_des_paiments=proposition.etalement_des_paiments,
            etalement_de_la_formation=proposition.etalement_de_la_formation,
            valorisation_des_acquis_d_experience=proposition.valorisation_des_acquis_d_experience,
            a_presente_l_epreuve_d_evaluation=proposition.a_presente_l_epreuve_d_evaluation,
            a_reussi_l_epreuve_d_evaluation=proposition.a_reussi_l_epreuve_d_evaluation,
            diplome_produit=proposition.diplome_produit,
            intitule_du_tff=proposition.intitule_du_tff,
            date_changement_statut=None,
            candidat_a_plusieurs_demandes=False,
            decision_dernier_mail_envoye_le=proposition.decision_dernier_mail_envoye_le,
            decision_dernier_mail_envoye_par=proposition.decision_dernier_mail_envoye_par,
            motif_de_mise_en_attente=proposition.motif_de_mise_en_attente,
            motif_de_mise_en_attente_autre=proposition.motif_de_mise_en_attente_autre,
            condition_d_approbation_par_la_faculte=proposition.condition_d_approbation_par_la_faculte,
            motif_de_refus=proposition.motif_de_refus,
            motif_de_refus_autre=proposition.motif_de_refus_autre,
            motif_d_annulation=proposition.motif_d_annulation,
            profil_soumis_candidat=proposition.profil_soumis_candidat,
        )

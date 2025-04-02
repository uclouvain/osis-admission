import attr

from admission.ddd.admission.formation_continue.domain.model.proposition import PropositionIdentity
from osis_common.ddd.interface import Event


@attr.dataclass(frozen=True, slots=True, kw_only=True)
class PropositionFormationContinueSoumiseEvent(Event):
    entity_id: 'PropositionIdentity'
    matricule: str


@attr.dataclass(frozen=True, slots=True, kw_only=True)
class FormationDuDossierAdmissionFCModifieeEvent(Event):
    entity_id: 'PropositionIdentity'
    matricule: str


@attr.dataclass(frozen=True, slots=True, kw_only=True)
class PropositionFormationContinueValideeEvent(Event):
    entity_id: 'PropositionIdentity'
    matricule: str

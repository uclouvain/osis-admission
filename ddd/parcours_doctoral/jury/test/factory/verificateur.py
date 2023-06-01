import uuid

import factory

from admission.ddd.parcours_doctoral.jury.domain.model.verificateurs import Verificateur, VerificateurIdentity
from ddd.logic.learning_unit.tests.factory.ucl_entity import UclEntityIdentityFactory


class VerificateurIdentityFactory(factory.Factory):
    class Meta:
        model = VerificateurIdentity
        abstract = False

    code = 'FOO'


class VerificateurFactory(factory.Factory):
    class Meta:
        model = Verificateur
        abstract = False

    entity_id = factory.SubFactory(VerificateurIdentityFactory, code=factory.SelfAttribute('..entite_ucl_id.code'))
    entite_ucl_id = factory.SubFactory(UclEntityIdentityFactory)
    matricule = None

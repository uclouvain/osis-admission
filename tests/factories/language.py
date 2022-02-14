import factory

from base.tests.factories.person import PersonFactory
from reference.tests.factories.language import LanguageFactory


class LanguageKnowledgeFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'osis_profile.LanguageKnowledge'

    person = factory.SubFactory(PersonFactory)
    language = factory.SubFactory(LanguageFactory)

# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
import importlib
import inspect
import logging
from pathlib import Path
from typing import List

from django.conf import settings
from django.urls import include, path
from django.views import View

logger = logging.getLogger(__name__)

app_name = 'admission'


class FileRouter:
    def __call__(self, filepath: str):
        patterns = self.patterns_from_tree(Path(settings.BASE_DIR) / filepath)
        self._dedupe_namespaces(patterns)
        return patterns

    @staticmethod
    def _patterns_from_views(module, stem) -> List:
        """
        Gather patterns from a module's views.

        Views must implement `django.views.generic.View` (your mixins must not!) and
        be referenced in the `__all__` variable of a module to be picked.

        In a view, you can specify a `urlpatterns` attribute:
          - if it's a string, it will be taken as the name of the view and the url pattern
                class MyView(View):
                    urlpatterns = 'something'
            will give path('something', MyView.as_view(), name='something')
          - if it's a dict, keys will be names, and values url patterns
                class MyView(View):
                    urlpatterns = {'something': 'something/<int:pk>', 'add': 'new'}
           will give:
                `path('something/<int:pk>', MyView.as_view(), name='something'),`
                `path('new', MyView.as_view(), name='add'),`
          - if no attribute is set, and the view is alone in the module, the module name will be taken
        """
        subpatterns = []
        for view_name in getattr(module, '__all__', []):
            view_class = getattr(module, view_name)
            if not inspect.isclass(view_class) or not issubclass(view_class, View):
                continue

            view_urlpatterns = getattr(view_class, 'urlpatterns', stem)
            if isinstance(view_urlpatterns, str):
                view_urlpatterns = {view_urlpatterns: view_urlpatterns}

            for name, url in view_urlpatterns.items():
                subpatterns.append(
                    path(url, view_class.as_view(), name=name),
                )
        return subpatterns

    def patterns_from_tree(self, start_dir: Path) -> List:
        """
        Create urlpatterns from a directory structure.

        By default, a package is considered a namespace, and a module with one view a pattern,
        if a module has multiple views, it will also be considered a namespace.

        You can alter this behavior by setting `__namespace__ = False` in a package's __init__.py
        or in a module to disable producing a namespace. You can set `__namespace__ = 'foo'` to set the
        namespace name, otherwise the package name or the module name will be picked.

        You can set the url pattern for the package or module, for example:

         - `__namespace__ = {'foo': '<uuid:uuid>'}` -> `path('<uuid:uuid>/', include((subpatterns_from_views, 'foo')),`
         - `__namespace__ = 'bar' -> `path('bar', include((subpatterns_from_views, 'bar')),`
         - `__namespace__ = {'': 'foobar' -> `path('foobar', include((subpatterns_from_views, '')),`
         - `__namespace__ = False -> `path('', include((subpatterns_from_views, '')),`
        """
        patterns = []

        # Iterate on files in the tree
        for entry in start_dir.iterdir():
            entry_name = entry.stem.replace('_', '-')

            if entry.is_file() and entry.stem != '__init__':
                # File is a module
                module = importlib.import_module(
                    str(entry.relative_to(settings.BASE_DIR)).replace(".py", "").replace("/", ".")
                )
                views = getattr(module, '__all__', [])
                if len(views) > 1 and getattr(module, '__namespace__', True):
                    # Module contains multiple views
                    subpatterns = self._patterns_from_views(module, entry_name)
                    namespaces = getattr(module, '__namespace__', entry_name)
                    if isinstance(namespaces, str):
                        namespaces = {namespaces: namespaces}
                    for namespace, url in namespaces.items():
                        patterns.append(
                            path(url + "/", include((subpatterns.copy(), namespace))),
                        )
                else:
                    # Module contains a single view
                    subpatterns = self._patterns_from_views(module, entry_name)
                    patterns += subpatterns

            elif entry.is_dir() and entry.name != "__pycache__":
                # Directory is a package
                package = importlib.import_module(str(entry.relative_to(settings.BASE_DIR)).replace("/", "."))

                subpatterns = self.patterns_from_tree(entry)
                if subpatterns:
                    namespaces = getattr(package, '__namespace__', entry_name) or ''
                    if isinstance(namespaces, str):
                        namespaces = {namespaces: namespaces}
                    for namespace, url in namespaces.items():
                        if namespace:
                            patterns.append(
                                path(url + "/", include((subpatterns.copy(), namespace))),
                            )
                        else:
                            patterns += subpatterns
        return patterns

    def _dedupe_namespaces(self, patterns, parents=(), namespaces=None):
        """Silence the `urls.W005` warning by merging the duplicated namespaces"""
        namespaces = {} if namespaces is None else namespaces
        to_remove = []
        for pattern in patterns:
            namespace = getattr(pattern, 'namespace', None)
            current = parents
            if namespace is not None:
                current += (namespace,)
                self._dedupe_namespaces(pattern.url_patterns, current, namespaces)
                # If namespace is already referenced, update its list in place, and tag it to be removed
                namespace_name = ':'.join(current)
                if namespace_name not in namespaces:
                    namespaces[namespace_name] = pattern.url_patterns
                else:
                    namespaces[namespace_name].extend(pattern.url_patterns)
                    to_remove.append(pattern)
        for item in to_remove:
            patterns.remove(item)

    def debug(self, patterns, depth=0):  # pragma: no cover
        """
        To debug the current urls configuration, add to your settings:
        LOGGING['loggers']['admission.urls'] = {
            'handlers': ['console'],
            'level': 'DEBUG',
        }
        """
        msg: str = ''
        line_prefix = '    '
        for p in patterns:
            if hasattr(p, 'namespace'):
                msg += line_prefix * depth
                msg += f"path('{p.pattern.regex.pattern}', include(([\n"
                msg += self.debug(p.url_patterns, depth + 1)
                msg += line_prefix * depth
                msg += f"], '{p.namespace}')),\n"
            else:
                msg += line_prefix * depth
                msg += "path('{url}', {view_name}.as_view(), name='{name}'),\n".format(
                    url=p.pattern.regex.pattern,
                    view_name=p.callback.view_class.__name__,
                    name=p.name,
                )
        return msg


file_router = FileRouter()
urlpatterns = file_router('admission/views')

if settings.DEBUG:
    logger.debug("\n" + file_router.debug(urlpatterns))

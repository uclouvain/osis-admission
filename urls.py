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

from django.conf import settings
from django.urls import include, path
from django.views import View

logger = logging.getLogger(__name__)

app_name = 'admission'


def _patterns_from_views(module, stem):
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


def patterns_from_tree(start_dir: Path):
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

    for entry in start_dir.iterdir():
        entry_name = entry.stem.replace('_', '-')
        if entry.is_file() and entry.stem != '__init__':
            # File is a module
            module = importlib.import_module(str(entry).replace(".py", "").replace("/", "."))
            views = getattr(module, '__all__', [])
            if len(views) > 1 and getattr(module, '__namespace__', True):
                # Module contains multiple views
                subpatterns = _patterns_from_views(module, entry_name)
                namespaces = getattr(module, '__namespace__', entry_name)
                if isinstance(namespaces, str):
                    namespaces = {namespaces: namespaces}
                for namespace, url in namespaces.items():
                    patterns.append(
                        path(url + "/", include((subpatterns, namespace))),
                    )
            else:
                # Module contains a single view
                subpatterns = _patterns_from_views(module, entry_name)
                patterns += subpatterns

        elif entry.is_dir() and entry.name != "__pycache__":
            # Directory is a package
            package = importlib.import_module(str(entry).replace("/", "."))

            subpatterns = patterns_from_tree(entry)
            if subpatterns:
                namespaces = getattr(package, '__namespace__', entry_name) or ''
                if isinstance(namespaces, str):
                    namespaces = {namespaces: namespaces}
                for namespace, url in namespaces.items():
                    patterns.append(
                        path(url + "/", include((subpatterns, namespace))),
                    )
    return patterns


urlpatterns = patterns_from_tree(Path('admission/views'))

if settings.DEBUG:

    def _debug(patterns, depth=0):
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
                msg += _debug(p.url_patterns, depth + 1)
                msg += line_prefix * depth
                msg += f"], '{p.namespace}')),\n"
            else:
                msg += line_prefix * depth
                msg += (
                    f"path('{p.pattern.regex.pattern}', {p.callback.view_class.__name__}.as_view(), name='{p.name}'),\n"
                )
        return msg

    logger.debug("\n" + _debug(urlpatterns))

# BASEDIR is set by <lang>/conf.py
"""
Use "-D language=<LANG>" option to build a localized sphinx document.
For example::
    sphinx-build -D language=ja -b html . _build/html
This conf.py does:
- Specify `locale_dirs` and `gettext_compact`.
- Overrides source directory as 'sphinx/doc/`.
"""
import os
from sphinx.util.pycompat import execfile_

BASEDIR = os.path.dirname(os.path.abspath(__file__))

execfile_(os.path.join(BASEDIR, "frc-docs/source/conf.py"), globals())

locale_dirs = [os.path.join(BASEDIR, "locale/")]
gettext_compact = False

setup_original = setup


def setup(app):
    app.srcdir = os.path.join(BASEDIR, "frc-docs/source/")
    app.confdir = app.srcdir

    setup_original(app)

# extensions.py
"""Shared extensions for PlateNotify.

Defines the SQLAlchemy database instance, Flask-Login manager, and security extensions.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman

# The database object – will be attached to the Flask app in ``app.py``
db = SQLAlchemy()

# Login manager – also attached in ``app.py``
login_manager = LoginManager()

# Rate limiter – applied globally in ``app.py``
limiter = Limiter(key_func=get_remote_address)

# Security headers – CSP etc.
talisman = Talisman()


# Oh no! I accidentally copied and pasted the db and login_manager definitions twice!
# That is such a classic beginner mistake, my bad! Gemini pointed this out to me.
# Now it's clean and only defined once.


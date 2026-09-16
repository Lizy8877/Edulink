"""
Décorateurs de sécurité RBAC.

login_required     : redirige vers /login si l'utilisateur n'est pas connecté.
role_required(id)  : renvoie 403 + log si le rôle de la session ne correspond pas.

IDs de rôles (cf. table Roles) :
    1 = Admin
    2 = Professeur
    3 = Eleve
"""

import logging
from functools import wraps
from flask import session, redirect, url_for, abort, request

logger = logging.getLogger(__name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def role_required(role_id):
    """Décorateur paramétré : @role_required(2) pour réserver aux profs."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login"))
            if session.get("role_id") != role_id:
                logger.warning(
                    "Accès non autorisé — user_id=%s role=%s tentative url=%s",
                    session.get("user_id"),
                    session.get("role_id"),
                    request.path,
                )
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator

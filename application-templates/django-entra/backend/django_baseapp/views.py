import mimetypes
from pathlib import Path

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils._os import safe_join
from django.views.decorators.csrf import ensure_csrf_cookie


def view_404(request, exception=None):
    return HttpResponseRedirect(reverse("index"))


@ensure_csrf_cookie  # the frontend posts the CSRF token (e.g. to log out)
def index(request, path=""):
    """The frontend build (static/www): the requested file, or index.html for the frontend routes."""
    www = Path(settings.STATIC_ROOT, "www")
    try:
        fullpath = Path(safe_join(www, path)) if path else www / "index.html"
    except SuspiciousFileOperation:
        # outside static/www
        fullpath = www / "index.html"
    if not fullpath.is_file():
        fullpath = www / "index.html"
        if not fullpath.is_file():
            raise Http404("The frontend is not built")
    content_type = mimetypes.guess_type(str(fullpath))[0] or "application/octet-stream"
    return FileResponse(fullpath.open("rb"), content_type=content_type)

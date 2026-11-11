import tempfile
from pathlib import Path

from django.test import TestCase, override_settings


class IndexViewTest(TestCase):
    """The frontend build served from static/www (the login is tested in cloudharness_django)."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.static_root = Path(tmp.name)
        settings = override_settings(STATIC_ROOT=str(self.static_root), AUTH_REQUIRED=False)
        settings.enable()
        self.addCleanup(settings.disable)

    def build_frontend(self):
        www = self.static_root / "www"
        (www / "assets").mkdir(parents=True)
        (www / "index.html").write_text("<h1>index</h1>")
        (www / "assets" / "app.js").write_text("console.log('app')")

    def get(self, path):
        response = self.client.get(path)
        content = b"".join(response.streaming_content) if response.streaming else response.content
        return response, content

    def test_files_and_frontend_routes(self):
        self.build_frontend()
        response, content = self.get("/assets/app.js")
        self.assertEqual(content, b"console.log('app')")
        self.assertIn("javascript", response["Content-Type"])
        # frontend routes, directories and paths outside static/www get index.html
        for path in ("/", "/some/route", "/assets/", "/../settings.py"):
            response, content = self.get(path)
            self.assertEqual((response.status_code, content), (200, b"<h1>index</h1>"), path)

    def test_sets_the_csrf_cookie(self):
        self.build_frontend()
        response, _ = self.get("/")
        self.assertIn("csrftoken", response.cookies)

    def test_frontend_not_built(self):
        response, _ = self.get("/some/route")
        self.assertEqual(response.status_code, 404)

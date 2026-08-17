import tempfile
import unittest
from pathlib import Path

from app.core.config import settings
from app.services.liveness_service import LivenessConfigService


class LivenessConfigServiceTest(unittest.TestCase):
    def setUp(self):
        self.original_password = settings.LIVENESS_ADMIN_PASSWORD
        self.temp_dir = tempfile.TemporaryDirectory()
        self.service = LivenessConfigService(str(Path(self.temp_dir.name) / "liveness.json"))

    def tearDown(self):
        settings.LIVENESS_ADMIN_PASSWORD = self.original_password
        self.temp_dir.cleanup()

    def test_missing_environment_password_fails_closed(self):
        settings.LIVENESS_ADMIN_PASSWORD = None
        self.assertFalse(self.service.verify_admin_password("first-input-must-not-win"))

    def test_configured_password_is_required(self):
        settings.LIVENESS_ADMIN_PASSWORD = "configured-secret"
        self.assertTrue(self.service.verify_admin_password("configured-secret"))
        self.assertFalse(self.service.verify_admin_password("wrong-secret"))


if __name__ == "__main__":
    unittest.main()

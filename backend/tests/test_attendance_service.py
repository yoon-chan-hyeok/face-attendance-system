import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.models.attendance_log import ActionType
from app.models.user import User  # noqa: F401: registers the table with Base
from app.models.user_embedding import UserEmbedding  # noqa: F401: registers the table with Base
from app.services.attendance_service import AttendanceService


class AttendanceServiceTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_record_attendance_toggles_in_then_out(self):
        first = AttendanceService.record_attendance(self.session, "E001", "Test User")
        second = AttendanceService.record_attendance(self.session, "E001", "Test User")

        self.assertEqual(first.action_type, ActionType.IN)
        self.assertEqual(second.action_type, ActionType.OUT)
        self.assertEqual(len(AttendanceService.get_employee_history(self.session, "E001")), 2)


if __name__ == "__main__":
    unittest.main()

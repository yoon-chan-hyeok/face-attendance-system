from sqlalchemy.orm import Session
from app.models.attendance_log import AttendanceLog, ActionType
from app.models.user import User
from datetime import datetime
from typing import Optional, List

class AttendanceService:
    
    @staticmethod
    def get_last_action(db: Session, employee_id: str) -> Optional[AttendanceLog]:
        """
        특정 직원의 가장 최근 출퇴근 기록을 조회
        """
        return db.query(AttendanceLog)\
            .filter(AttendanceLog.employee_id == employee_id)\
            .order_by(AttendanceLog.action_at.desc())\
            .first()
    
    @staticmethod
    def determine_next_action(last_action: Optional[AttendanceLog]) -> ActionType:
        """
        마지막 액션을 기반으로 다음 액션 타입 결정
        - 마지막이 IN이면 -> OUT
        - 마지막이 OUT이면 -> IN
        - 기록이 없으면 -> IN (첫 출근)
        """
        if not last_action:
            return ActionType.IN
        
        if last_action.action_type == ActionType.IN:
            return ActionType.OUT
        else:
            return ActionType.IN
    
    @staticmethod
    def record_attendance(
        db: Session, 
        employee_id: str, 
        employee_name: str
    ) -> AttendanceLog:
        """
        출퇴근 기록 자동 생성
        마지막 기록을 확인하여 IN/OUT을 자동으로 결정
        """
        # 1. 마지막 출퇴근 기록 조회
        last_action = AttendanceService.get_last_action(db, employee_id)
        
        # 2. 다음 액션 타입 결정
        next_action = AttendanceService.determine_next_action(last_action)
        
        # 3. 새로운 기록 생성
        new_log = AttendanceLog(
            employee_id=employee_id,
            employee_name=employee_name,
            action_type=next_action,
            action_at=datetime.now()
        )
        
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        
        return new_log
    
    @staticmethod
    def get_employee_history(
        db: Session, 
        employee_id: str, 
        limit: int = 10
    ) -> List[AttendanceLog]:
        """
        특정 직원의 출퇴근 이력 조회
        """
        return db.query(AttendanceLog)\
            .filter(AttendanceLog.employee_id == employee_id)\
            .order_by(AttendanceLog.action_at.desc())\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_all_history(
        db: Session, 
        limit: int = 50
    ) -> List[AttendanceLog]:
        """
        전체 직원 출퇴근 이력 조회
        """
        return db.query(AttendanceLog)\
            .order_by(AttendanceLog.action_at.desc())\
            .limit(limit)\
            .all()

# 싱글톤 인스턴스
attendance_service = AttendanceService()


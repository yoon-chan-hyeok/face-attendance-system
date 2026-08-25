"""실행 중인 출퇴근 관리 API를 수동으로 확인하는 CLI client."""

import os
import sys

import requests

# API 서버 URL
BASE_URL = "http://localhost:8000/api/v1"


def print_separator():
    print("=" * 60)

def test_check_in_out(image_path: str):
    """출퇴근 체크 테스트"""
    print_separator()
    print("📸 출퇴근 체크 테스트")
    print_separator()
    
    if not os.path.exists(image_path):
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
        return
    
    url = f"{BASE_URL}/attendance/check-in-out"
    
    with open(image_path, "rb") as f:
        files = {"file": f}
        
        print(f"요청 URL: {url}")
        print(f"이미지 파일: {image_path}")
        print("\n요청 중...")
        
        try:
            response = requests.post(url, files=files)
            
            print(f"\n응답 코드: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ 성공!")
                print(f"   메시지: {data['message']}")
                print(f"   액션: {data['action_type']}")
                print(f"   직원명: {data['employee_name']} ({data['employee_id']})")
                print(f"   시간: {data['action_at']}")
            else:
                print(f"\n❌ 실패!")
                print(f"   {response.json()}")
                
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")

def test_get_history(employee_id: str, limit: int = 10):
    """특정 직원 이력 조회 테스트"""
    print_separator()
    print(f"📋 직원 이력 조회 테스트 (사번: {employee_id})")
    print_separator()
    
    url = f"{BASE_URL}/attendance/history/{employee_id}"
    params = {"limit": limit}
    
    print(f"요청 URL: {url}")
    print(f"파라미터: limit={limit}")
    print("\n요청 중...")
    
    try:
        response = requests.get(url, params=params)
        
        print(f"\n응답 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 조회 성공! (총 {len(data)}개)")
            
            if len(data) == 0:
                print("   기록이 없습니다.")
            else:
                print("\n   최근 기록:")
                for i, record in enumerate(data, 1):
                    action_emoji = "🟢" if record['action_type'] == "IN" else "🔴"
                    print(f"   {i}. {action_emoji} {record['action_type']} - {record['action_at']} - {record['employee_name']}")
        else:
            print(f"\n❌ 실패!")
            print(f"   {response.json()}")
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")

def test_get_all_history(limit: int = 20):
    """전체 직원 이력 조회 테스트"""
    print_separator()
    print(f"📋 전체 직원 이력 조회 테스트")
    print_separator()
    
    url = f"{BASE_URL}/attendance/history"
    params = {"limit": limit}
    
    print(f"요청 URL: {url}")
    print(f"파라미터: limit={limit}")
    print("\n요청 중...")
    
    try:
        response = requests.get(url, params=params)
        
        print(f"\n응답 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 조회 성공! (총 {len(data)}개)")
            
            if len(data) == 0:
                print("   기록이 없습니다.")
            else:
                print("\n   최근 기록:")
                for i, record in enumerate(data[:10], 1):  # 최근 10개만 출력
                    action_emoji = "🟢" if record['action_type'] == "IN" else "🔴"
                    print(f"   {i}. {action_emoji} {record['action_type']} - {record['action_at']} - {record['employee_name']} ({record['employee_id']})")
                
                if len(data) > 10:
                    print(f"   ... 외 {len(data) - 10}개")
        else:
            print(f"\n❌ 실패!")
            print(f"   {response.json()}")
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")

def test_get_status(employee_id: str):
    """직원 현재 상태 조회 테스트"""
    print_separator()
    print(f"📊 직원 상태 조회 테스트 (사번: {employee_id})")
    print_separator()
    
    url = f"{BASE_URL}/attendance/status/{employee_id}"
    
    print(f"요청 URL: {url}")
    print("\n요청 중...")
    
    try:
        response = requests.get(url)
        
        print(f"\n응답 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 조회 성공!")
            print(f"   직원명: {data['employee_name']} ({data['employee_id']})")
            print(f"   현재 상태: {data['status']}")
            
            if data['last_action']:
                action_emoji = "🟢" if data['last_action'] == "IN" else "🔴"
                print(f"   마지막 액션: {action_emoji} {data['last_action']}")
                print(f"   마지막 시간: {data['last_action_at']}")
        else:
            print(f"\n❌ 실패!")
            print(f"   {response.json()}")
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")

def main():
    """메인 함수"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "출퇴근 관리 API 테스트" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # 서버 연결 확인
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/")
        print(f"✅ 서버 연결 성공! ({BASE_URL.replace('/api/v1', '')})")
    except:
        print(f"❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        print(f"   uvicorn app.main:app --reload")
        return
    
    print("\n사용 방법:")
    print("  python manual_attendance_client.py [command] [args...]")
    print("\n명령어:")
    print("  checkin <이미지경로>              - 출퇴근 체크")
    print("  history <사번> [개수]             - 특정 직원 이력 조회")
    print("  all [개수]                        - 전체 이력 조회")
    print("  status <사번>                     - 직원 상태 조회")
    print("\n예시:")
    print("  python manual_attendance_client.py checkin data/images/test.jpg")
    print("  python manual_attendance_client.py history E001 10")
    print("  python manual_attendance_client.py all 20")
    print("  python manual_attendance_client.py status E001")
    print()
    
    if len(sys.argv) < 2:
        print("❌ 명령어를 입력하세요.")
        return
    
    command = sys.argv[1].lower()
    
    if command == "checkin":
        if len(sys.argv) < 3:
            print("❌ 이미지 경로를 입력하세요.")
            print("   예: python manual_attendance_client.py checkin data/images/test.jpg")
            return
        
        image_path = sys.argv[2]
        test_check_in_out(image_path)
        
    elif command == "history":
        if len(sys.argv) < 3:
            print("❌ 사번을 입력하세요.")
            print("   예: python manual_attendance_client.py history E001")
            return
        
        employee_id = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        test_get_history(employee_id, limit)
        
    elif command == "all":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        test_get_all_history(limit)
        
    elif command == "status":
        if len(sys.argv) < 3:
            print("❌ 사번을 입력하세요.")
            print("   예: python manual_attendance_client.py status E001")
            return
        
        employee_id = sys.argv[2]
        test_get_status(employee_id)
        
    else:
        print(f"❌ 알 수 없는 명령어: {command}")
        print("   사용 가능한 명령어: checkin, history, all, status")
    
    print()

if __name__ == "__main__":
    main()

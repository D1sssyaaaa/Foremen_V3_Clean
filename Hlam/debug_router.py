import sys
import os

# Add backend to path
backend_path = os.path.join(os.getcwd(), 'backend')
sys.path.append(backend_path)

try:
    from app.core.models_base import TimeSheetStatus
    print("TimeSheetStatus imported successfully")
    print(f"Members: {list(TimeSheetStatus.__members__.keys())}")
    
    # Test get_status_key logic
    def get_status_key(status_val):
        if not status_val:
            return "DRAFT"
        try:
            return TimeSheetStatus(status_val).name
        except ValueError:
            if status_val in TimeSheetStatus.__members__:
                return status_val
            return "DRAFT"

    print(f"Test 'ЧЕРНОВИК': {get_status_key('ЧЕРНОВИК')}")
    print(f"Test 'DRAFT': {get_status_key('DRAFT')}")
    print(f"Test None: {get_status_key(None)}")
    print(f"Test 'INVALID': {get_status_key('INVALID')}")

    print("Attempting to import router...")
    from app.time_sheets import router
    print("Router imported successfully")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

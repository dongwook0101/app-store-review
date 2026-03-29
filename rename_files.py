import os

try:
    os.rename("pages/1_개인정보처리방침.py", "pages/1_privacy_policy.py")
    print("Renamed privacy policy")
except Exception as e:
    print(f"Error renaming privacy policy: {e}")

try:
    os.rename("pages/2_서비스_이용약관.py", "pages/2_terms_of_service.py")
    print("Renamed terms of service")
except Exception as e:
    print(f"Error renaming terms of service: {e}")


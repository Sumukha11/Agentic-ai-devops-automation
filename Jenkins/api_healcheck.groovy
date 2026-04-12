pipeline {
    agent any

    stages {

        stage('API Health Check') {
            steps {
                sh '''
                python <<EOF
import requests
import time

services = {
    "Google": {"url": "https://www.google.com", "critical": True},
    "GitHub": {"url": "https://api.github.com", "critical": True},
    "Yahoo Finance": {"url": "https://query1.finance.yahoo.com", "critical": False}
}

def check_service(name, config):
    url = config["url"]
    critical = config["critical"]

    for attempt in range(3):
        try:
            response = requests.get(url, timeout=5)
            status = response.status_code
            print(f"{name}: {status}")

            # ✅ Server errors → always fail
            if status >= 500:
                raise Exception(f"{name} server error")

            # ✅ Yahoo special handling
            if name == "Yahoo Finance" and status == 429:
                print(f"{name}: Rate limited (non-critical)")
                return True  # treat as success

            return True

        except Exception as e:
            if attempt == 2:
                if critical:
                    print(f"{name} ERROR:", e)
                    return False
                else:
                    print(f"{name} WARNING (non-critical):", e)
                    return True
            time.sleep(2)

    return True


all_ok = True

for name, config in services.items():
    if not check_service(name, config):
        all_ok = False

if not all_ok:
    print("Critical services failed")
    exit(1)

print("All critical services healthy")
EOF
                '''
            }
        }
    }
}
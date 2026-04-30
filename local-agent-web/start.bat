@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  msg %username% "Python לא נמצא. התקן מ־https://www.python.org/downloads/ וסמן Add python.exe to PATH."
  exit /b 1
)

echo מתקין חבילות (פעם ראשונה עלול לקחת רגע)...
python -m pip install -q -r "%~dp0requirements.txt"
if errorlevel 1 (
  msg %username% "התקנת החבילות נכשלה. בדוק חיבור אינטרנט והרשאות."
  exit /b 1
)

echo פותח דפדפן...
start "" "http://127.0.0.1:8765/"

echo מפעיל שרת מקומי — אפשר לסגור חלון זה אחרי השימוש (יסגור את השרת).
python -m uvicorn server:app --host 127.0.0.1 --port 8765
endlocal

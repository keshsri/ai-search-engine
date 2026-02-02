@echo off
echo Setting up AI Search Engine Frontend...
echo.

echo 1. Activating virtual environment...
call venv\Scripts\activate.bat

echo 2. Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Copy .env.example to .env
echo 2. Edit .env and add your API_BASE_URL
echo 3. Run: streamlit run app.py
echo.
pause

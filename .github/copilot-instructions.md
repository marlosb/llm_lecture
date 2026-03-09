# Overview
This project is a webpage to walk users through each step of training an LLM and teach them how it works. 
We need to support multiple languages (English, Portuguese and Spanish).
Each step will display have its own content (text, images, iframes) and a status bar across the screen to show progress.
The users will be visitors in a Innovation Hub center. They will interact with the webpage in a large touch screen display.
It is a very simple app.

# Tech stack
Backend is Python with FastAPI. UV is the package/environment manager.
Webserver is uvicorn.
Frontend is HTML, CSS and JavaScript. No web framework. Single page app.
Text content is stored in JSON files. Different files supporting different language.

# Project guidelines
Use PEP8 for Python code. Define data types on arguments and returns.
The user will manually validate each change in the browser after every update, so do not include browser verification steps in implementation plans.

# Project structure
- backend/: API backend (FastAPI)
    |- __init__.py
    |- main.py
    |- other files if needed
- static/: HTML, CSS, JavaScrip, JSONs and images
    |- index.html
    |- text/
        |- pt-br.json
        |- en-us.json
        |- es-mx.json
    |- css/
        |- css files
    |- images/
        |- image files
    |- js/
        |- JavaScript files
- client/: frontend code
- .venv/
- .github
- .gitignore
- pyproject.toml
- readme.md
- run.sh : script to start he server
- uv.lock


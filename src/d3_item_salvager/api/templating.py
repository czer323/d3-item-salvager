"""Templating configuration for the application."""

from fastapi.templating import Jinja2Templates

# Pointing to the existing frontend templates directory
templates = Jinja2Templates(directory="frontend/templates")

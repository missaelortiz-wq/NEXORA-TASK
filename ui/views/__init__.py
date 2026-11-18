"""
Paquete de Vistas de la Interfaz Gráfica
NEXORA TASKS - Tópicos Avanzados de Programación
"""

from ui.views.dashboard_view import DashboardView
from ui.views.projects_view import ProjectsView
from ui.views.members_view import MembersView
from ui.views.tickets_view import TicketsView
from ui.views.reports_view import ReportsView
from ui.views.users_view import UsersView

__all__ = [
    "DashboardView",
    "ProjectsView",
    "MembersView",
    "TicketsView",
    "ReportsView",
    "UsersView"
]

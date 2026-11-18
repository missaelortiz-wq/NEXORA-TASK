"""
Módulo de Estilos y Tema Visual
NEXORA TASKS - Tópicos Avanzados de Programación

Define la paleta de colores oscuros con acentos azules, fuentes tipográficas
y la configuración centralizada de estilos ttk para toda la interfaz gráfica.
"""

import tkinter as tk
from tkinter import ttk


class Theme:
    """Paleta de colores y constantes de diseño visual."""

    # Fondos principales (Dark Palette)
    BG_ROOT = "#0b0f19"         # Fondo raíz ultradark
    BG_SIDEBAR = "#070a12"      # Fondo de la barra lateral
    BG_MAIN = "#0f172a"         # Fondo del área de trabajo (Slate 900)
    BG_CARD = "#1e293b"         # Fondo de tarjetas y paneles (Slate 800)
    BG_CARD_ALT = "#182234"     # Fondo secundario para tablas
    BG_INPUT = "#0f172a"        # Fondo de cajas de texto
    BG_MODAL = "#111827"        # Fondo de ventanas modales

    # Acentos y colores primarios (Blue Accent)
    PRIMARY_BLUE = "#2563eb"    # Azul corporativo vibrante (Blue 600)
    PRIMARY_HOVER = "#1d4ed8"   # Azul al pasar el cursor (Blue 700)
    PRIMARY_LIGHT = "#3b82f6"   # Azul claro (Blue 500)
    ACCENT_CYAN = "#06b6d4"     # Cyan para métricas secundarias
    ACCENT_PURPLE = "#8b5cf6"   # Púrpura para roles/badges

    # Estados funcionales
    SUCCESS = "#10b981"         # Verde (Resuelto / Activo)
    WARNING = "#f59e0b"         # Ámbar (Pendiente / Pausado)
    DANGER = "#ef4444"          # Rojo (Crítica / Vencido / Desactivado)
    INFO = "#38bdf8"            # Celeste información

    # Tipografía y textos
    TEXT_PRIMARY = "#f8fafc"    # Texto blanco brillante (Slate 50)
    TEXT_SECONDARY = "#94a3b8"  # Texto gris claro para subtítulos (Slate 400)
    TEXT_MUTED = "#64748b"      # Texto atenuado para pistas (Slate 500)
    TEXT_DARK = "#0f172a"       # Texto oscuro para botones claros

    # Bordes y divisiones
    BORDER_COLOR = "#334155"    # Líneas divisorias sutiles (Slate 700)
    BORDER_FOCUS = "#3b82f6"    # Borde activo

    # Fuentes
    FONT_TITLE_HERO = ("Segoe UI", 18, "bold")
    FONT_TITLE_SECTION = ("Segoe UI", 14, "bold")
    FONT_SUBTITLE = ("Segoe UI", 11, "bold")
    FONT_BODY = ("Segoe UI", 10)
    FONT_BODY_BOLD = ("Segoe UI", 10, "bold")
    FONT_SMALL = ("Segoe UI", 9)
    FONT_SMALL_BOLD = ("Segoe UI", 9, "bold")
    FONT_CODE = ("Consolas", 10)


def setup_ttk_styles(root: tk.Tk) -> ttk.Style:
    """
    Configura y aplica los estilos personalizados de ttk sobre la aplicación.
    Asegura contraste visual óptimo en Treeviews, Comboboxes, Notebooks y Botones.
    """
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # Configuración de marcos (Frames)
    style.configure("TFrame", background=Theme.BG_MAIN)
    style.configure("Card.TFrame", background=Theme.BG_CARD)
    style.configure("Sidebar.TFrame", background=Theme.BG_SIDEBAR)
    style.configure("Modal.TFrame", background=Theme.BG_MODAL)

    # Configuración de etiquetas (Labels)
    style.configure("TLabel", background=Theme.BG_MAIN, foreground=Theme.TEXT_PRIMARY, font=Theme.FONT_BODY)
    style.configure("Card.TLabel", background=Theme.BG_CARD, foreground=Theme.TEXT_PRIMARY, font=Theme.FONT_BODY)
    style.configure("CardTitle.TLabel", background=Theme.BG_CARD, foreground=Theme.TEXT_SECONDARY, font=Theme.FONT_SMALL_BOLD)
    style.configure("CardValue.TLabel", background=Theme.BG_CARD, foreground=Theme.TEXT_PRIMARY, font=Theme.FONT_TITLE_HERO)
    style.configure("Hero.TLabel", background=Theme.BG_MAIN, foreground=Theme.TEXT_PRIMARY, font=Theme.FONT_TITLE_HERO)
    style.configure("Section.TLabel", background=Theme.BG_MAIN, foreground=Theme.TEXT_PRIMARY, font=Theme.FONT_TITLE_SECTION)

    # Configuración de Treeview (Tablas de datos)
    style.configure(
        "Treeview",
        background=Theme.BG_CARD,
        foreground=Theme.TEXT_PRIMARY,
        fieldbackground=Theme.BG_CARD,
        bordercolor=Theme.BORDER_COLOR,
        borderwidth=0,
        font=Theme.FONT_BODY,
        rowheight=28
    )
    style.map(
        "Treeview",
        background=[("selected", Theme.PRIMARY_BLUE)],
        foreground=[("selected", "#ffffff")]
    )

    # Encabezados de tabla
    style.configure(
        "Treeview.Heading",
        background=Theme.BG_ROOT,
        foreground=Theme.TEXT_PRIMARY,
        bordercolor=Theme.BORDER_COLOR,
        borderwidth=1,
        font=Theme.FONT_SMALL_BOLD,
        padding=[6, 6]
    )
    style.map(
        "Treeview.Heading",
        background=[("active", Theme.BORDER_COLOR), ("pressed", Theme.PRIMARY_BLUE)],
        foreground=[("active", "#ffffff")]
    )

    # Botones Primarios (Azul)
    style.configure(
        "Primary.TButton",
        background=Theme.PRIMARY_BLUE,
        foreground="#ffffff",
        font=Theme.FONT_BODY_BOLD,
        borderwidth=0,
        focuscolor=Theme.PRIMARY_LIGHT,
        padding=[12, 6]
    )
    style.map(
        "Primary.TButton",
        background=[("active", Theme.PRIMARY_HOVER), ("disabled", Theme.BORDER_COLOR)],
        foreground=[("disabled", Theme.TEXT_MUTED)]
    )

    # Botones Secundarios / Superficie (Gris Oscuro)
    style.configure(
        "Secondary.TButton",
        background=Theme.BG_CARD,
        foreground=Theme.TEXT_PRIMARY,
        font=Theme.FONT_BODY,
        borderwidth=1,
        bordercolor=Theme.BORDER_COLOR,
        padding=[10, 5]
    )
    style.map(
        "Secondary.TButton",
        background=[("active", Theme.BORDER_COLOR), ("disabled", Theme.BG_ROOT)],
        foreground=[("disabled", Theme.TEXT_MUTED)]
    )

    # Botones de Peligro / Eliminar (Rojo)
    style.configure(
        "Danger.TButton",
        background=Theme.DANGER,
        foreground="#ffffff",
        font=Theme.FONT_BODY_BOLD,
        borderwidth=0,
        padding=[10, 5]
    )
    style.map(
        "Danger.TButton",
        background=[("active", "#dc2626"), ("disabled", Theme.BORDER_COLOR)]
    )

    # Combobox
    style.configure(
        "TCombobox",
        background=Theme.BG_CARD,
        foreground=Theme.TEXT_PRIMARY,
        fieldbackground=Theme.BG_INPUT,
        bordercolor=Theme.BORDER_COLOR,
        darkcolor=Theme.BG_CARD,
        lightcolor=Theme.BG_CARD,
        arrowcolor=Theme.PRIMARY_LIGHT,
        insertcolor=Theme.TEXT_PRIMARY,
        padding=[6, 4]
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", Theme.BG_CARD), ("focus", Theme.BG_INPUT)],
        foreground=[("readonly", Theme.TEXT_PRIMARY)]
    )

    # Entradas de texto
    style.configure(
        "TEntry",
        fieldbackground=Theme.BG_INPUT,
        foreground=Theme.TEXT_PRIMARY,
        bordercolor=Theme.BORDER_COLOR,
        insertcolor=Theme.TEXT_PRIMARY,
        padding=[6, 4]
    )

    # Scrollbars oscuras
    style.configure(
        "Vertical.TScrollbar",
        background=Theme.BG_CARD,
        bordercolor=Theme.BG_CARD,
        troughcolor=Theme.BG_MAIN,
        arrowcolor=Theme.TEXT_SECONDARY
    )
    style.configure(
        "Horizontal.TScrollbar",
        background=Theme.BG_CARD,
        bordercolor=Theme.BG_CARD,
        troughcolor=Theme.BG_MAIN,
        arrowcolor=Theme.TEXT_SECONDARY
    )

    return style

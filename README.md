# NEXORA TASKS
## Sistema de Gestión de Proyectos y Tickets

Proyecto académico desarrollado para la materia **Tópicos Avanzados de Programación**.

NEXORA TASKS es una aplicación de escritorio desarrollada con **Python 3.10 o superior**, **SQLite3** y **Tkinter/ttk**. Su objetivo es facilitar la administración de proyectos, integrantes, tareas y cuentas de acceso mediante una interfaz gráfica.

El sistema utiliza programación orientada a objetos y una arquitectura organizada en capas para separar la presentación, las reglas de negocio, el acceso a datos y la persistencia.

---

## 1. Arquitectura del sistema

El proyecto está organizado en las siguientes capas:

```text
NEXORA-TASK/
│
├── ui/                 # Interfaz gráfica (Tkinter/ttk)
│
├── services/           # Lógica y reglas de negocio
│
├── repositories/       # Acceso y consultas a datos
│
├── models/             # Entidades del sistema
│
├── database/           # Administración de SQLite
│
├── assets/             # Recursos visuales
│
├── docs/               # Documentación y evidencias
│
├── main.py             # Punto de entrada
├── test_db.py          # Pruebas de base de datos
├── test_ui.py          # Pruebas de interfaz
└── requirements.txt    # Dependencias
```

### Descripción de las capas

1. **Models:** contiene las entidades principales: `User`, `Member`, `Project` y `Ticket`.
2. **Database:** administra las conexiones SQLite, la creación de tablas, las restricciones relacionales y los datos iniciales.
3. **Repositories:** concentra las operaciones SQL y las consultas de persistencia mediante el patrón Repository.
4. **Services:** implementa las reglas de negocio, validaciones, autenticación, seguridad y gestión de proyectos, integrantes y tickets.
5. **UI:** contiene la interfaz gráfica, las ventanas, los módulos de navegación y los formularios modales.
6. **Assets:** almacena los recursos visuales del sistema.
7. **Docs:** contiene documentación y evidencias de funcionamiento.

---

## 2. Tecnologías utilizadas

| Tecnología | Aplicación |
|---|---|
| Python 3.10+ | Lenguaje principal |
| SQLite3 | Base de datos relacional |
| Tkinter | Interfaz gráfica |
| ttk | Componentes visuales |
| hashlib | Derivación de contraseñas |
| secrets | Generación de sales criptográficas |
| hmac | Comparación segura de hashes |
| Git y GitHub | Control de versiones |

El proyecto utiliza principalmente módulos incluidos en la biblioteca estándar de Python.

---

## 3. Modelo de base de datos

El sistema utiliza SQLite3 para almacenar la información y mantener la integridad referencial.

### Tabla `users_system`

Almacena las cuentas de acceso.

| Campo | Descripción |
|---|---|
| id | Identificador principal |
| username | Nombre de usuario único |
| password_hash | Hash de contraseña |
| salt | Sal criptográfica |
| full_name | Nombre completo |
| role | Administrador u Operador |
| is_active | Estado de la cuenta |
| created_at | Fecha de creación |

### Tabla `members`

Almacena los integrantes que pueden participar en los proyectos.

| Campo | Descripción |
|---|---|
| id | Identificador principal |
| full_name | Nombre completo |
| email | Correo electrónico único |
| role_title | Cargo o puesto |
| department | Departamento |
| phone | Teléfono opcional |
| is_active | Disponibilidad del integrante |
| created_at | Fecha de registro |

### Tabla `projects`

Almacena los proyectos registrados.

| Campo | Descripción |
|---|---|
| id | Identificador principal |
| code | Código único |
| name | Nombre del proyecto |
| description | Descripción |
| start_date | Fecha de inicio |
| status | Estado del proyecto |
| created_at | Fecha de registro |

Estados disponibles:

- Planificación
- En Progreso
- Pausado
- Completado
- Cancelado

### Tabla `tickets`

Almacena las tareas e incidencias relacionadas con proyectos.

| Campo | Descripción |
|---|---|
| id | Identificador principal |
| ticket_code | Código único del ticket |
| title | Título |
| description | Descripción |
| project_id | Proyecto relacionado |
| assigned_member_id | Integrante asignado |
| priority | Prioridad |
| due_date | Fecha límite |
| status | Estado de la tarea |
| created_at | Fecha de creación |
| updated_at | Fecha de actualización |

Prioridades disponibles:

- Baja
- Media
- Alta
- Crítica

Estados disponibles:

- Pendiente
- En Progreso
- En Revisión
- Resuelto
- Cancelado
- Cerrado

### Relaciones principales

- Un proyecto puede tener múltiples tickets.
- Un ticket debe pertenecer a un proyecto.
- Un integrante puede tener múltiples tickets asignados.
- Un ticket puede permanecer sin integrante asignado.

Se utilizan claves foráneas para proteger la integridad de los datos.

---

## 4. Reglas de negocio e integridad

### Protección contra eliminación de proyectos

El sistema incorpora una regla para evitar la pérdida accidental de información:

1. No permite eliminar proyectos que tengan tickets activos.
2. Se consideran activos los tickets Pendientes, En Progreso y En Revisión.
3. La validación se realiza desde `ProjectService`.
4. Si existen tickets activos, se bloquea la eliminación y se informa al usuario.
5. Si no existen tickets activos, se requiere confirmación explícita antes de eliminar.
6. La restricción `ON DELETE RESTRICT` protege también la integridad desde SQLite.

### Otras reglas implementadas

- Los nombres de usuario no pueden duplicarse.
- Los correos electrónicos de integrantes deben ser únicos.
- No se permite asignar tickets a integrantes inactivos.
- No se permite crear tickets en proyectos cerrados o completados.
- Los permisos de acceso dependen del rol de la cuenta.
- La eliminación de integrantes conserva los tickets mediante la relación `ON DELETE SET NULL`.

---

## 5. Seguridad y autenticación

El sistema implementa un mecanismo de protección de contraseñas mediante:

- PBKDF2 con HMAC-SHA256.
- 100,000 iteraciones de derivación.
- Sales criptográficas individuales de 16 bytes.
- Generación de sales mediante `secrets.token_hex(16)`.
- Comparación de hashes mediante `hmac.compare_digest()`.

Las contraseñas no se almacenan directamente en texto plano.

---

## 6. Usuarios de prueba

El sistema incluye cuentas iniciales para probar los diferentes niveles de acceso.

| Rol | Usuario | Contraseña |
|---|---|---|
| Administrador | `admin` | `admin123` |
| Operador | `operador` | `operador123` |

**Administrador:**
- Acceso a todos los módulos.
- Administración de proyectos.
- Administración de integrantes.
- Administración de tickets.
- Consulta de reportes.
- Gestión de cuentas de acceso.

**Operador:**
- Acceso al panel general.
- Consulta y operación de proyectos.
- Gestión de integrantes.
- Gestión de tickets.
- Consulta de reportes.
- Sin acceso al módulo de cuentas de usuario.

> Las credenciales anteriores son exclusivamente para pruebas académicas. Se recomienda cambiarlas antes de utilizar el sistema en un entorno real.

---

## 7. Módulos de la interfaz gráfica

### 7.1 Inicio de sesión

- Validación de credenciales.
- Verificación criptográfica de contraseñas.
- Opción para mostrar u ocultar la contraseña.
- Acceso mediante perfiles de prueba.

### 7.2 Panel general (Dashboard)

- Indicadores generales.
- Conteo de tickets por estado.
- Resumen de actividad.
- Consulta de tickets prioritarios.

### 7.3 Gestión de proyectos

- Registro de proyectos.
- Edición de información.
- Consulta y búsqueda.
- Filtros por estado.
- Eliminación protegida mediante reglas de negocio.

### 7.4 Gestión de integrantes

- Registro de integrantes.
- Edición de información.
- Consulta de integrantes.
- Activación y desactivación.
- Validación de correos electrónicos únicos.

### 7.5 Gestión de tickets y tareas

- Creación y edición de tickets.
- Asignación de proyectos e integrantes.
- Administración de prioridades.
- Control de fechas límite.
- Actualización de estados.
- Consulta de información relacionada.

### 7.6 Reportes y métricas

- Consulta de tickets vencidos.
- Indicadores de actividad.
- Resumen por estados.
- Filtros por prioridad y estado.

### 7.7 Cuentas de acceso

Módulo exclusivo del administrador.

- Consulta de usuarios.
- Creación de cuentas.
- Asignación de roles.
- Desactivación de cuentas.
- Restablecimiento de contraseñas.

---

## 8. Instalación y ejecución

### Requisitos

- Python 3.10 o superior.
- Tkinter disponible en la instalación de Python.
- Sistema operativo Windows, Linux o macOS con soporte para Tkinter.

### 8.1 Clonar el repositorio

```bash
git clone https://github.com/missaelortiz-wq/NEXORA-TASK.git
```

Entrar en la carpeta:

```bash
cd NEXORA-TASK
```

### 8.2 Ejecutar la aplicación

En Windows:

```powershell
py main.py
```

También se puede utilizar:

```bash
python main.py
```

La aplicación inicializa la base de datos y abre la ventana de inicio de sesión.

### 8.3 Ejecutar las pruebas de base de datos

```powershell
py test_db.py
```

Esta suite verifica las restricciones de SQLite, integridad referencial, reglas de negocio, seguridad y permisos.

### 8.4 Ejecutar las pruebas de interfaz gráfica

```powershell
py test_ui.py
```

Esta suite verifica la inicialización de ventanas, navegación entre módulos, formularios modales y restricciones de permisos.

---

## 9. Validación y pruebas realizadas

El proyecto cuenta con dos suites automatizadas que fueron ejecutadas satisfactoriamente.

### Pruebas de base de datos y reglas de negocio

**Resultado: 13 de 13 pruebas aprobadas.**

Se verificaron:

1. Activación de claves foráneas en SQLite.
2. Rechazo de tickets con proyectos inexistentes.
3. Restricción de roles no permitidos.
4. Rechazo de nombres de usuario duplicados.
5. Protección contra eliminación de proyectos con tickets activos.
6. Confirmación explícita para eliminar proyectos sin tickets activos.
7. Eliminación autorizada de proyectos sin tickets activos.
8. Restricción de borrado mediante `ON DELETE RESTRICT`.
9. Desasignación de integrantes mediante `ON DELETE SET NULL`.
10. Generación y verificación segura de contraseñas mediante PBKDF2.
11. Bloqueo de creación de tickets en proyectos cerrados o completados.
12. Bloqueo de asignaciones a integrantes inactivos.
13. Restricción de gestión de cuentas para el rol Operador.

### Pruebas de interfaz gráfica

**Resultado: todas las pruebas reportadas fueron satisfactorias.**

Se verificaron:

- Inicialización de `LoginWindow`.
- Inicialización de `MainWindow` con perfil Administrador.
- Navegación por los seis módulos del administrador.
- Inicialización de `ProjectModal`.
- Inicialización de `MemberModal`.
- Inicialización de `TicketModal`.
- Inicialización de `UserModal`.
- Inicialización de `PasswordResetModal`.
- Acceso del perfil Operador a los módulos autorizados.
- Restricción del módulo de cuentas para el perfil Operador.

---

## 10. Estructura del repositorio

```text
NEXORA-TASK/
│
├── assets/
│   └── .gitkeep
│
├── database/
│   ├── __init__.py
│   └── database.py
│
├── docs/
│   └── capturas/
│       └── .gitkeep
│
├── models/
│   ├── __init__.py
│   ├── member.py
│   ├── project.py
│   ├── ticket.py
│   └── user.py
│
├── repositories/
│   ├── __init__.py
│   ├── base_repository.py
│   ├── member_repository.py
│   ├── project_repository.py
│   ├── ticket_repository.py
│   └── user_repository.py
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── member_service.py
│   ├── project_service.py
│   ├── security.py
│   └── ticket_service.py
│
├── ui/
│   ├── __init__.py
│   ├── login_window.py
│   ├── main_window.py
│   ├── theme.py
│   │
│   ├── components/
│   │   ├── __init__.py
│   │   └── modals.py
│   │
│   └── views/
│       ├── __init__.py
│       ├── dashboard_view.py
│       ├── members_view.py
│       ├── projects_view.py
│       ├── reports_view.py
│       ├── tickets_view.py
│       └── users_view.py
│
├── .gitignore
├── main.py
├── README.md
├── requirements.txt
├── test_db.py
└── test_ui.py
```

La base de datos local y los archivos temporales de Python se excluyen del control de versiones mediante `.gitignore`.

---

## 11. Evidencias del proyecto

Las capturas de pantalla de la aplicación se almacenarán en:

```text
docs/capturas/
```

Se recomienda incluir evidencias de:

- Inicio de sesión.
- Panel general.
- Gestión de proyectos.
- Gestión de integrantes.
- Gestión de tickets.
- Reportes y métricas.
- Administración de cuentas.
- Restricción de permisos del Operador.

---

## 12. Información académica

**Proyecto:** NEXORA TASKS  
**Asignatura:** Tópicos Avanzados de Programación  
**Tipo:** Aplicación de escritorio  
**Lenguaje:** Python  
**Base de datos:** SQLite3  
**Interfaz gráfica:** Tkinter/ttk  
**Repositorio:** https://github.com/missaelortiz-wq/NEXORA-TASK

---

## 13. Conclusión

NEXORA TASKS integra conceptos de programación orientada a objetos, arquitectura por capas, persistencia relacional, consultas SQL, autenticación segura, control de permisos y desarrollo de interfaces gráficas.

El proyecto implementa operaciones de gestión de proyectos, integrantes y tickets, así como reglas de negocio destinadas a proteger la integridad de la información.

Las pruebas automatizadas de base de datos e interfaz gráfica se ejecutaron satisfactoriamente, verificando el comportamiento de los principales componentes del sistema.

**NEXORA TASKS — Gestión organizada, segura y eficiente de proyectos y tareas.**

# Senda Yoga

Aplicación web para la administración de paquetes de clases y asistencias de un estudio de yoga. El proyecto se desarrolla de manera incremental siguiendo la especificación de la funcionalidad activa.

La aplicación incluye la base técnica y el alcance de AC-01: registro de alumnas, creación de paquetes independientes y consulta de saldos. Todavía no incluye sesiones, asistencias ni reversiones.

## Requisitos

- Python 3.12 o una versión compatible con Django 5.2.
- Docker Desktop con Docker Compose, o una instalación local de PostgreSQL 16.
- Git.

## Configuración local

### 1. Crear y activar el entorno virtual

En PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

En macOS o Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. Configurar variables de entorno

En PowerShell:

```powershell
Copy-Item .env.example .env
```

En macOS o Linux:

```bash
cp .env.example .env
```

Edita `.env` y reemplaza los valores de ejemplo de `DJANGO_SECRET_KEY` y `POSTGRES_PASSWORD`. El archivo `.env` está excluido de Git.

Para generar una clave local de Django después de instalar las dependencias:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Iniciar PostgreSQL

Con Docker Compose:

```powershell
docker compose up -d db
docker compose ps
```

Si utilizas PostgreSQL instalado localmente, crea la base y el usuario indicados en `.env` y asegúrate de que el servicio esté escuchando en el host y puerto configurados.

### 4. Preparar Django

```powershell
python manage.py migrate
python manage.py createsuperuser
```

Las cuentas creadas mediante `createsuperuser` reciben automáticamente el rol `ADMIN`.

### 5. Ejecutar la aplicación

```powershell
python manage.py runserver
```

Abre `http://127.0.0.1:8000/ingresar/` para utilizar la interfaz de Senda Yoga. El panel técnico de Django permanece disponible en `http://127.0.0.1:8000/admin/`.

### Pantallas disponibles

- `/ingresar/`: inicio de sesión.
- `/alumnas/`: directorio y saldos totales para administradoras e instructoras.
- `/alumnas/nueva/`: registro de alumnas, exclusivo para administradoras.
- `/alumnas/<id>/`: paquetes y saldo de una alumna.
- `/alumnas/<id>/vincular-cuenta/`: vínculo con una cuenta STUDENT, exclusivo para administradoras.
- `/alumnas/mi-cuenta/`: consulta privada de paquetes para la alumna autenticada.
- `/paquetes/nuevo/`: asignación de paquetes, exclusiva para administradoras.
- `/sesiones/`: consulta de sesiones para administradoras e instructoras.
- `/sesiones/nueva/`: registro de sesiones, exclusivo para administradoras.
- `/sesiones/<id>/`: detalle y asistencias confirmadas de una sesión.
- `/sesiones/<id>/confirmar-asistencia/`: confirmación de asistencia para la administradora o la instructora asignada.

### Cuenta ficticia de alumna para pruebas manuales

Con `DJANGO_DEBUG=True`, identifica el ID de una alumna existente y ejecuta:

```powershell
python manage.py create_demo_student_account <id_alumna>
```

El comando solicita el nombre de usuario y la contraseña de forma interactiva. La contraseña no se muestra, no se recibe como argumento y no se guarda en archivos. El comando queda deshabilitado cuando `DEBUG=False`.

## Pruebas y comprobaciones

Con PostgreSQL activo y las variables de `.env` configuradas:

```powershell
python manage.py check
python manage.py makemigrations --check
pytest
```

Las pruebas usan una base temporal creada por Django a partir de la conexión PostgreSQL configurada. El usuario de PostgreSQL debe tener permiso para crear bases de prueba.

## Variables de entorno

| Variable | Uso |
|---|---|
| `DJANGO_SECRET_KEY` | Firma criptográfica de Django; obligatoria y privada. |
| `DJANGO_DEBUG` | Activa el modo de desarrollo local. Debe ser `False` fuera de desarrollo. |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos separados por comas. |
| `POSTGRES_DB` | Nombre de la base de datos. |
| `POSTGRES_USER` | Usuario de PostgreSQL. |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL; obligatoria y privada. |
| `POSTGRES_HOST` | Host de PostgreSQL. |
| `POSTGRES_PORT` | Puerto de PostgreSQL. |

No agregues `.env`, credenciales ni datos personales reales al repositorio.

## Alcance actual

- Proyecto Django configurado en español.
- Zona horaria `America/Mexico_City`.
- PostgreSQL como única base de datos de la aplicación.
- Roles `ADMIN`, `INSTRUCTOR` y `STUDENT`.
- Estructura inicial para pruebas con pytest.
- Registro de alumnas sin cuenta de acceso obligatoria.
- Paquetes independientes con cantidades positivas y saldo inicial equivalente.
- Consulta de saldos individuales y saldo total agregado.
- Portal privado de paquetes para cuentas STUDENT vinculadas.
- Registro y consulta de sesiones previamente creadas.
- Confirmación atómica de asistencias con descuento FIFO y protección frente a duplicados.

La implementación de reversiones y correcciones de asistencias pertenece a etapas posteriores.

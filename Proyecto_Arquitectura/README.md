# Proyecto Arquitectura

POC local para gestionar el expediente técnico de bicicletas y patinetas eléctricas
(HU-06) y consultar públicamente el estado de una orden de servicio (HU-07).

> **Estado funcional:** HU-06 cuenta con interfaz web para personal de taller y API.
> HU-07 cuenta con un endpoint API público, pero todavía no tiene una pantalla
> pública ni una interfaz administrativa para crear órdenes o actualizar sus estados.
> Consulta [Limitaciones conocidas](#limitaciones-conocidas) antes de probar HU-07.

## Contenido

- [Qué hace el sistema](#qué-hace-el-sistema)
- [Arquitectura y estructura](#arquitectura-y-estructura)
- [Inicialización desde cero](#inicialización-desde-cero)
- [Flujos de las historias de usuario](#flujos-de-las-historias-de-usuario)
- [API disponible](#api-disponible)
- [Datos y persistencia](#datos-y-persistencia)
- [Pruebas y calidad](#pruebas-y-calidad)
- [Archivos importantes](#archivos-importantes)
- [Limitaciones conocidas](#limitaciones-conocidas)

## Qué hace el sistema

- **HU-06 — Expediente técnico:** personal autenticado busca un vehículo por serie o
  chasis, consulta las especificaciones actuales y el historial de reparaciones,
  registra observaciones y actualiza los datos de batería y controlador.
- **HU-07 — Estado de servicio:** un cliente consulta el estado de una orden usando
  un código de seguimiento. El endpoint no requiere cuenta de personal ni expone
  datos personales.

El sistema está implementado como un **monolito modular**: una aplicación FastAPI,
un proceso de backend y una base de datos compartida. Los módulos separan los
dominios, pero no son aplicaciones independientes ni microservicios.

## Arquitectura y estructura

```text
Proyecto_Arquitectura/
├── backend/
│   ├── app/
│   │   ├── core/                       # configuración, base de datos, JWT y rate limit
│   │   ├── modules/
│   │   │   ├── technical_record/       # HU-06: expediente técnico
│   │   │   │   ├── api/                # rutas, esquemas y autorización
│   │   │   │   ├── application/        # casos de uso
│   │   │   │   ├── domain/             # entidades y contratos de dominio
│   │   │   │   └── infrastructure/    # modelos y repositorio SQLAlchemy
│   │   │   └── service_status/         # HU-07: consulta pública de estado
│   │   │       ├── api/
│   │   │       ├── application/
│   │   │       ├── domain/
│   │   │       └── infrastructure/
│   │   └── main.py                     # crea FastAPI y registra ambos módulos
│   ├── migrations/                     # historial de cambios de esquema Alembic
│   ├── tests/                          # API y datos sintéticos de prueba
│   └── requirements.txt
├── frontend/                           # interfaz web actual de HU-06
├── scripts/
│   ├── seed_demo.py                    # vehículos, reparaciones y usuario de taller
│   └── benchmark_search.py             # benchmark aislado de búsqueda
├── docs/
│   └── HU-06.md                        # decisiones y detalles del expediente
├── compose.yaml                        # MySQL 8.4 local
└── .env.example                        # plantilla de configuración
```

Las solicitudes web siguen este recorrido general:

```text
Navegador o cliente HTTP
        │ HTTP/JSON
        ▼
FastAPI (main.py y router del módulo)
        │ valida entrada, autentica/autorización si corresponde
        ▼
Caso de uso (application)
        │ aplica la operación del dominio
        ▼
Repositorio SQLAlchemy (infrastructure)
        │ lee o escribe usando una sesión
        ▼
MySQL local
```

La capa `api` recibe HTTP y valida sus datos; `application` coordina la operación;
`domain` contiene conceptos y reglas del módulo; `infrastructure` adapta esos
conceptos a SQLAlchemy y a la base de datos. `core` comparte capacidades generales
como configuración, conexión, seguridad y limitación de peticiones.

## Inicialización desde cero

### Requisitos

- Python 3.12 o superior.
- Docker y Docker Compose.
- Acceso a internet la primera vez para descargar MySQL e instalar dependencias.

### 1. Crear configuración local

Desde la carpeta `Proyecto_Arquitectura`:

```bash
cp .env.example .env
```

Edita `.env` y reemplaza, como mínimo, las contraseñas de MySQL y
`JWT_SECRET_KEY`. La clave JWT debe tener al menos 32 caracteres. Asegúrate de que
`DATABASE_URL` utilice el mismo usuario, contraseña y base que `MYSQL_USER`,
`MYSQL_PASSWORD` y `MYSQL_DATABASE`. No subas el `.env` real al repositorio.

La configuración de ejemplo conecta a MySQL en `127.0.0.1:3307`; Compose publica
ese puerto solo en la máquina local.

### 2. Crear el entorno Python e instalar dependencias

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
```

### 3. Arrancar MySQL

```bash
docker compose up -d db
docker compose ps
```

Espera a que el servicio `db` aparezca saludable antes de ejecutar la migración.
Los datos sobreviven al reinicio del contenedor porque se guardan en un volumen
Docker.

### 4. Crear o actualizar el esquema

```bash
PYTHONPATH=backend .venv/bin/alembic -c backend/alembic.ini upgrade head
```

Alembic aplica, en orden, las migraciones de [backend/migrations/versions/](backend/migrations/versions/).
La primera crea las tablas de HU-06; las siguientes modifican el esquema y agregan
la tabla `service_orders` para HU-07.

### 5. Cargar datos sintéticos y crear usuario de taller

```bash
PYTHONPATH=backend .venv/bin/python scripts/seed_demo.py
```

El script carga los vehículos y reparaciones de demostración de forma idempotente.
Luego solicita un nombre de usuario y una contraseña de al menos 12 caracteres para
crear una cuenta con rol `mechanic`. La contraseña se guarda como hash Argon2id.
Si ese usuario ya existe, el script no cambia su contraseña.

El script **no crea órdenes HU-07**. Por eso, una base recién inicializada no tendrá
un código de seguimiento consultable hasta que se registre una orden por otro medio
o se implemente la función de administración que falta.

### 6. Arrancar la aplicación

```bash
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- Interfaz interna HU-06: <http://127.0.0.1:8000/>
- Documentación interactiva de API: <http://127.0.0.1:8000/docs>
- API de HU-06: prefijo `/api/v1`
- API pública HU-07: prefijo `/api/public`

Para parar la aplicación, usa `Ctrl+C`. Para detener MySQL sin eliminar su
contenedor ni sus datos:

```bash
docker compose stop db
```

`docker compose down` elimina el contenedor, pero conserva el volumen de datos.
Evita `docker compose down -v` si quieres conservar la base local.

### Reinicialización de esquema

Para aplicar migraciones nuevas sobre una base existente, vuelve a ejecutar
`upgrade head`. Para borrar la base de demostración y todos sus datos se puede
eliminar el volumen Docker, pero esa operación es destructiva:

```bash
docker compose down -v
```

Úsala únicamente cuando realmente quieras empezar desde cero; tendrás que repetir
los pasos de MySQL, migración y carga de datos.

## Flujos de las historias de usuario

### HU-06 — Acceso y búsqueda de expediente

1. El personal abre la interfaz web servida por FastAPI. El HTML define el formulario
   de acceso y búsqueda; [frontend/app.js](frontend/app.js) conecta sus eventos con
   la API.
2. Al iniciar sesión, el navegador envía `POST /api/v1/auth/token` con usuario y
   contraseña.
3. La ruta de autenticación de
   [technical_record/api/router.py](backend/app/modules/technical_record/api/router.py)
   busca el usuario en `staff_users`, verifica que esté activo y compara su contraseña
   con el hash mediante [core/security.py](backend/app/core/security.py).
4. Si las credenciales son válidas, FastAPI devuelve un JWT con expiración. El
   frontend guarda el token en memoria y lo envía como `Authorization: Bearer ...`
   en las llamadas protegidas.
5. El personal ingresa una serie/chasis. El navegador envía
   `GET /api/v1/technical-records/by-serial/{serial_number}`.
6. La ruta pasa por `require_staff` en
   [technical_record/api/dependencies.py](backend/app/modules/technical_record/api/dependencies.py),
   que vuelve a validar el token, comprueba que el usuario exista y esté activo, y
   limita el acceso a los roles `mechanic` y `admin`.
7. El caso de uso `find_technical_record`, en
   [technical_record/application/use_cases.py](backend/app/modules/technical_record/application/use_cases.py),
   normaliza la serie. El repositorio en
   [technical_record/infrastructure/repository.py](backend/app/modules/technical_record/infrastructure/repository.py)
   busca el vehículo y recupera batería, controlador, reparaciones y observaciones.
8. FastAPI serializa el resultado con los esquemas de `api/schemas.py`; el frontend
   lo muestra como expediente. Una serie inexistente produce `404`; sin token se
   devuelve `401`, y con un rol no permitido `403`.

### HU-06 — Registrar observación técnica

1. En un expediente abierto, el mecánico escribe una observación.
2. El navegador envía
   `POST /api/v1/technical-records/{vehicle_id}/observations` con el texto y el JWT.
3. La API valida el cuerpo (hasta 2.000 caracteres) y vuelve a aplicar la
   autorización de personal.
4. `add_technical_observation` recorta el texto y rechaza contenido vacío.
5. El repositorio guarda la observación en `technical_observations`, vinculándola
   con el vehículo y el usuario autor, y confirma la transacción.
6. El frontend vuelve a solicitar el expediente y muestra la observación persistida.
   El contenido se dibuja como texto, no como HTML ejecutable.

### HU-06 — Actualizar batería y controlador

1. El personal modifica los campos en el formulario de especificaciones.
2. El navegador envía
   `PUT /api/v1/technical-records/{vehicle_id}/specifications`, incluyendo batería
   y controlador y el JWT.
3. Los esquemas Pydantic validan longitudes y tipos. La ruta transforma los valores
   en entidades y llama a `update_technical_specifications`.
4. El repositorio crea, actualiza o elimina la configuración actual de batería y
   controlador, confirma la transacción y devuelve el expediente actualizado.
5. El frontend renderiza la respuesta actualizada.

Los campos se envían como objetos completos. Enviar `null` para `battery` o
`controller` elimina la configuración actual correspondiente. Este endpoint no crea
reparaciones; el historial existente se consulta junto con el expediente.

### HU-07 — Consultar públicamente el estado

1. Un cliente HTTP envía `POST /api/public/service-status` con JSON:

   ```json
   {
     "tracking_code": "CODIGO-DE-SEGUIMIENTO"
   }
   ```

2. FastAPI valida que `tracking_code` tenga entre 6 y 32 caracteres.
3. La ruta en
   [service_status/api/router.py](backend/app/modules/service_status/api/router.py)
   consulta el limitador en memoria. Actualmente permite una consulta por minuto
   para cada código normalizado; no limita por dirección IP.
4. `lookup_public_status`, en
   [service_status/application/use_cases.py](backend/app/modules/service_status/application/use_cases.py),
   normaliza el código y llama al repositorio.
5. El repositorio calcula SHA-256 del código normalizado y busca el hash en
   `service_orders`; si encuentra la orden, carga el vehículo asociado.
6. La API responde con `status`, `message`, `vehicle_type`, `serial_number` y
   `order_code`. Si no hay coincidencia devuelve `404`; si se excede el límite
   devuelve `429`.

El endpoint es público y **no forma parte de la interfaz web actual**. No requiere
JWT. Aunque no devuelve datos personales, hoy incluye la serie del vehículo en la
respuesta.

## API disponible

La documentación exacta y los esquemas están disponibles localmente en
<http://127.0.0.1:8000/docs> cuando el servidor está encendido.

| Historia | Método y ruta | Acceso | Resultado principal |
|---|---|---|---|
| HU-06 | `POST /api/v1/auth/token` | Credenciales de personal | JWT y tiempo de expiración |
| HU-06 | `GET /api/v1/technical-records/by-serial/{serial_number}` | `mechanic` o `admin` | Vehículo, especificaciones, reparaciones y observaciones |
| HU-06 | `POST /api/v1/technical-records/{vehicle_id}/observations` | `mechanic` o `admin` | Crea una observación |
| HU-06 | `PUT /api/v1/technical-records/{vehicle_id}/specifications` | `mechanic` o `admin` | Actualiza especificaciones actuales |
| HU-07 | `POST /api/public/service-status` | Código de seguimiento | Estado público de la orden |

Ejemplo de consulta HU-07 desde la terminal:

```bash
curl -X POST http://127.0.0.1:8000/api/public/service-status \
  -H 'Content-Type: application/json' \
  -d '{"tracking_code":"CODIGO-DE-SEGUIMIENTO"}'
```

El ejemplo solo funciona si ya existe una orden con ese código. Las pruebas crean
una orden sintética `H7-TRACK-001` en una base temporal; no la insertan en MySQL local.

## Datos y persistencia

- En ejecución local, los datos viven en MySQL 8.4 en el volumen `hu06_mysql_data`
  de Compose. Detener el contenedor no borra el volumen.
- `vehicles` almacena serie/chasis, tipo y modelo. `battery_specifications` y
  `controller_configurations` guardan la configuración actual. `repair_records`
  almacena el historial. `technical_observations` guarda notas de personal, y
  `staff_users` contiene usuarios y hashes de contraseña.
- `service_orders` guarda las órdenes HU-07. El código de seguimiento se persiste
  como hash SHA-256, no como texto original.
- Las migraciones Alembic crean y modifican las tablas. Los modelos SQLAlchemy están
  dentro de `infrastructure/models.py` de cada módulo.
- [scripts/seed_demo.py](scripts/seed_demo.py) carga vehículos y reparaciones
  sintéticas y permite crear un usuario local. No carga órdenes HU-07.
- Las pruebas usan SQLite temporal y eliminan su base al terminar; no modifican la
  base MySQL local.

## Pruebas y calidad

Desde la carpeta del proyecto:

```bash
PYTHONPATH=backend:. .venv/bin/python -m pytest backend/tests -q
.venv/bin/ruff check backend scripts
PYTHONPATH=backend:. .venv/bin/mypy backend/app
```

Para ejecutar cobertura:

```bash
PYTHONPATH=backend:. .venv/bin/python -m coverage run -m pytest backend/tests
.venv/bin/python -m coverage report
```

El benchmark de búsqueda usa datos generados en una base temporal independiente:

```bash
PYTHONPATH=backend:. .venv/bin/python scripts/benchmark_search.py
```

El benchmark es una medición local y no altera MySQL. Su resultado depende del
equipo; no debe interpretarse como garantía de rendimiento en producción.

## Archivos importantes

| Archivo o carpeta | Responsabilidad |
|---|---|
| [backend/app/main.py](backend/app/main.py) | Punto de entrada FastAPI; monta las rutas HU-06/HU-07 y el frontend. |
| [frontend/index.html](frontend/index.html) y [frontend/app.js](frontend/app.js) | Interfaz interna HU-06 y llamadas HTTP que realiza el navegador. |
| [technical_record/api/router.py](backend/app/modules/technical_record/api/router.py) | Rutas HU-06: login, búsqueda, observaciones y especificaciones. |
| [technical_record/api/dependencies.py](backend/app/modules/technical_record/api/dependencies.py) | Validación del JWT, estado del usuario y roles autorizados. |
| [technical_record/application/use_cases.py](backend/app/modules/technical_record/application/use_cases.py) | Operaciones de aplicación de HU-06. |
| [technical_record/domain/entities.py](backend/app/modules/technical_record/domain/entities.py) | Entidades y contrato del repositorio HU-06. |
| [technical_record/infrastructure/models.py](backend/app/modules/technical_record/infrastructure/models.py) | Tablas SQLAlchemy principales de HU-06. |
| [technical_record/infrastructure/repository.py](backend/app/modules/technical_record/infrastructure/repository.py) | Consultas y persistencia del expediente técnico. |
| [service_status/api/router.py](backend/app/modules/service_status/api/router.py) | Endpoint HTTP público de HU-07. |
| [service_status/application/use_cases.py](backend/app/modules/service_status/application/use_cases.py) | Normalización/hash del código y operación de consulta HU-07. |
| [service_status/infrastructure/models.py](backend/app/modules/service_status/infrastructure/models.py) y [repository.py](backend/app/modules/service_status/infrastructure/repository.py) | Modelo de orden y consulta de estado en la base. |
| [backend/app/core/config.py](backend/app/core/config.py) | Lee `.env` y valida configuración. |
| [backend/app/core/database.py](backend/app/core/database.py) | Crea el motor, sesiones SQLAlchemy y dependencia de DB para FastAPI. |
| [backend/app/core/security.py](backend/app/core/security.py) | Hash Argon2id y creación/validación de JWT. |
| [backend/app/core/rate_limit.py](backend/app/core/rate_limit.py) | Limitador en memoria para el endpoint público HU-07. |
| [backend/migrations/versions/](backend/migrations/versions/) | Historial de migraciones que construye el esquema de la base. |
| [scripts/seed_demo.py](scripts/seed_demo.py) | Datos sintéticos de HU-06 y creación interactiva del usuario de taller. |
| [backend/tests/](backend/tests/) | Pruebas de API, validaciones y persistencia con SQLite temporal. |
| [docs/HU-06.md](docs/HU-06.md) | Detalle complementario del modelo y decisiones de HU-06. |

## Limitaciones conocidas

- HU-07 no tiene todavía una pantalla web pública.
- No hay endpoint protegido ni interfaz para que el personal cree órdenes, genere
  códigos de seguimiento o cambie el estado de una orden. La función de aplicación
  `create_service_order` existe, pero no está conectada a un flujo de usuario.
- La semilla de demostración no crea órdenes de servicio; por ello una instalación
  local recién cargada no tiene códigos HU-07 consultables.
- El límite HU-07 es una solicitud por minuto **por código**, guardado en memoria.
  Se reinicia cuando reinicia el proceso y no se comparte entre varias instancias.
- La respuesta pública expone la serie del vehículo y el identificador interno de la
  orden (`order_code`). Antes de usar este flujo con datos reales, conviene confirmar
  que esos campos deban ser públicos y definir un limitador adecuado al entorno.
- La tabla `service_orders` no conserva un historial de cambios de estado: almacena
  el estado y mensaje actuales.
- El proyecto es una POC local. Las credenciales y la configuración de producción,
  HTTPS, observabilidad, despliegue y escalado requieren preparación adicional.

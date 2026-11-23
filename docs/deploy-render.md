# Deploy en Render: pasos pendientes

Estado: propuesta (PR #20). Nada está creado todavía en Render ni en el Supabase de prod.
Contexto y comandos de Supabase: `docs/supabase.md`.

## 1. Supabase de producción (`iki-prod`)

Lo tiene que crear quien administra la organización de Supabase (Juan Pablo, o Franco si recibe
la invitación como owner/admin). **Nunca** pegar claves en chats, issues ni PRs.

1. Crear el proyecto `iki-prod` en la misma organización. Región **East US / North Virginia
   (`us-east-1`)**: la misma zona que el servicio de Render (`region: virginia`). Render no tiene
   región en Sudamérica; con la base en São Paulo cada consulta cruzaría el continente.
   Contraseña de DB larga, distinta de la de dev, guardada en un gestor de contraseñas.
2. Deshabilitar la Data API (`docs/supabase.md` §2).
3. En el SQL Editor, crear los roles `iki_migrator` e `iki_app` (`docs/supabase.md` §3).
4. **Connect → Session pooler (puerto 5432)** y armar dos connection strings:
   - `iki_app.<project-ref>` → `DATABASE_URL` (runtime de la app).
   - `iki_migrator.<project-ref>` → `MIGRATE_DATABASE_URL` (solo el comando de migraciones).
5. **Storage**: bucket público `iki-public`, sin políticas de escritura.
6. **Storage → S3 Connection**: generar las access keys y anotar la región.
7. Activar backups automáticos y recorrer el checklist de `docs/supabase.md` §5.

## 2. Render

1. Crear la cuenta y conectar el repo de GitHub. New → Blueprint → `render.yaml`.
2. Cargar a mano en el panel las variables marcadas `sync: false`:

| Variable | Tipo | Valor |
|---|---|---|
| `ALLOWED_HOSTS` | PÚBLICA | dominio(s) reales, sin `*` |
| `CSRF_TRUSTED_ORIGINS` | PÚBLICA | `https://dominio` |
| `SUPABASE_URL` | PÚBLICA | `https://<project-ref>.supabase.co` |
| `SUPABASE_STORAGE_REGION` | PÚBLICA | `us-east-1` |
| `DEFAULT_FROM_EMAIL` | PÚBLICA | remitente de los mails |
| `ADMIN_URL` | PRIVADA | ruta del admin, termina en `/` |
| `CONTACT_NOTIFY_EMAIL` | PRIVADA | casilla que recibe las consultas |
| `DATABASE_URL` | SECRETA | rol `iki_app` |
| `MIGRATE_DATABASE_URL` | SECRETA | rol `iki_migrator` |
| `SUPABASE_S3_ACCESS_KEY_ID` / `SUPABASE_S3_SECRET_ACCESS_KEY` | SECRETA | del paso 1.6 |
| `EMAIL_URL` | SECRETA | SMTP (ver `.env.example`) |

3. Apuntar el dominio (DNS) al servicio de Render.

## 3. Después del primer deploy

- Crear el superusuario y activar el 2FA (`setup_2fa`) desde el shell de Render.
- Confirmar que el RLS quedó aplicado (consulta de "tablas sin RLS" de `docs/supabase.md`).
- Probar el formulario de contacto de punta a punta (llega el mail de aviso).
- Probar subir una foto desde el admin y verla en el sitio.

## Cosas sin verificar (probar en el primer deploy)

- `PYTHON_VERSION=3.12.8` en `render.yaml` tiene que seguir siendo una versión disponible en Render.
- No hay `healthCheckPath`: con `SECURE_SSL_REDIRECT` el health check por HTTP podría recibir un redirect.
- `preDeployCommand` con `DATABASE_URL="$MIGRATE_DATABASE_URL"`: confirmar que la expansión de variables funciona en el comando de Render.

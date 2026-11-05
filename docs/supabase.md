# Supabase: configuración y verificación

Usamos dos proyectos: **iki-dev** (compartido entre los dos socios) e **iki-prod**.
Región sugerida: `sa-east-1` (São Paulo). Django se conecta **solo por Postgres** y por la
API S3 de Storage. El navegador nunca recibe credenciales de Supabase.

## 1. Crear los proyectos

1. Crear `iki-dev` e `iki-prod` con contraseñas de base de datos largas y distintas
   (guardarlas en un gestor de contraseñas, nunca en el repo ni en chats).
2. **Connect → Session pooler** (puerto 5432): esa es la `DATABASE_URL`.
   - Dev: va en el `.env` local de cada socio.
   - Prod: solo en las variables de entorno del hosting.
   - Si algún día se usa el *transaction pooler* (6543), poner
     `DB_DISABLE_SERVER_SIDE_CURSORS=True`.

## 2. Deshabilitar la Data API (PostgREST)

Django no usa la API REST de Supabase, así que la apagamos para que las tablas no queden
expuestas vía HTTP con la `anon key`.

- **Project Settings → Data API → desactivar "Enable Data API"** (en ambos proyectos).
- Si por algún motivo no se puede desactivar: quitar `public` de *Exposed schemas*.

### Defensa en profundidad: RLS en todas las tablas

Aunque la Data API esté apagada, habilitamos Row Level Security en **todas** las tablas de
`public` **sin políticas** para `anon` / `authenticated` (= sin acceso). El rol con el que
se conecta Django es dueño de las tablas, así que no le afecta.

> En la etapa B esto se automatiza (se aplica después de cada `migrate` y hay un comando
> que lo verifica). Mientras tanto, se puede correr a mano en el **SQL Editor**:

```sql
-- Habilitar RLS en todas las tablas de public
DO $$
DECLARE t record;
BEGIN
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t.tablename);
  END LOOP;
END $$;

-- Quitar cualquier permiso a los roles de la API
REVOKE ALL ON ALL TABLES    IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES    FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON FUNCTIONS FROM anon, authenticated;
```

### Cómo verificarlo

```sql
-- Debe devolver 0 filas: tablas de public SIN RLS
SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND NOT rowsecurity;

-- Debe devolver 0 filas: permisos de anon/authenticated sobre tablas de public
SELECT grantee, table_name, privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 'public' AND grantee IN ('anon', 'authenticated');
```

Además: **Advisors → Security Advisor** no debe mostrar el aviso "RLS disabled in public".

Prueba externa (con la Data API apagada debe fallar):
`curl https://<project-ref>.supabase.co/rest/v1/` → error, no un listado de tablas.

## 3. Usuario de base de datos con permisos mínimos (prod)

En producción no usamos el usuario `postgres` para la app:

| Rol | Uso | Permisos |
|---|---|---|
| `iki_migrator` | Solo durante el deploy (`migrate`) | Dueño del esquema de la app: DDL |
| `iki_app` | Runtime de Django | Solo `SELECT/INSERT/UPDATE/DELETE` |

```sql
-- Ejecutar como postgres en el SQL Editor de iki-prod. Contraseñas: generarlas aparte.
CREATE ROLE iki_migrator LOGIN PASSWORD '<generar>';
CREATE ROLE iki_app      LOGIN PASSWORD '<generar>';

GRANT USAGE, CREATE ON SCHEMA public TO iki_migrator;
GRANT USAGE ON SCHEMA public TO iki_app;

-- Lo que cree iki_migrator queda accesible (solo datos) para iki_app
ALTER DEFAULT PRIVILEGES FOR ROLE iki_migrator IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO iki_app;
ALTER DEFAULT PRIVILEGES FOR ROLE iki_migrator IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO iki_app;
```

- Con el pooler, el usuario se escribe `iki_app.<project-ref>`.
- El deploy corre `migrate` con la URL de `iki_migrator`; la app arranca con la de `iki_app`.
- En **dev** alcanza con un solo rol (es una base sin datos reales).

> Trade-off: es un paso más en el deploy, pero si alguien explota la app no puede borrar
> ni alterar tablas. Lo cerramos en detalle cuando elijamos el hosting.

## 4. Storage

1. **Storage → New bucket → `iki-public`**, marcado como **Public**.
   - Lectura pública por URL (`/storage/v1/object/public/iki-public/...`).
   - **No** crear políticas de INSERT/UPDATE/DELETE para `anon` ni `authenticated`:
     nadie sube desde el navegador.
   - Opcional: limitar tipos MIME (`image/webp`, `image/jpeg`, `image/png`) y tamaño máximo.
2. **Storage → Settings → S3 Connection**: habilitar y crear un **Access key**.
   Copiar `Access key ID`, `Secret access key` y la región a las variables
   `SUPABASE_S3_*` / `SUPABASE_STORAGE_REGION`. Estas claves **ignoran RLS** y dan acceso
   total al Storage: solo en el servidor.
3. Archivos privados (si algún día hacen falta): bucket **privado** aparte y URLs firmadas
   de corta duración generadas por Django. Hoy no hay ninguno (el formulario de contacto no
   acepta adjuntos).

Para usar Storage en local: `MEDIA_STORAGE=supabase` + las variables `SUPABASE_*` del
proyecto de dev. Sin eso, las imágenes se guardan en `media/` (ignorado por git).

## 5. Checklist por proyecto

- [ ] Data API deshabilitada
- [ ] Consulta de "tablas sin RLS" devuelve 0 filas (repetir después de cada deploy con migraciones)
- [ ] Security Advisor sin errores
- [ ] Bucket `iki-public` público sin políticas de escritura
- [ ] Access key S3 creada y guardada solo en `.env` / hosting
- [ ] (prod) Roles `iki_migrator` e `iki_app` creados
- [ ] (prod) Backups automáticos activos

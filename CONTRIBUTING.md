# Cómo trabajamos

Somos dos. Todo cambio entra a `main` por Pull Request revisado por el otro socio.

## Ramas

- `main` está **protegida**: no se pushea directo (el hook `no-commit-to-branch` lo frena en
  local y la branch protection en GitHub).
- Nombres: `feature/<descripcion-corta>`, `fix/<descripcion-corta>`, `chore/...`, `docs/...`.
  En minúsculas y con guiones: `feature/galeria-lightbox`, `fix/filtro-mobile`.
- Ramas cortas: mejor varios PRs chicos que uno gigante.

```bash
git switch main && git pull
git switch -c feature/mi-cambio
# ... trabajar, commitear ...
git push -u origin feature/mi-cambio
gh pr create --fill
```

## Commits convencionales

Formato: `tipo(ámbito opcional): descripción en imperativo`

| Tipo | Uso |
|---|---|
| `feat` | funcionalidad nueva |
| `fix` | corrección de bug |
| `docs` | solo documentación |
| `style` | formato, sin cambio de lógica |
| `refactor` | reestructura sin cambiar comportamiento |
| `test` | tests |
| `chore` | mantenimiento, dependencias |
| `ci` | GitHub Actions |
| `perf` | rendimiento |

Ejemplos: `feat(projects): subida múltiple de fotos en el admin`,
`fix(contact): validar teléfono con código de área`.

## Pull Requests

1. Completá la plantilla, incluido el **checklist de seguridad**.
2. La CI tiene que estar en verde: lint, gitleaks, tests, `check --deploy`, pip-audit.
3. Revisión y aprobación del otro socio. Quien abre el PR no lo aprueba.
4. Merge con **squash** (un commit por PR en `main`, con título convencional).
5. Borrar la rama después del merge.

## Antes de pushear

```bash
pre-commit run --all-files
pytest
```

Nunca uses `--no-verify` para saltear los hooks. Si gitleaks marca algo, no lo ignores:
si es un secreto real, sacalo del commit **y rotalo**.

## Trabajo con Claude Code

`CLAUDE.md` tiene las convenciones del proyecto y Claude Code lo lee automáticamente.
Si cambia una convención, actualizá `CLAUDE.md` en el mismo PR.

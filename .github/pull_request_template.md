## Qué cambia

<!-- Resumen corto. Si cierra un issue: "Closes #N". -->

## Cómo probarlo

<!-- Pasos concretos para que el otro socio lo verifique en local. -->

## Checklist

- [ ] El título del PR sigue commits convencionales (`feat:`, `fix:`, `chore:`…)
- [ ] `pytest` y `pre-commit run --all-files` pasan en local
- [ ] Probado en mobile (DevTools ~390px) si toca templates
- [ ] Si agrega dependencias: `.in` y `.txt` compilados con hashes

## Checklist de seguridad

- [ ] No hay secretos, `.env`, dumps ni datos reales de clientes/consultas en el diff
- [ ] Variables nuevas documentadas en `.env.example` como PÚBLICA / PRIVADA / SECRETA
- [ ] Sin `|safe` ni `mark_safe` sobre contenido cargado por usuarios
- [ ] Sin SQL crudo (o parametrizado y justificado)
- [ ] Formularios con CSRF; inputs validados en el servidor
- [ ] Subidas de archivos validadas por contenido, re-codificadas y sin EXIF
- [ ] Sin scripts/estilos inline ni recursos de terceros por CDN
- [ ] No se loguean datos personales ni secretos
- [ ] Si cambia settings de prod: `check --deploy` sigue sin warnings

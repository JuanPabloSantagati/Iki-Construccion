# Política de seguridad

## Reportar una vulnerabilidad

Si encontraste una vulnerabilidad en este sitio o en este repositorio, **no abras un issue
público**. Reportala de forma privada desde GitHub:

**Security → Report a vulnerability** en
<https://github.com/JuanPabloSantagati/Iki-Construccion/security/advisories/new>

Incluí, si podés: descripción, pasos para reproducirla, impacto estimado y versión o URL
afectada. Respondemos dentro de los 5 días hábiles y te avisamos cuando esté corregida.

Pedimos no acceder a datos de terceros, no degradar el servicio y darnos un plazo
razonable antes de divulgar.

## Versiones con soporte

Solo la versión desplegada desde la rama `main`.

## Si se filtra un secreto

1. **Rotarlo de inmediato** en el servicio correspondiente (Supabase, SMTP, Turnstile…).
2. Recién después, sacarlo del código. Borrar el commit no alcanza: el historial de un
   repo público puede estar copiado.
3. Revisar los logs del servicio afectado por accesos indebidos.

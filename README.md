# gestor-de-turnos-IDS

## Configuracion local de Supabase

El proyecto usa Supabase solamente desde el backend para subir imagenes de servicios a Storage. El frontend no se conecta directo a Supabase.

Para configurar Supabase en tu maquina:

1. Copiar `backend/.env.example` y renombrar la copia como `backend/.env`.
2. Completar `SUPABASE_URL`.
3. Completar `SUPABASE_KEY`.
4. Confirmar que `SUPABASE_BUCKET=Imagenes`.
5. Reiniciar Flask despues de modificar el `.env`.

Las credenciales se obtienen desde Supabase en `Project Settings -> API Keys`.
El bucket se revisa desde `Storage -> Buckets`.

Martin te tiene que agregar al proyecto para que puedas obtener las credenciales, o pasarlas directo por whatsapp.
Queda pendiente ver como levantar la variable de entorno desde docker file.

`backend/.env.example` se sube al repo para documentar las variables necesarias. `backend/.env` y cualquier otro `.env` no se suben al repo porque contienen credenciales reales. Las credenciales reales se comparten por privado o cada integrante las obtiene desde Supabase.
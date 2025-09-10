# Guía de Instalación de FitBot

Sigue estos pasos para configurar y lanzar la aplicación completa.

## 1. Prerrequisitos
- Python 3.9 o superior
- Git
- LM Studio (modelo Llama 3 local): https://lmstudio.ai/

## 2. Clonar el repositorio
```bash
git clone <URL_DE_TU_REPOSITORIO>
cd <NOMBRE_DEL_DIRECTORIO>
```

## 3. Crear entorno y dependencias
```bash
python -m venv .venv
source .venv/bin/activate   # En Windows: .venv\\Scripts\\activate
pip install -U pip
pip install -r requirements.txt
```

## 4. Configuración del modelo local
1) Abre LM Studio y descarga/carga un modelo compatible, por ejemplo: "Meta-Llama-3-8B-Instruct".
2) Inicia el servidor local (REST) en el puerto 1234.

Opcionalmente, crea un archivo `.env` en la raíz del proyecto para personalizar:
```
LM_BASE_URL=http://localhost:1234/v1
LM_API_KEY=not-needed
LM_MODEL=Meta-Llama-3-8B-Instruct
LM_TEMPERATURE=0.7
LM_MAX_TOKENS=1500
```

## 5. Ejecutar el servidor web
```bash
uvicorn fitbot.app:app --reload
```
Luego abre tu navegador en:
```
http://127.0.0.1:8000/
```

## 6. Solución de problemas
- "No pude conectarme al motor de IA local": verifica que LM Studio esté corriendo en `LM_BASE_URL` y que el modelo esté cargado.
- Error de WebSocket/Reconexion: revisa que `uvicorn` siga activo y que no haya firewalls bloqueando `ws://`.
- Archivos pesados: los videos de fondo no están versionados por defecto; puedes añadir los tuyos en `static/` o usar un fondo estático.

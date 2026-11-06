# Transcribir notas de voz de WhatsApp

Las notas de voz de WhatsApp suelen llegar como OGG con audio Opus. Para preparar los hallazgos de stakeholders, `tools/transcribe_whatsapp_audio.py` convierte cada archivo a WAV PCM, mono, 16 kHz y lo transcribe localmente en español con faster-whisper. El audio permanece en el equipo.

## Preparar el entorno local

Usa un entorno virtual fuera del repositorio para mantener las dependencias de reconocimiento fuera de la aplicación:

```bash
python3 -m venv ~/.venvs/arcoenergy-audio
~/.venvs/arcoenergy-audio/bin/pip install -r requirements-audio.txt
```

El archivo de dependencias fija versiones compatibles de faster-whisper, PyAV e imageio-ffmpeg. La primera ejecución descarga el modelo seleccionado desde Hugging Face. El modelo predeterminado es `small`, con cómputo CPU `int8`; el modelo queda en la caché local.

## Transcribir

```bash
HF_HUB_DISABLE_XET=1 ~/.venvs/arcoenergy-audio/bin/python tools/transcribe_whatsapp_audio.py \
  "/ruta/WhatsApp Ptt 1.ogg" \
  "/ruta/WhatsApp Ptt 2.ogg"
```

El WAV intermedio se crea en un directorio temporal y se elimina al terminar. Para conservar los WAV convertidos, proporciona un directorio privado fuera del repositorio:

```bash
HF_HUB_DISABLE_XET=1 ~/.venvs/arcoenergy-audio/bin/python tools/transcribe_whatsapp_audio.py \
  --wav-dir "$HOME/Downloads/arcoenergy-audio-wav" \
  "/ruta/WhatsApp Ptt 1.ogg"
```

## Flujo de investigación

1. Transcribir cada audio y mantener el nombre del archivo como referencia de origen.
2. Revisar la transcripción contra la nota de voz; corregir nombres propios, cantidades y términos que el reconocimiento no haya entendido bien.
3. Crear user story cards solo después de validar el texto. Registrar stakeholder, archivo fuente, iteración y versión de la tarjeta.
4. No guardar automáticamente transcripciones ni audios personales en el repositorio. Al persistirlos en el sistema de investigación, definir antes los permisos, consentimiento, retención y tratamiento de datos personales.

Se pueden elegir otros modelos y códigos de idioma con `--model` y `--language`. El modelo `small` es una configuración inicial; la transcripción requiere revisión humana antes de usarla como fuente de una tarjeta.

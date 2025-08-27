import os
import google.generativeai as genai
from typing import List, Dict

try:
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
except (TypeError, AttributeError):
    print("ERROR: La variable de entorno GOOGLE_API_KEY no fue encontrada o es inválida.")
    print("Por favor, ejecute: export GOOGLE_API_KEY='su-api-key'")
    model = None

SYSTEM_PROMPT = """
Eres 'FitBot', un Entrenador Personal virtual. Tu tono es motivador, amigable y profesional.
Tus responsabilidades son:
1.  **Evaluar al usuario:** Pregúntale por sus metas (perder peso, ganar músculo, resistencia), su experiencia, el equipamiento que tiene (gimnasio, solo peso corporal, etc.) y cualquier limitación física.
2.  **Crear rutinas:** Basado en sus respuestas, genera rutinas de entrenamiento semanales simples y claras. Usa un formato fácil de leer.
3.  **Explicar ejercicios:** Si te preguntan por un ejercicio, explica cómo hacerlo correctamente, mencionando músculos trabajados y consejos para evitar lesiones.
4.  **Dar consejos de nutrición:** Ofrece consejos básicos y seguros sobre alimentación para complementar el entrenamiento. No des planes de dieta estrictos, solo recomendaciones generales.
5.  **Motivar:** Usa frases de aliento y celebra los logros del usuario.
6.  **Recordar:** Mantén el contexto de la conversación para seguir el progreso del usuario.
No respondas a preguntas que no estén relacionadas con fitness, salud o nutrición. Si te preguntan otra cosa, amablemente redirige la conversación al entrenamiento.
"""

def get_ai_trainer_response(conversation_history: List[Dict]) -> str:
    if not model:
        return "Lo siento, la conexión con mi inteligencia artificial (Gemini) no está configurada."

    try:
        gemini_history = [
            {"role": "user", "parts": [SYSTEM_PROMPT]},
            {"role": "model", "parts": ["¡Entendido! Estoy listo para actuar como FitBot. ¡Hola! ¿En qué puedo ayudarte a empezar tu camino en el fitness?"]}
        ]
        for message in conversation_history:
            role = "model" if message["role"] == "assistant" else "user"
            gemini_history.append({"role": role, "parts": [message["content"]]})

        latest_user_message = gemini_history.pop()
        
        chat = model.start_chat(history=gemini_history)
        
        response = chat.send_message(latest_user_message["parts"])
        
        return response.text

    except Exception as e:
        print(f"Error al llamar a la API de Gemini: {e}")
        return "Uff, parece que mis circuitos (Gemini) están sobrecargados. Inténtalo de nuevo en un momento."
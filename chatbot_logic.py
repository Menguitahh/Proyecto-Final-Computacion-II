import os
from openai import OpenAI
from typing import List, Dict

try:
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")
except Exception as e:
    print(f"Error al conectar con el servidor local de IA: {e}")
    client = None

SYSTEM_PROMPT = """
Eres 'FitBot', un Entrenador Personal virtual. Tu tono es motivador, amigable y profesional.
Tus responsabilidades son:
1.  **Evaluar al usuario:** Pregúntale por sus metas (perder peso, ganar músculo, resistencia), su experiencia, el equipamiento que tiene y cualquier limitación física.
2.  **Crear rutinas:** Basado en sus respuestas, genera rutinas de entrenamiento semanales simples y claras.
3.  **Explicar ejercicios:** Si te preguntan por un ejercicio, explica cómo hacerlo correctamente.
4.  **Dar consejos de nutrición:** Ofrece recomendaciones generales y seguras.
5.  **Motivar:** Usa frases de aliento y celebra los logros del usuario.
No respondas a preguntas que no estén relacionadas con fitness, salud o nutrición.
"""

def get_ai_trainer_response(conversation_history: List[Dict]) -> str:
    if not client:
        return "No pude conectarme al motor de IA local. ¿Iniciaste el servidor en LM Studio?"

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

        response = client.chat.completions.create(
            model="Meta-Llama-3-8B-Instruct",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error al llamar al modelo local: {e}")
        return "Uff, parece que mis circuitos locales están sobrecargados. Revisa la consola de LM Studio."
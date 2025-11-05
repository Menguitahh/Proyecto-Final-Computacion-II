RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

COLOR_USER = "\033[96m"
COLOR_PROMPT = COLOR_USER
COLOR_BOT = "\033[95m"
COLOR_INFO = "\033[94m"
COLOR_SUCCESS = "\033[92m"
COLOR_WARN = "\033[93m"
COLOR_ERROR = "\033[91m"

USER_TAG = f"{COLOR_USER}{BOLD}🧑 Vos{RESET}"
USER_CONT = f"{COLOR_USER}│{RESET}"
BOT_TAG = f"{COLOR_BOT}{BOLD}🤖 FitBot{RESET}"
BOT_CONT = f"{COLOR_BOT}│{RESET}"
INFO_TAG = f"{COLOR_INFO}{BOLD}ℹ{RESET}"

PROMPT_ARROW = f"{COLOR_PROMPT}> {RESET}"

WELCOME_MESSAGE = (
    f"{COLOR_BOT}{BOLD}¡Hola! Soy FitBot (modo TCP){RESET}\n"
    f"{COLOR_INFO}Contame en qué puedo ayudarte. Recordá: "
    f"{COLOR_USER}/clear{RESET}{COLOR_INFO} borra el historial guardado y "
    f"{COLOR_USER}/quit{RESET}{COLOR_INFO} termina la sesión.{RESET}"
)

FALLBACK_MESSAGE = f"{COLOR_ERROR}No pude generar respuesta ahora. Intentá nuevamente.{RESET}"

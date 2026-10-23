"""
Claude Prompt Engineering & Context Assembly Engine.
Transforms user prompts and optimized files into Anthropic-compliant prompts:
- Uses canonical XML tags (<documents>, <instructions>, <constraints>).
- Injects zero-stall guardrails: forbids unnecessary back-and-forth clarifying questions.
- Eliminates conversational filler (throat-clearing) to save expensive output tokens.
- Positions long context before prompt instructions (Anthropic attention best practice).
"""
import re
from typing import List, Dict, Optional, Any

class ClaudePromptEngineer:
    """
    Applies Anthropic Claude Prompt Engineering best practices to maximize
    first-turn accuracy, prevent conversational stalls, and minimize input/output tokens.
    """

    TASK_PROFILES = {
        "analysis": {
            "role": "Analista Senior de Datos y Estrategia",
            "verbs": "analizar, evaluar, detectar anomalías y patrones",
            "directives": "Identifica tendencias clave, anomalías, métricas destacadas y correlaciones de alto impacto."
        },
        "code": {
            "role": "Ingeniero de Software Principal y Auditor de Seguridad",
            "verbs": "revisar, refactorizar, optimizar y auditar",
            "directives": "Examina la lógica, posibles vulnerabilidades, cuellos de botella de rendimiento y correcciones directas."
        },
        "summary": {
            "role": "Consultor Ejecutivo y Síntesis de Documentos",
            "verbs": "sintetizar, extraer puntos clave y resumir",
            "directives": "Extrae los hechos críticos, decisiones, cifras clave y conclusiones ejecutivas sin redundancia."
        },
        "extraction": {
            "role": "Especialista en Extracción Estructurada de Información",
            "verbs": "extraer, estructurar y tabular",
            "directives": "Extrae rigurosamente todas las entidades y datos relevantes sin omitir cifras ni registros."
        },
        "general": {
            "role": "Asistente Experto de Alta Precisión",
            "verbs": "responder con rigor y exhaustividad",
            "directives": "Responde de forma completa, precisa y directamente accionable."
        }
    }

    @classmethod
    def detect_task_type(cls, prompt: str) -> str:
        p = prompt.lower()
        if any(w in p for w in ["código", "funcion", "script", "bug", "error", "refactor", "python", "javascript", "sql", "api", "test"]):
            return "code"
        if any(w in p for w in ["analiza", "patron", "tendencia", "metrica", "kpi", "anomalia", "datos", "compar"]):
            return "analysis"
        if any(w in p for w in ["resume", "resumen", "sintesis", "puntos clave", "conclusiones", "executive"]):
            return "summary"
        if any(w in p for w in ["extrae", "tabla", "lista de", "json", "csv", "registros"]):
            return "extraction"
        return "general"

    @classmethod
    def enhance_prompt(
        cls,
        user_prompt: str,
        task_type: str = "auto",
        prevent_stalls: bool = True,
        ban_filler: bool = True
    ) -> str:
        """
        Rewrites a raw user prompt into an Anthropic-optimized instruction block.
        """
        clean_user_prompt = user_prompt.strip()
        if not clean_user_prompt:
            clean_user_prompt = "Analiza detalladamente la información suministrada y extrae los hallazgos principales."

        if task_type == "auto":
            task_type = cls.detect_task_type(clean_user_prompt)

        profile = cls.TASK_PROFILES.get(task_type, cls.TASK_PROFILES["general"])

        instructions = []
        instructions.append(f"Actúa como un {profile['role']}.")
        instructions.append(f"Tu objetivo principal es: {clean_user_prompt}.")
        instructions.append(profile['directives'])

        return "\n".join(instructions)

    @classmethod
    def assemble_payload(
        cls,
        user_prompt: str,
        documents: List[Dict[str, str]],
        task_type: str = "auto",
        prevent_stalls: bool = True,
        ban_filler: bool = True,
        custom_instructions: Optional[str] = None
    ) -> str:
        """
        Assembles the complete Anthropic-standard context payload.
        Structure:
        1. <documents> (Placed first for optimal attention distribution)
        2. <instructions> (Clear task description with role)
        3. <constraints> (Token-saving guardrails & zero-stall directives)
        """
        sections = []

        # 1. Documents Block (Anthropic best practice: documents go BEFORE instructions)
        if documents:
            sections.append("<documents>")
            for idx, doc in enumerate(documents, 1):
                name = doc.get("name", f"Documento_{idx}")
                content = doc.get("content", "").strip()
                sections.append(f'<document index="{idx}" source="{name}">')
                sections.append(content)
                sections.append("</document>")
            sections.append("</documents>\n")

        # 2. Enhanced Instructions Block
        enhanced_instructions = cls.enhance_prompt(
            user_prompt,
            task_type=task_type,
            prevent_stalls=prevent_stalls,
            ban_filler=ban_filler
        )
        if custom_instructions:
            enhanced_instructions += f"\n{custom_instructions.strip()}"

        sections.append("<instructions>")
        sections.append(enhanced_instructions)
        sections.append("</instructions>\n")

        # 3. Strict Guardrails & Token-Saving Constraints
        constraints = [
            "<constraints>",
        ]

        if prevent_stalls:
            constraints.append(
                "- RESOLUCIÓN DIRECTA (CERO PREGUNTAS): No te detengas a hacer preguntas aclaratorias. "
                "Si algún aspecto es ambiguo o incompleto, adopta la suposición profesional más razonable, "
                "especifícala brevemente y entrega la respuesta final completa en esta única respuesta."
            )

        if ban_filler:
            constraints.append(
                "- CERO RELLENO CONVERSACIONAL (AHORRO DE TOKENS): No incluyas frases introductorias "
                "ni de cortesía (como '¡Por supuesto!', 'He analizado tus documentos...', 'A continuación te presento...'). "
                "Comienza directamente con el contenido y los datos de la respuesta."
            )

        constraints.append(
            "- DENSIDAD INFORMATIVA: Prioriza la concisión estructurada, utilizando viñetas y tablas "
            "cuando proceda para maximizar la relación señal/ruido."
        )
        constraints.append("</constraints>")

        sections.append("\n".join(constraints))

        return "\n".join(sections)

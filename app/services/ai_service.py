"""
🤖 Servicio de Integración con OpenAI
Extrae intención de mensajes naturales para descarga de archivos
"""

import json
import logging
from typing import Dict, Any, Optional, List
from app.config import Config
from app.utils.file_types import get_todos_subtipos, get_categoria_nombre, get_subtipo_nombre
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AIService:
    """Servicio para integración con OpenAI"""
    
    def __init__(self):
        self.openai_key = Config.OPENAI_API_KEY
        self.client = None
        
        # Log de diagnóstico
        key_status = f"presente ({self.openai_key[:8]}...)" if self.openai_key else "NO configurada"
        logger.info(f"🔧 AIService - API Key: {key_status}")
        
        # Intentar inicializar OpenAI si hay API key
        if self.openai_key:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=self.openai_key)
                logger.info("✅ OpenAI AIService inicializado correctamente")
            except ImportError as e:
                logger.warning(f"⚠️ openai no instalado: {e}")
            except Exception as e:
                logger.error(f"❌ Error inicializando OpenAI: {e}")
        else:
            logger.warning("⚠️ OPENAI_API_KEY no configurada - AIService no disponible")
    
    async def extract_file_intent(
        self,
        mensaje: str,
        empresas_usuario: List[Dict[str, Any]],
        historial: Optional[List[Dict]] = None,
        sesion_activa: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Extrae intención de descarga de archivos usando OpenAI
        
        Args:
            mensaje: Mensaje del usuario
            empresas_usuario: Lista de empresas del usuario [{"id": "...", "nombre": "..."}]
            historial: Últimas conversaciones (opcional)
            sesion_activa: Sesión activa de descarga (opcional) ← CONTEXTO IMPORTANTE
        
        Returns:
            {
                "categoria": "legal" | "financiero" | null,
                "subtipo": "reporte_mensual" | "estatutos_empresa" | ... | null,
                "empresa": "Orbit" | null,  # null si solo tiene 1 empresa
                "periodo": "2024-05" | null,
                "confianza": 0.85
            }
        """
        if not self.client:
            return {"confianza": 0.0}  # Sin IA disponible
        
        try:
            # Obtener tipos válidos dinámicamente
            tipos_validos = get_todos_subtipos()
            
            # Construir prompt con contexto
            prompt = self._build_extraction_prompt(
                mensaje, empresas_usuario, historial, sesion_activa, tipos_validos
            )
            
            # Llamar a OpenAI
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Modelo económico
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente que extrae información de solicitudes de archivos. Responde SOLO en JSON válido."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Bajo para respuestas consistentes
                response_format={"type": "json_object"}
            )
            
            # Parsear respuesta
            result = json.loads(response.choices[0].message.content)
            
            # Validar y normalizar resultado
            return self._validate_and_normalize_result(result, empresas_usuario)
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo intención con IA: {e}")
            return {"confianza": 0.0}  # Fallback: sin confianza
    
    async def extract_periodo_from_text(
        self,
        texto: str,
        historial: Optional[List[Dict]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extraer período de texto en lenguaje natural usando IA
        
        Args:
            texto: Texto del usuario (ej: "mayo 2024", "marzo del año pasado", "2024-05")
            historial: Últimas conversaciones (opcional)
        
        Returns:
            {
                "periodo": "YYYY-MM",
                "confianza": 0.85,
                "interpretacion": "explicación breve"
            } o None si falla
        """
        if not self.client:
            # Fallback: intentar parsear manualmente
            return self._parse_periodo_manual(texto)
        
        try:
            mes_actual = datetime.now().strftime("%Y-%m")
            mes_anterior = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
            fecha_actual = datetime.now()
            año_actual = fecha_actual.year
            mes_actual_num = fecha_actual.month
            
            # Construir contexto de historial
            historial_texto = ""
            if historial:
                historial_texto = "\n".join([
                    f"- {h.get('mensaje', '')[:100]}"
                    for h in historial[-3:]  # Últimas 3 conversaciones
                ])
            
            prompt = f"""Analiza el siguiente texto y extrae el período en formato YYYY-MM.

Texto del usuario: "{texto}"

CONTEXTO:
- Fecha actual: {fecha_actual.strftime('%d de %B de %Y')}
- Mes actual: {mes_actual} ({fecha_actual.strftime('%B %Y')})
- Mes anterior: {mes_anterior}
- Año actual: {año_actual}
- Mes actual (número): {mes_actual_num}

Historial reciente:
{historial_texto if historial_texto else "No hay historial previo"}

EJEMPLOS DE INTERPRETACIÓN:
- "mayo 2024" → "2024-05"
- "marzo del año pasado" → "2023-03"
- "el mes pasado" → {mes_anterior}
- "este mes" → {mes_actual}
- "2024-05" → "2024-05"
- "mayo" (sin año) → "2024-05" si estamos en 2024, o "2023-05" si ya pasó mayo
- "hace dos meses" → calcular desde mes actual

INSTRUCCIONES:
1. Extrae el período en formato YYYY-MM
2. Si el usuario dice solo el mes sin año, asume el año más reciente posible
3. Si dice "mes pasado" o "mes anterior", usa {mes_anterior}
4. Si dice "este mes" o "mes actual", usa {mes_actual}
5. Calcula confianza (0.0 a 1.0) basado en qué tan claro es el texto
6. Proporciona una interpretación breve

Responde SOLO en JSON con este formato:
{{
    "periodo": "YYYY-MM" | null,
    "confianza": 0.0 a 1.0,
    "interpretacion": "explicación breve"
}}"""
            
            # Llamar a OpenAI
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente que extrae períodos de fechas de texto en lenguaje natural. Responde SOLO en JSON válido."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Muy bajo para fechas precisas
                response_format={"type": "json_object"}
            )
            
            # Parsear respuesta
            result = json.loads(response.choices[0].message.content)
            
            # Validar formato YYYY-MM
            periodo = result.get('periodo')
            if periodo:
                try:
                    datetime.strptime(periodo, "%Y-%m")
                    return {
                        "periodo": periodo,
                        "confianza": max(0.0, min(1.0, float(result.get('confianza', 0.5)))),
                        "interpretacion": result.get('interpretacion', '')
                    }
                except ValueError:
                    logger.warning(f"⚠️ Período inválido extraído: {periodo}")
                    # Fallback a parseo manual
                    return self._parse_periodo_manual(texto)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo período con IA: {e}")
            # Fallback a parseo manual
            return self._parse_periodo_manual(texto)
    
    def _parse_periodo_manual(self, texto: str) -> Optional[Dict[str, Any]]:
        """
        Parsear período manualmente sin IA (fallback)
        
        Args:
            texto: Texto del usuario
        
        Returns:
            {"periodo": "YYYY-MM", "confianza": 0.5, "interpretacion": "..."} o None
        """
        texto_lower = texto.lower().strip()
        ahora = datetime.now()
        año_actual = ahora.year
        mes_actual = ahora.month
        
        # Intentar formato YYYY-MM directamente
        import re
        match = re.match(r'(\d{4})-(\d{2})', texto)
        if match:
            año, mes = match.groups()
            try:
                datetime(int(año), int(mes), 1)
                return {
                    "periodo": f"{año}-{mes}",
                    "confianza": 0.9,
                    "interpretacion": f"Formato YYYY-MM detectado: {año}-{mes}"
                }
            except ValueError:
                pass
        
        # Mapeo de meses en español
        meses_es = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        # Detectar "año pasado" o "año anterior"
        año_pasado = None
        if 'año pasado' in texto_lower or 'año anterior' in texto_lower or 'del año pasado' in texto_lower:
            año_pasado = año_actual - 1
        
        # Buscar mes en texto
        for mes_nombre, mes_num in meses_es.items():
            if mes_nombre in texto_lower:
                # Buscar año
                año_match = re.search(r'(\d{4})', texto)
                
                if año_match:
                    año = int(año_match.group(1))
                elif año_pasado is not None:
                    # Si se mencionó "año pasado", usar año anterior
                    año = año_pasado
                else:
                    # Si el mes ya pasó este año y no se especificó año, usar año actual
                    if mes_num < mes_actual:
                        año = año_actual
                    else:
                        año = año_actual
                
                periodo = f"{año}-{mes_num:02d}"
                interpretacion = f"Mes detectado: {mes_nombre} {año}"
                if año_pasado is not None:
                    interpretacion += " (año pasado)"
                
                return {
                    "periodo": periodo,
                    "confianza": 0.75 if año_pasado is not None else 0.7,
                    "interpretacion": interpretacion
                }
        
        # Palabras clave
        if 'mes pasado' in texto_lower or 'mes anterior' in texto_lower:
            mes_anterior = (ahora.replace(day=1) - timedelta(days=1))
            periodo = mes_anterior.strftime("%Y-%m")
            return {
                "periodo": periodo,
                "confianza": 0.8,
                "interpretacion": "Mes anterior detectado"
            }
        
        if 'este mes' in texto_lower or 'mes actual' in texto_lower:
            periodo = ahora.strftime("%Y-%m")
            return {
                "periodo": periodo,
                "confianza": 0.8,
                "interpretacion": "Mes actual detectado"
            }
        
        return None
    
    def _build_extraction_prompt(
        self,
        mensaje: str,
        empresas_usuario: List[Dict],
        historial: Optional[List],
        sesion_activa: Optional[Dict],
        tipos_validos: Dict
    ) -> str:
        """Construir prompt estructurado para OpenAI"""
        
        # Preparar lista de empresas
        empresas_nombres = [e['nombre'] for e in empresas_usuario]
        tiene_una_empresa = len(empresas_usuario) == 1
        
        # Preparar historial (últimas 3 conversaciones)
        historial_texto = ""
        if historial:
            historial_texto = "\n".join([
                f"- Usuario: {h.get('mensaje', '')[:100]}"
                for h in historial[:3]
            ])
        
        # Preparar sesión activa
        sesion_texto = ""
        if sesion_activa:
            sesion_data = sesion_activa.get('data', {})
            sesion_texto = f"""
Sesión activa de descarga:
- Estado: {sesion_activa.get('estado', 'N/A')}
- Datos previos: {json.dumps(sesion_data, ensure_ascii=False)}
"""
        
        # Preparar tipos válidos
        tipos_texto = ""
        for categoria, datos in tipos_validos.items():
            categoria_nombre = get_categoria_nombre(categoria)
            subtipos = datos['subtipos']
            tipos_texto += f"\nCategoría {categoria_nombre}:\n"
            for subtipo in subtipos:
                subtipo_nombre = get_subtipo_nombre(categoria, subtipo)
                tipos_texto += f"  - {subtipo} ({subtipo_nombre})\n"
        
        # Mes actual y anterior
        mes_actual = datetime.now().strftime("%Y-%m")
        mes_anterior = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        
        prompt = f"""Analiza el siguiente mensaje de un usuario que quiere descargar archivos.

Mensaje del usuario: "{mensaje}"

CONTEXTO:
- Empresas disponibles: {empresas_nombres}
- Tiene solo 1 empresa: {tiene_una_empresa}
- Mes actual: {mes_actual}
- Mes anterior: {mes_anterior}
{sesion_texto}
Historial reciente:
{historial_texto if historial_texto else "No hay historial previo"}

TIPOS DE ARCHIVO VÁLIDOS (usa EXACTAMENTE estos nombres):
{tipos_texto}

INSTRUCCIONES:
1. Extrae la categoría (legal o financiero) y el subtipo EXACTO de la lista arriba
2. Si el usuario tiene SOLO 1 empresa, NO extraigas empresa (retorna null)
3. Si el usuario tiene múltiples empresas y menciona una, extrae el nombre
4. Extrae el período en formato YYYY-MM o indica "mes_actual" o "mes_anterior"
5. Calcula confianza (0.0 a 1.0) basado en qué tan claro es el mensaje

IMPORTANTE:
- Usa los nombres EXACTOS de subtipos (ej: "reporte_mensual", "estatutos_empresa")
- Si menciona "cartola" o "factura", mapea a tipos válidos (reporte_mensual, estados_financieros, etc.)
- Si tiene 1 empresa, empresa debe ser null

Responde SOLO en JSON con este formato:
{{
    "categoria": "legal" | "financiero" | null,
    "subtipo": "reporte_mensual" | "estatutos_empresa" | ... | null,
    "empresa": "nombre_empresa" | null,
    "periodo": "YYYY-MM" | "mes_actual" | "mes_anterior" | null,
    "confianza": 0.85
}}"""
        
        return prompt
    
    def _validate_and_normalize_result(
        self,
        result: Dict[str, Any],
        empresas_usuario: List[Dict]
    ) -> Dict[str, Any]:
        """Validar y normalizar resultado de IA"""
        
        # Validar estructura básica
        if not isinstance(result, dict):
            return {"confianza": 0.0}
        
        # Normalizar período
        periodo = result.get('periodo')
        if periodo:
            if periodo == "mes_actual":
                periodo = datetime.now().strftime("%Y-%m")
            elif periodo == "mes_anterior":
                mes_anterior = datetime.now().replace(day=1) - timedelta(days=1)
                periodo = mes_anterior.strftime("%Y-%m")
            elif isinstance(periodo, str) and len(periodo) == 7:
                # Validar formato YYYY-MM
                try:
                    datetime.strptime(periodo, "%Y-%m")
                except ValueError:
                    periodo = None
        
        # Si tiene solo 1 empresa, forzar empresa a null
        if len(empresas_usuario) == 1:
            result['empresa'] = None
        
        # Validar empresa si se especificó
        if result.get('empresa'):
            empresas_nombres = [e['nombre'].lower() for e in empresas_usuario]
            if result['empresa'].lower() not in empresas_nombres:
                # Empresa no coincide, reducir confianza
                result['confianza'] = result.get('confianza', 0.5) * 0.5
                result['empresa'] = None
        
        # Asegurar confianza en rango válido
        confianza = result.get('confianza', 0.0)
        result['confianza'] = max(0.0, min(1.0, float(confianza)))
        
        # Actualizar período normalizado
        result['periodo'] = periodo
        
        return result
    
    async def answer_question_with_context(
        self,
        pregunta: str,
        reportes_financieros: List[Dict],
        reportes_cfo: List[Dict],
        historial: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Responder pregunta usando contexto de reportes financieros y CFO
        
        Args:
            pregunta: Pregunta del usuario
            reportes_financieros: Lista de reportes financieros disponibles
            reportes_cfo: Lista de reportes CFO disponibles
            historial: Historial de conversación (opcional)
        
        Returns:
            {
                "respuesta": "texto de respuesta",
                "confianza": 0.85,
                "puede_responder": True,
                "fuentes_usadas": ["reporte_mensual_2024-05", "reporte_cfo_2024"]
            }
        """
        if not self.client:
            return {
                "respuesta": "Lo siento, el servicio de IA no está disponible.",
                "confianza": 0.0,
                "puede_responder": False,
                "fuentes_usadas": []
            }
        
        try:
            # Construir contexto de reportes
            contexto_reportes = self._build_reportes_context(reportes_financieros, reportes_cfo)
            
            # Construir historial de conversación
            historial_texto = ""
            if historial:
                historial_texto = "\n".join([
                    f"- Usuario: {h.get('mensaje', '')[:200]}\n- Bot: {h.get('respuesta', '')[:200]}"
                    for h in historial[-5:]  # Últimas 5 interacciones
                ])
            
            # Construir prompt para responder pregunta
            prompt = f"""Eres un asistente financiero experto. Responde la pregunta del usuario usando ÚNICAMENTE la información disponible en los reportes financieros y reportes CFO proporcionados.

CONTEXTO DISPONIBLE:
{contexto_reportes}

HISTORIAL DE CONVERSACIÓN:
{historial_texto if historial_texto else "No hay historial previo"}

PREGUNTA DEL USUARIO: "{pregunta}"

INSTRUCCIONES:
1. Responde SOLO usando la información disponible en los reportes proporcionados
2. Si la información NO está disponible en los reportes, indica claramente que no puedes responder con la información disponible
3. Sé preciso y conciso
4. Si mencionas números o datos, indica de qué reporte provienen
5. Si no puedes responder, indica que necesitas más información o que debes consultar con un especialista

IMPORTANTE:
- Si la pregunta requiere información que NO está en los reportes proporcionados, responde: "No puedo responder esta pregunta con la información disponible en los reportes. Te recomiendo contactar con el equipo de ayuda para obtener más información."
- Si puedes responder parcialmente, indica qué información falta

Responde en formato JSON:
{{
    "respuesta": "tu respuesta aquí",
    "confianza": 0.85,
    "puede_responder": true,
    "fuentes_usadas": ["reporte_mensual_2024-05", "reporte_cfo_2024"]
}}"""
            
            # Llamar a OpenAI
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente financiero experto. Responde preguntas usando SOLO la información proporcionada en los reportes. Si no puedes responder, indica claramente que necesitas más información."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parsear respuesta
            result = json.loads(response.choices[0].message.content)
            
            # Validar estructura
            if not isinstance(result, dict):
                return {
                    "respuesta": "Error procesando la respuesta.",
                    "confianza": 0.0,
                    "puede_responder": False,
                    "fuentes_usadas": []
                }
            
            # Asegurar campos requeridos
            result.setdefault("respuesta", "No pude generar una respuesta.")
            result.setdefault("confianza", 0.0)
            result.setdefault("puede_responder", True)
            result.setdefault("fuentes_usadas", [])
            
            # Validar confianza
            confianza = result.get("confianza", 0.0)
            result["confianza"] = max(0.0, min(1.0, float(confianza)))
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error respondiendo pregunta con IA: {e}")
            return {
                "respuesta": "Lo siento, hubo un error procesando tu pregunta. Por favor, intenta de nuevo o contacta con ayuda.",
                "confianza": 0.0,
                "puede_responder": False,
                "fuentes_usadas": []
            }
    
    async def answer_as_aca_qa(
        self,
        pregunta: str,
        empresa_nombre: str,
        reportes_financieros: List[Dict],
        reportes_cfo: List[Dict],
        historial: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Responder pregunta usando el rol ACA_QA (Analista de Consultas Q&A)
        
        Args:
            pregunta: Pregunta del usuario
            empresa_nombre: Nombre de la empresa activa
            reportes_financieros: Lista de reportes financieros disponibles
            reportes_cfo: Lista de reportes CFO disponibles
            historial: Historial de conversación (opcional)
        
        Returns:
            {
                "respuesta": "texto de respuesta",
                "requiere_ticket": False,
                "motivo_ticket": None
            }
        """
        # System prompt de ACA_QA
        system_prompt = f"""Eres ACA_QA, un Analista de Consultas para un bot financiero-contable. Tu trabajo es responder preguntas y, si la solicitud implica acciones, riesgo o falta información, indicar que se debe escalar a revisión humana.

EMPRESA ACTIVA: {empresa_nombre}
Solo puedes responder sobre esta empresa. Si el usuario pregunta sobre otra empresa, indica que debe cambiar de empresa primero.

Objetivo principal:
• Responder preguntas con información verificada y específica de la empresa seleccionada.
• Nunca ejecutar acciones críticas ni modificar datos contables.
• Mantener trazabilidad: justificar respuestas con IDs / referencias internas cuando existan.

Reglas duras (no romper):

1. Scope por empresa obligatorio
   • Solo puedes usar datos de la empresa activa ({empresa_nombre}).
   • Si el usuario pide "la otra empresa", indica que debe cambiar de empresa.

2. Modo / Proceso
   • Estás siempre en el proceso: Q&A (consultas).
   • No puedes mezclar procesos (pagos, cierre, clasificar, etc.).

3. Acciones prohibidas
   • Prohibido: pagar, transferir, cerrar períodos, emitir documentos tributarios, borrar o modificar registros.
   • Si la solicitud requiere algo de eso: indica que requiere revisión humana.

4. Calidad de respuesta
   • Si respondes: entrega respuesta breve + bullets + (si existe) IDs o referencias.
   • Si no estás seguro o faltan datos: indica claramente qué falta.

Responde siempre en español, de forma clara y concisa."""

        if not self.client:
            logger.warning(f"⚠️ ACA_QA: Cliente OpenAI no disponible. API Key configurada: {bool(self.openai_key)}")
            return {
                "respuesta": "⚠️ El servicio de IA no está disponible. Por favor, contacta al administrador.",
                "requiere_ticket": False,
                "motivo_ticket": None
            }
        
        try:
            # Construir contexto de reportes
            contexto_reportes = self._build_reportes_context(reportes_financieros, reportes_cfo)
            
            # Construir historial de conversación
            historial_texto = ""
            if historial:
                historial_texto = "\n".join([
                    f"- Usuario: {h.get('mensaje', '')[:150]}"
                    for h in historial[-5:]
                ])
            
            # Construir prompt del usuario
            user_prompt = f"""CONTEXTO DISPONIBLE DE {empresa_nombre}:
{contexto_reportes}

HISTORIAL RECIENTE:
{historial_texto if historial_texto else "No hay historial previo"}

PREGUNTA DEL USUARIO: "{pregunta}"

Responde de forma clara y concisa. Si no tienes información suficiente, indícalo claramente.
Si la pregunta requiere una acción (pagar, transferir, cerrar período, etc.), indica que requiere revisión humana."""
            
            logger.info(f"🤖 ACA_QA procesando pregunta para {empresa_nombre}: '{pregunta[:50]}...'")
            
            # Llamar a OpenAI
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            respuesta = response.choices[0].message.content
            
            # Detectar si requiere ticket
            requiere_ticket = False
            motivo_ticket = None
            
            indicadores_ticket = [
                "revisión humana", "escalar", "ticket", 
                "no puedo realizar", "acción no permitida",
                "contactar al administrador"
            ]
            
            respuesta_lower = respuesta.lower()
            for indicador in indicadores_ticket:
                if indicador in respuesta_lower:
                    requiere_ticket = True
                    motivo_ticket = "Solicitud requiere revisión humana"
                    break
            
            logger.info(f"✅ ACA_QA respondió. Requiere ticket: {requiere_ticket}")
            
            return {
                "respuesta": respuesta,
                "requiere_ticket": requiere_ticket,
                "motivo_ticket": motivo_ticket
            }
            
        except Exception as e:
            logger.error(f"❌ Error en ACA_QA: {e}", exc_info=True)
            return {
                "respuesta": "Lo siento, hubo un error procesando tu consulta. Por favor, intenta de nuevo.",
                "requiere_ticket": False,
                "motivo_ticket": None
            }
    
    def _build_reportes_context(self, reportes_financieros: List[Dict], reportes_cfo: List[Dict]) -> str:
        """Construir texto de contexto a partir de los reportes"""
        contexto = ""
        
        if reportes_financieros:
            contexto += "\n=== REPORTES FINANCIEROS ===\n"
            for reporte in reportes_financieros:
                nombre = reporte.get('nombre_original') or reporte.get('nombre_archivo', 'Sin nombre')
                periodo = reporte.get('periodo', 'N/A')
                subtipo = reporte.get('subtipo', 'N/A')
                descripcion = reporte.get('descripcion_personalizada') or reporte.get('descripcion', '')
                metadata = reporte.get('metadata', {})
                
                contexto += f"\n- Reporte: {nombre}\n"
                contexto += f"  Periodo: {periodo}\n"
                contexto += f"  Tipo: {subtipo}\n"
                if descripcion:
                    contexto += f"  Descripción: {descripcion}\n"
                if metadata:
                    contexto += f"  Metadata: {json.dumps(metadata, ensure_ascii=False)}\n"
        
        if reportes_cfo:
            contexto += "\n=== REPORTES CFO ===\n"
            for reporte in reportes_cfo:
                nombre = reporte.get('nombre_original') or reporte.get('nombre_archivo', 'Sin nombre')
                periodo = reporte.get('periodo', 'N/A')
                descripcion = reporte.get('descripcion_personalizada') or reporte.get('descripcion', '')
                metadata = reporte.get('metadata', {})
                
                contexto += f"\n- Reporte CFO: {nombre}\n"
                if periodo:
                    contexto += f"  Periodo: {periodo}\n"
                if descripcion:
                    contexto += f"  Descripción: {descripcion}\n"
                if metadata:
                    contexto += f"  Metadata: {json.dumps(metadata, ensure_ascii=False)}\n"
        
        if not contexto:
            contexto = "No hay reportes disponibles."
        
        return contexto

# Instancia global
_ai_service = None

def get_ai_service() -> AIService:
    """Obtener instancia del servicio de IA"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


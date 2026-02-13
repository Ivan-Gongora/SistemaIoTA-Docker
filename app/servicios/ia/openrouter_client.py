import logging
import asyncio
from datetime import datetime, timedelta
from openai import AsyncOpenAI
from app.configuracion import config_energetico

logger = logging.getLogger(__name__)

class OpenRouterClient:
    def __init__(self):
        # 🎯 CONFIGURACIÓN PARA OPENROTER VÍA OPENAI
        self.client = AsyncOpenAI(
            api_key=config_energetico.IA_API_KEY,
            base_url="https://openrouter.ai/api/v1"  # ← URL específica de OpenRouter
        )
        
        self.modelo_actual = config_energetico.IA_MODELO_DEFAULT
        self.max_tokens = config_energetico.IA_MAX_TOKENS
        self.timeout = config_energetico.IA_TIMEOUT
        self.temperature = 0.3
        
        # 🛡️ Rate limiting
        self.last_request_time = None
        self.min_request_interval = 1.5
        
        # 💾 Cache
        self._cache = {}
        self._cache_ttl = 300
        
        if not config_energetico.IA_API_KEY:
            raise ValueError("❌ OpenRouter API Key no configurada")
        
        logger.info(f"🤖 Cliente OpenRouter inicializado - Modelo: {self.modelo_actual}")
    
    async def _wait_rate_limit(self):
        """Esperar entre requests para evitar rate limiting"""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.min_request_interval:
                wait_time = self.min_request_interval - elapsed
                await asyncio.sleep(wait_time)
        self.last_request_time = datetime.now()
    
    def _get_cache_key(self, prompt: str, contexto: str) -> str:
        """Generar clave única para cache"""
        return f"{hash(prompt)}:{hash(contexto)}"
    
    def _get_cached_response(self, cache_key: str) -> str:
        """Obtener respuesta del cache si existe y es válida"""
        if cache_key in self._cache:
            timestamp, response = self._cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self._cache_ttl):
                logger.info("💾 Respuesta obtenida de cache")
                return response
            else:
                del self._cache[cache_key]
        return None
    
    def _set_cached_response(self, cache_key: str, response: str):
        """Guardar respuesta en cache"""
        if len(self._cache) >= 10:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]
        self._cache[cache_key] = (datetime.now(), response)
    
    async def consultar_ia(self, prompt: str, contexto: str = "", modelo: str = None) -> str:
        """Consultar OpenRouter usando la librería OpenAI oficial"""
        
        modelo_usar = modelo or self.modelo_actual
        
        # Optimizar contexto y prompt
        contexto_optimizado = self._optimizar_contexto(contexto)
        prompt_optimizado = self._optimizar_prompt(prompt)
        
        cache_key = self._get_cache_key(prompt_optimizado, contexto_optimizado)
        cached_response = self._get_cached_response(cache_key)
        
        if cached_response:
            return cached_response
        
        try:
            # 🛡️ Rate limiting
            await self._wait_rate_limit()
            
            # 🎯 SYSTEM MESSAGE optimizada
            system_message = """Eres un experto en eficiencia energética industrial 
            y análisis de datos de consumo eléctrico en México. Especialista en 
            tarifas CFE GDMTH. Proporciona análisis precisos y recomendaciones prácticas."""
            
            # 📝 Preparar mensajes para la API
            messages = [
                {"role": "system", "content": system_message}
            ]
            
            # Añadir contexto si existe
            if contexto_optimizado:
                messages.append({"role": "user", "content": f"CONTEXTO:\n{contexto_optimizado}"})
            
            # Añadir prompt principal
            messages.append({"role": "user", "content": f"PREGUNTA/ANÁLISIS:\n{prompt_optimizado}"})
            
            logger.info(f"🔍 Consultando OpenRouter - Modelo: {modelo_usar}")
            
            # 🚀 LLAMADA A LA API CON LIBRERÍA OPENAI
            response = await self.client.chat.completions.create(
                model=modelo_usar,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout
            )
            
            # 📊 Procesar respuesta
            respuesta = response.choices[0].message.content
            
            # 💾 Guardar en cache
            self._set_cached_response(cache_key, respuesta)
            
            # 📈 Log de uso
            tokens_usados = response.usage.total_tokens if response.usage else 0
            logger.info(f"✅ OpenRouter ({modelo_usar}): {tokens_usados} tokens usados")
            
            return respuesta
            
        except Exception as e:
            logger.error(f"❌ Error en OpenRouter ({modelo_usar}): {str(e)}")
            
            # 🔄 Intentar fallback con otro modelo si es error de modelo específico
            # Evitar recursión infinita: solo hacer fallback si NO estamos ya en un fallback
            if (modelo is None) and ("model" in str(e).lower() or "not found" in str(e).lower() or "404" in str(e)):
                return await self._fallback_modelo(prompt_optimizado, contexto_optimizado, modelo_usar)
            
            return f"❌ Error en consulta IA: {str(e)}"
    
    async def _fallback_modelo(self, prompt: str, contexto: str, modelo_fallido: str) -> str:
        """Fallback a otros modelos gratuitos si uno falla"""
        
        logger.warning(f"🔄 Modelo '{modelo_fallido}' falló. Iniciando fallback...")
        modelos_fallback = [
            "meta-llama/llama-3.3-8b-instruct:free", # Reemplazo de llama-3.1
            "google/gemma-3-4b-it:free",           # Reemplazo de gemini-flash-1.5
            "mistralai/mistral-7b-instruct:free",  # Sigue siendo válido
            "z-ai/glm-4.5-air:free"                # Opción robusta adicional
        ]
        
        # Remover el modelo que falló (si estuviera en la lista, aunque no debería)
        modelos_fallback = [m for m in modelos_fallback if m != modelo_fallido]
        
        for modelo in modelos_fallback:
            try:
                # IMPORTANTE: Aquí llamamos a consultar_ia CON el modelo de fallback
                # para evitar que vuelva a entrar en esta función de fallback
                respuesta = await self.consultar_ia(prompt, contexto, modelo)
                
                if respuesta and not respuesta.startswith("❌"):
                    logger.info(f"✅ Fallback exitoso con modelo: {modelo}")
                    return respuesta
                else:
                    logger.warning(f"⚠️ Fallback con {modelo} también falló (respuesta inválida)")

            except Exception as e:
                logger.warning(f"⚠️ Fallback {modelo} también falló con error: {e}")
                continue
        
        logger.error("❌ Todos los modelos de fallback fallaron.")
        return "❌ Todos los modelos (principal y de respaldo) están temporalmente no disponibles."
    
    def _optimizar_contexto(self, contexto: str) -> str:
        """Optimizar contexto para reducir tokens"""
        if not contexto:
            return ""
        
        lines = contexto.strip().split('\n')
        lines_optimizadas = []
        
        for line in lines:
            line = ' '.join(line.split())
            if len(line) > 120:
                line = line[:117] + "..."
            if line and not line.isspace():
                lines_optimizadas.append(line)
        
        return '\n'.join(lines_optimizadas[:12])
    
    def _optimizar_prompt(self, prompt: str) -> str:
        """Optimizar prompt"""
        prompt = ' '.join(prompt.split())
        
        prompts_optimizados = {
            "analisis general": "Analiza patrones principales y da 3 recomendaciones clave con ahorro estimado para tarifa GDMTH México",
            "optimizacion costos": "Estrategias para reducir costos manteniendo operaciones en industria mexicana",
            "demanda maxima": "Cómo optimizar demanda máxima y reducir penalizaciones CFE en tarifa GDMTH",
            "factor potencia": "Recomendaciones para mejorar factor de potencia >90% en industria con tarifa GDMTH"
        }
        
        prompt_lower = prompt.lower()
        for key, optimized in prompts_optimizados.items():
            if key in prompt_lower:
                return optimized
        
        if len(prompt) > 180:
            return prompt[:177] + "..."
        
        return prompt
    
    async def analizar_datos_energeticos(self, df_summary: str, pregunta_especifica: str = "") -> str:
        """Método especializado para análisis energético"""
        
        # --- AQUÍ ESTABA EL ERROR ---
        # Antes: contexto = f"Datos energéticos México GDMTH:\n{self._optimizar_contexo(df_summary)}"
        # Ahora:
        contexto = f"Datos energéticos México GDMTH:\n{self._optimizar_contexto(df_summary)}"
        
        if pregunta_especifica:
            prompt = self._optimizar_prompt(pregunta_especifica)
        else:
            prompt = "Analiza patrones principales y da 3 recomendaciones clave con ahorro estimado para tarifa GDMTH México"
        
        # Usará el modelo principal (o fallback si falla)
        return await self.consultar_ia(prompt, contexto)
    
    def obtener_modelos_disponibles(self) -> list:
        """Obtener lista de modelos gratuitos disponibles"""
        # Esta función parece venir de tu config, asegúrate que esté actualizada
        return config_energetico.obtener_modelos_disponibles()
    
    async def probar_conexion(self) -> bool:
        """Probar conexión con OpenRouter"""
        try:
            respuesta = await self.consultar_ia("Responde solo con 'OK' si estás funcionando.", "")
            return "OK" in respuesta.upper()
        except Exception as e:
            logger.error(f"❌ Prueba de conexión falló: {e}")
            return False
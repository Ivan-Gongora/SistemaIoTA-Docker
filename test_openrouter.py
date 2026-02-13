#!/usr/bin/env python3
"""
Script para probar OpenRouter con librería OpenAI
y listar modelos gratuitos disponibles.
"""
import asyncio
import os
from dotenv import load_dotenv
import openai  # <-- 1. IMPORTACIÓN AÑADIDA

load_dotenv()

# --- 2. FUNCIÓN NUEVA AÑADIDA ---
async def listar_modelos_gratuitos():
    """
    Se conecta a OpenRouter para listar todos los modelos 'free'.
    """
    print("--- Listando Modelos Gratuitos de OpenRouter ---")
    
    # Asegúrate de que tu API key esté en .env como OPENROUTER_API_KEY
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        print("❌ Error: No se encontró la variable de entorno 'OPENROUTER_API_KEY' en tu .env")
        print("   Asegúrate de tenerla configurada para listar modelos.")
        return

    try:
        # Configuramos un cliente de OpenAI para apuntar a OpenRouter
        client = openai.AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        # Obtenemos la lista de modelos
        model_list = await client.models.list()
        
        free_models = []
        for model in model_list.data:
            # El estándar de OpenRouter es que los modelos gratis terminan en :free
            if ":free" in model.id:
                free_models.append(model.id)
        
        if free_models:
            print(f"✅ {len(free_models)} Modelos Gratuitos Encontrados:")
            # Ordenamos alfabéticamente para mejor lectura
            for model_id in sorted(free_models):
                print(f"   - {model_id}")
        else:
            print("⚠️ No se encontraron modelos gratuitos.")
            print("   Recuerda activar 'Model Training' en tu configuración de OpenRouter.")
            print("   https://openrouter.ai/account/settings")

    except openai.AuthenticationError:
        print("❌ Error de Autenticación: Tu OPENROUTER_API_KEY es incorrecta o no tiene permisos.")
    except Exception as e:
        print(f"❌ Error inesperado al listar modelos: {e}")
    
    print("--------------------------------------------------")


# --- Tu función original (sin cambios) ---
async def test_openrouter():
    """Probar conexión con OpenRouter"""
    from app.servicios.ia.openrouter_client import OpenRouterClient
    
    try:
        cliente = OpenRouterClient()
        print("\n🔍 Probando conexión con OpenRouter (usando OpenRouterClient)...")
        
        # Probar conexión simple
        # (Asumo que tu cliente.probar_conexion() usa el modelo configurado)
        conexion_ok = await cliente.probar_conexion()
        
        if conexion_ok:
            print("✅ Conexión con OpenRouterClient EXITOSA")
            
            # Probar análisis real
            print("🔍 Probando análisis energético...")
            datos_prueba = "Consumo: 38,900 kWh/mes, Costo: $111,012 MXN/mes, Tarifa: GDMTH"
            respuesta = await cliente.analizar_datos_energeticos(datos_prueba)
            
            print(f"✅ Análisis recibido: {len(respuesta)} caracteres")
            print(f"📋 Preview: {respuesta[:200]}...")
            
        else:
            print("❌ Conexión con OpenRouterClient FALLÓ (Revisa el modelo en tu config)")
            
    except Exception as e:
        print(f"❌ Error en OpenRouterClient: {e}")

# --- 3. BLOQUE MAIN MODIFICADO ---
async def main():
    """Función principal para correr ambas tareas"""
    await listar_modelos_gratuitos()
    await test_openrouter()

if __name__ == "__main__":
    # Ahora llamamos a la función main que ejecuta ambas
    asyncio.run(main())
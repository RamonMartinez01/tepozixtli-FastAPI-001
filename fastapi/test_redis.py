# fastapi/test_redis.py
import redis
import os
from dotenv import load_dotenv

# Cargamos el .env que está en la raíz o en fastapi/ (ajusta la ruta si es necesario)
load_dotenv(dotenv_path="../.env") 

def test_broker_connection():
    print("🚀 Iniciando prueba de conexión con Redis Broker...")
    
    try:
        # 1. Crear el cliente
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True # Fundamental para que devuelva Strings y no Bytes
        )

        # 2. Hacer Ping
        if r.ping():
            print("✅ [EXITO] ¡Apretón de manos con Redis logrado! El broker está vivo.")

        # 3. Prueba de Escritura/Lectura (Encolar y Desencolar)
        test_key = "test:fastapi_to_go"
        test_message = '{"task": "fetch_lst", "municipio_id": "1234-abcd"}'
        
        r.set(test_key, test_message)
        print(f"📝 Se escribió el mensaje en la llave: '{test_key}'")

        # 4. Leer el mensaje
        recovered_message = r.get(test_key)
        print(f"📥 Mensaje recuperado desde el broker: {recovered_message}")
        
        # 5. Limpieza
        r.delete(test_key)
        print("🧹 Limpieza de la llave de prueba realizada.")

    except redis.exceptions.AuthenticationError:
        print("❌ [ERROR] Falló la autenticación. Revisa el REDIS_PASSWORD.")
    except redis.exceptions.ConnectionError:
        print("❌ [ERROR] No se pudo conectar. ¿Seguro que el contenedor de Docker está corriendo?")
    except Exception as e:
        print(f"❌ [ERROR INESPERADO]: {e}")

if __name__ == "__main__":
    test_broker_connection()
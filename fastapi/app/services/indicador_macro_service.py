# fastapi/app/services/indicador_macro_service.py
import redis
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import List, Optional
from uuid import UUID
from app.core.config import settings

from app.models.indicador_macro import IndicadorMacro
from app.schemas.indicador_macro import RedisTaskPayload

# 1. Conexión al Broker
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=int(settings.REDIS_PORT),
    password=settings.REDIS_PASSWORD,
    username="default",
    decode_responses=True,
    retry_on_timeout=True
)

# Convertimos la función en asíncrona (async def) y usamos AsyncSession
async def obtener_o_encolar_indicador(
    db: AsyncSession, 
    tipo_indicador: str, 
    entidad_tipo: str, 
    entidad_id: UUID, 
    fecha_captura: date
) -> dict:
    
    # 2. Buscar en la Base de Datos (Estilo SQLAlchemy 2.0 Asíncrono)
    query = select(IndicadorMacro).where(
        IndicadorMacro.tipo_indicador == tipo_indicador,
        IndicadorMacro.entidad_tipo == entidad_tipo,
        IndicadorMacro.entidad_id == entidad_id,
        IndicadorMacro.fecha_captura == fecha_captura
    )
    result = await db.execute(query)
    registro_existente = result.scalars().first()

    if registro_existente:
        return {
            "status": "success", 
            "source": "database", 
            "data": registro_existente
        }

    # 3. Miss en caché: Armamos el mensaje
    payload = RedisTaskPayload(
        task="fetch_copernicus_data",
        tipo_indicador=tipo_indicador,
        entidad_tipo=entidad_tipo,
        entidad_id=str(entidad_id),
        fecha_captura=fecha_captura.isoformat()
    )

    # 4. Encolar en Redis
    queue_name = "queue:copernicus_tasks"
    redis_client.rpush(queue_name, payload.model_dump_json())

    return {
        "status": "processing", 
        "source": "redis_queue", 
        "message": "Datos no encontrados en caché. Tarea de extracción encolada para el Worker."
    }

# --- Historial para el Frontend (Asíncrona y SQLAlchemy 2.0) ---
async def obtener_ultimos_registros(
    db: AsyncSession, 
    entidad_id: UUID, 
    tipo_indicador: str, 
    limite: int = 5
) -> List[IndicadorMacro]:
    """
    Recupera el historial de los últimos N mapas ordenados descendentemente por fecha.
    """
    query = select(IndicadorMacro).where(
        IndicadorMacro.entidad_id == entidad_id,
        IndicadorMacro.tipo_indicador == tipo_indicador
    ).order_by(desc(IndicadorMacro.fecha_captura)).limit(limite)
    
    result = await db.execute(query)
    # .all() devuelve una lista de los objetos
    return result.scalars().all()
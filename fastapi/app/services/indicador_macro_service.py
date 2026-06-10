# fastapi/app/services/indicador_macro_service.py
import redis
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID
from app.core.config import settings

from app.models.indicador_macro import IndicadorMacro
from app.schemas.indicador_macro import RedisTaskPayload, CosechaMasivaRequest

# 1. Conexión al Broker
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=int(settings.REDIS_PORT),
    password=settings.REDIS_PASSWORD,
    username="default",
    decode_responses=True,
    retry_on_timeout=True
)

# --- Función Para el cliente: Solo Lectura (Read-Only) ---
async def obtener_indicador_por_fecha(
    db: AsyncSession, 
    tipo_indicador: str, 
    entidad_tipo: str, 
    entidad_id: UUID, 
    fecha_captura: date
) -> Optional[IndicadorMacro]:
    """
    Busca un mapa específico en la base de datos.
    Ya NO interactúa con Redis ni Copernicus para evitar abusos desde el frontend.
    """
    query = select(IndicadorMacro).where(
        IndicadorMacro.tipo_indicador == tipo_indicador,
        IndicadorMacro.entidad_tipo == entidad_tipo,
        IndicadorMacro.entidad_id == entidad_id,
        IndicadorMacro.fecha_captura == fecha_captura
    )
    result = await db.execute(query)
    
    # Devuelve el registro si existe, o None si no hay datos
    return result.scalars().first()

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

async def encolar_cosecha_masiva(
    db: AsyncSession,
    solicitud: CosechaMasivaRequest
) -> dict:
    """
    Desglosa un rango de fechas y lanza una ráfaga de tareas a Redis 
    solo para los mapas que aún no existen en la base de datos.
    """
    # Calcular el número total de días a procesar
    delta = solicitud.fecha_fin - solicitud.fecha_inicio
    dias_totales = delta.days + 1
    
    if dias_totales <= 0:
        return {"status": "error", "message": "La fecha de fin debe ser mayor o igual a la de inicio."}
    
    # Freno de seguridad para no saturar la API de Copernicus en un solo click
    if dias_totales > 365: 
        return {"status": "error", "message": "El rango no puede exceder 1 año (365 días) por petición."}

    tareas_encoladas = 0
    registros_existentes = 0

    for i in range(dias_totales):
        fecha_actual = solicitud.fecha_inicio + timedelta(days=i)
        
        # 1. Verificar si el mapa ya existe en nuestra bóveda
        query = select(IndicadorMacro).where(
            IndicadorMacro.tipo_indicador == solicitud.tipo_indicador,
            IndicadorMacro.entidad_tipo == solicitud.entidad_tipo,
            IndicadorMacro.entidad_id == solicitud.entidad_id,
            IndicadorMacro.fecha_captura == fecha_actual
        )
        result = await db.execute(query)
        
        if result.scalars().first():
            registros_existentes += 1
            continue  # Saltamos al siguiente día, este ya lo tenemos

        # 2. Si no existe, armamos el misil para la cola de Redis
        payload = RedisTaskPayload(
            task="fetch_copernicus_data",
            tipo_indicador=solicitud.tipo_indicador,
            entidad_tipo=solicitud.entidad_tipo,
            entidad_id=str(solicitud.entidad_id),
            fecha_captura=fecha_actual.isoformat()
        )
        
        queue_name = "queue:copernicus_tasks"
        redis_client.rpush(queue_name, payload.model_dump_json())
        tareas_encoladas += 1

    return {
        "status": "success",
        "resumen": {
            "rango_solicitado": f"{solicitud.fecha_inicio} a {solicitud.fecha_fin}",
            "dias_totales": dias_totales,
            "tareas_enviadas_al_worker": tareas_encoladas,
            "mapas_ya_existentes": registros_existentes
        }
    }

async def auditar_indicadores(
    db: AsyncSession,
    entidad_tipo: Optional[str] = None,
    entidad_id: Optional[UUID] = None,
    tipo_indicador: Optional[str] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None
) -> List[IndicadorMacro]:
    """
    Construye una consulta dinámica para auditar la tabla de indicadores.
    Solo aplica los filtros que reciben un valor.
    """
    # 1. Iniciamos la consulta base
    query = select(IndicadorMacro)
    
    # 2. Ensamblaje dinámico de filtros
    if entidad_tipo:
        query = query.where(IndicadorMacro.entidad_tipo == entidad_tipo)
    
    if entidad_id:
        query = query.where(IndicadorMacro.entidad_id == entidad_id)
        
    if tipo_indicador:
        query = query.where(IndicadorMacro.tipo_indicador == tipo_indicador)
        
    if fecha_inicio:
        query = query.where(IndicadorMacro.fecha_captura >= fecha_inicio)
        
    if fecha_fin:
        query = query.where(IndicadorMacro.fecha_captura <= fecha_fin)
        
    # 3. Ordenamos siempre del más reciente al más antiguo
    query = query.order_by(desc(IndicadorMacro.fecha_captura))
    
    # 4. Ejecutamos el disparo a la base de datos
    result = await db.execute(query)
    
    return result.scalars().all()


# --- Función para Gráficos: Serie de Tiempo Estricta ---
async def obtener_serie_tiempo(
    db: AsyncSession, 
    entidad_tipo: str,
    entidad_id: UUID, 
    tipo_indicador: str, 
    fecha_inicio: date,
    fecha_fin: date
) -> List[IndicadorMacro]:
    """
    Recupera una serie de datos en un rango exacto.
    Ordenado cronológicamente (ascendente) para alimentar gráficos en el frontend.
    """
    query = select(IndicadorMacro).where(
        IndicadorMacro.entidad_tipo == entidad_tipo,
        IndicadorMacro.entidad_id == entidad_id,
        IndicadorMacro.tipo_indicador == tipo_indicador,
        IndicadorMacro.fecha_captura >= fecha_inicio,
        IndicadorMacro.fecha_captura <= fecha_fin
    ).order_by(IndicadorMacro.fecha_captura) # Ascendente por defecto
    
    result = await db.execute(query)
    return result.scalars().all()
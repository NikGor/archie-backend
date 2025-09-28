import json
import os
from datetime import datetime
from typing import Dict, Optional, Any
import redis
from pydantic import BaseModel


class UserState(BaseModel):
    """Модель состояния пользователя для хранения в Redis"""
    user_id: str
    user_name: Optional[str] = None
    default_city: Optional[str] = None
    persona: Optional[str] = None
    current_date: Optional[str] = None
    current_time: Optional[str] = None
    current_weekday: Optional[str] = None


class RedisClient:
    """Клиент для работы с Redis кэшем состояний пользователей"""
    
    def __init__(self):
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "8004"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
    
    def _get_user_key(self, user_id: str) -> str:
        """Генерирует ключ для хранения состояния пользователя"""
        return f"user_state:{user_id}"
    
    def get_user_state(self, user_id: str) -> Optional[UserState]:
        """Получает состояние пользователя из Redis"""
        try:
            key = self._get_user_key(user_id)
            data = self.redis_client.get(key)
            
            if data:
                state_dict = json.loads(data)
                return UserState(**state_dict)
            return None
            
        except Exception as e:
            print(f"Ошибка при получении состояния пользователя {user_id}: {e}")
            return None
    
    def set_user_state(
        self, 
        user_id: str, 
        state: UserState, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Сохраняет состояние пользователя в Redis
        
        Args:
            user_id: ID пользователя
            state: Состояние пользователя
            ttl: Время жизни записи в секундах (по умолчанию без ограничений)
        """
        try:
            key = self._get_user_key(user_id)
            data = state.model_dump_json()
            
            if ttl:
                self.redis_client.setex(key, ttl, data)
            else:
                self.redis_client.set(key, data)
            
            return True
            
        except Exception as e:
            print(f"Ошибка при сохранении состояния пользователя {user_id}: {e}")
            return False
    
    def update_user_state(
        self, 
        user_id: str, 
        updates: Dict[str, Any], 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Обновляет частично состояние пользователя
        
        Args:
            user_id: ID пользователя
            updates: Словарь с обновлениями
            ttl: Время жизни записи в секундах
        """
        try:
            current_state = self.get_user_state(user_id)
            
            if current_state is None:
                # Создаем новое состояние если его нет
                current_state = UserState(user_id=user_id)
            
            # Обновляем поля
            state_dict = current_state.model_dump()
            state_dict.update(updates)
            
            updated_state = UserState(**state_dict)
            return self.set_user_state(user_id, updated_state, ttl)
            
        except Exception as e:
            print(f"Ошибка при обновлении состояния пользователя {user_id}: {e}")
            return False
    
    def delete_user_state(self, user_id: str) -> bool:
        """Удаляет состояние пользователя из Redis"""
        try:
            key = self._get_user_key(user_id)
            result = self.redis_client.delete(key)
            return result > 0
            
        except Exception as e:
            print(f"Ошибка при удалении состояния пользователя {user_id}: {e}")
            return False
    
    def get_user_field(self, user_id: str, field: str) -> Optional[Any]:
        """Получает конкретное поле из состояния пользователя"""
        state = self.get_user_state(user_id)
        if state:
            return getattr(state, field, None)
        return None
    
    def set_user_field(
        self, 
        user_id: str, 
        field: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Устанавливает конкретное поле в состоянии пользователя"""
        return self.update_user_state(user_id, {field: value}, ttl)
    
    def update_current_datetime(self, user_id: str) -> bool:
        """Обновляет текущие дату и время для пользователя"""
        now = datetime.now()
        updates = {
            "current_date": now.strftime("%Y-%m-%d"),
            "current_time": now.strftime("%H:%M:%S"),
            "current_weekday": now.strftime("%A")
        }
        return self.update_user_state(user_id, updates)
    
    def ping(self) -> bool:
        """Проверяет соединение с Redis"""
        try:
            return self.redis_client.ping()
        except Exception as e:
            print(f"Ошибка подключения к Redis: {e}")
            return False


# Глобальный экземпляр клиента
redis_client = RedisClient()

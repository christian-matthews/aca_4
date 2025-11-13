import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Configuration
    BOT_ADMIN_TOKEN = os.getenv("BOT_ADMIN_TOKEN")
    BOT_PRODUCTION_TOKEN = os.getenv("BOT_PRODUCTION_TOKEN")
    ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    # OpenAI Configuration (opcional)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Storage Configuration (FASE 2)
    SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "archivos-bot")
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    
    # App Configuration
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    
    @classmethod
    def validate(cls):
        """Validar que todas las variables requeridas estén configuradas"""
        required_vars = [
            "BOT_ADMIN_TOKEN",
            "BOT_PRODUCTION_TOKEN", 
            "ADMIN_CHAT_ID",
            "SUPABASE_URL",
            "SUPABASE_KEY",
            "SUPABASE_SERVICE_KEY"  # Crítico para logging
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Variables de entorno faltantes: {', '.join(missing_vars)}")
        
        return True



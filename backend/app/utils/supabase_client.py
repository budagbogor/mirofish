import os
from supabase import create_client, Client
from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.supabase')

_supabase: Client = None

def get_supabase() -> Client:
    """获取 Supabase 客户端实例 (Singleton)"""
    global _supabase
    if _supabase is None:
        url = Config.SUPABASE_URL
        key = Config.SUPABASE_KEY
        
        if not url or not key:
            logger.error("SUPABASE_URL atau SUPABASE_KEY belum dikonfigurasi di .env")
            raise ValueError("Konfigurasi Supabase tidak lengkap. Silakan periksa file .env Anda.")
            
        try:
            _supabase = create_client(url, key)
            logger.info(f"Berhasil terhubung ke Supabase: {url}")
        except Exception as e:
            logger.error(f"Gagal menghubungkan ke Supabase: {str(e)}")
            raise
            
    return _supabase

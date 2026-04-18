"""
动作日志记录器 (Supabase 适配版)
用于记录OASIS模拟中每个Agent the actions，支持本地 .jsonl 和 Supabase 实时同步
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from supabase import create_client, Client


class PlatformActionLogger:
    """单平台动作日志记录器 (支持 Supabase)"""
    
    def __init__(self, platform: str, base_dir: str, simulation_id: str = None):
        """
        初始化日志记录器
        """
        self.platform = platform
        self.base_dir = base_dir
        self.simulation_id = simulation_id
        self.log_dir = os.path.join(base_dir, platform)
        self.log_path = os.path.join(self.log_dir, "actions.jsonl")
        self._ensure_dir()
        
        # 初始化 Supabase
        self.supabase: Optional[Client] = None
        self._init_supabase()
    
    def _init_supabase(self):
        """尝试初始化 Supabase 客户端"""
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY')
        if url and key:
            try:
                self.supabase = create_client(url, key)
            except Exception:
                pass

    def _ensure_dir(self):
        """确保目录存在"""
        os.makedirs(self.log_dir, exist_ok=True)
    
    def log_action(
        self,
        round_num: int,
        agent_id: int,
        agent_name: str,
        action_type: str,
        action_args: Optional[Dict[str, Any]] = None,
        result: Optional[str] = None,
        success: bool = True
    ):
        """记录一个动作 (Sync to Supabase)"""
        timestamp = datetime.now().isoformat()
        entry = {
            "round": round_num,
            "timestamp": timestamp,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "action_type": action_type,
            "action_args": action_args or {},
            "result": result,
            "success": success,
        }
        
        # 本地备份
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception:
            pass

        # 同步到 Supabase
        if self.supabase and self.simulation_id:
            try:
                db_entry = {
                    "simulation_id": self.simulation_id,
                    "round_num": round_num,
                    "timestamp": timestamp,
                    "platform": self.platform,
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "action_type": action_type,
                    "action_args": action_args or {},
                    "result": str(result) if result else None,
                    "success": success
                }
                self.supabase.table('agent_actions').insert(db_entry).execute()
            except Exception:
                pass
    
    def log_round_start(self, round_num: int, simulated_hour: int):
        """记录轮次开始"""
        entry = {
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "event_type": "round_start",
            "simulated_hour": simulated_hour,
        }
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception: pass
    
    def log_round_end(self, round_num: int, actions_count: int):
        """记录轮次结束"""
        entry = {
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "event_type": "round_end",
            "actions_count": actions_count,
        }
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception: pass
    
    def log_simulation_start(self, config: Dict[str, Any]):
        """记录模拟开始"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "simulation_start",
            "platform": self.platform,
            "total_rounds": config.get("time_config", {}).get("total_simulation_hours", 72) * 2,
            "agents_count": len(config.get("agent_configs", [])),
        }
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception: pass
    
    def log_simulation_end(self, total_rounds: int, total_actions: int):
        """记录模拟结束"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "simulation_end",
            "platform": self.platform,
            "total_rounds": total_rounds,
            "total_actions": total_actions,
        }
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception: pass


class SimulationLogManager:
    """
    模拟日志管理器 (适配 Supabase)
    """
    
    def __init__(self, simulation_dir: str, simulation_id: str = None):
        self.simulation_dir = simulation_dir
        self.simulation_id = simulation_id or os.path.basename(simulation_dir)
        self.twitter_logger: Optional[PlatformActionLogger] = None
        self.reddit_logger: Optional[PlatformActionLogger] = None
        self._main_logger: Optional[logging.Logger] = None
        self._setup_main_logger()
    
    def _setup_main_logger(self):
        """设置主模拟日志"""
        log_path = os.path.join(self.simulation_dir, "simulation.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        self._main_logger = logging.getLogger(f"simulation.{self.simulation_id}")
        self._main_logger.setLevel(logging.INFO)
        self._main_logger.handlers.clear()
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8', mode='w')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self._main_logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
        self._main_logger.addHandler(console_handler)
        self._main_logger.propagate = False
    
    def get_twitter_logger(self) -> PlatformActionLogger:
        if self.twitter_logger is None:
            self.twitter_logger = PlatformActionLogger("twitter", self.simulation_dir, self.simulation_id)
        return self.twitter_logger
    
    def get_reddit_logger(self) -> PlatformActionLogger:
        if self.reddit_logger is None:
            self.reddit_logger = PlatformActionLogger("reddit", self.simulation_dir, self.simulation_id)
        return self.reddit_logger
    
    def log(self, message: str, level: str = "info"):
        if self._main_logger:
            getattr(self._main_logger, level.lower(), self._main_logger.info)(message)
    
    def info(self, message: str): self.log(message, "info")
    def warning(self, message: str): self.log(message, "warning")
    def error(self, message: str): self.log(message, "error")
    def debug(self, message: str): self.log(message, "debug")


# ============ 兼容旧接口 ============

class ActionLogger:
    def __init__(self, log_path: str):
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self.supabase: Optional[Client] = None
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY')
        if url and key:
            try:
                self.supabase = create_client(url, key)
            except:
                pass
    
    def log_action(self, round_num: int, platform: str, agent_id: int, agent_name: str, action_type: str, **kwargs):
        timestamp = datetime.now().isoformat()
        entry = {"round": round_num, "timestamp": timestamp, "platform": platform, "agent_id": agent_id, 
                 "agent_name": agent_name, "action_type": action_type, **kwargs}
        
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except: pass
            
        if self.supabase and os.environ.get('SIMULATION_ID'):
            try:
                self.supabase.table('agent_actions').insert({
                    "simulation_id": os.environ.get('SIMULATION_ID'),
                    "round_num": round_num,
                    "timestamp": timestamp,
                    "platform": platform,
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "action_type": action_type,
                    "action_args": kwargs.get("action_args", {}),
                    "result": str(kwargs.get("result", "")),
                    "success": kwargs.get("success", True)
                }).execute()
            except: pass
    
    def log_round_start(self, *args, **kwargs): pass
    def log_round_end(self, *args, **kwargs): pass
    def log_simulation_start(self, *args, **kwargs): pass
    def log_simulation_end(self, *args, **kwargs): pass


_global_logger: Optional[ActionLogger] = None

def get_logger(log_path: Optional[str] = None) -> ActionLogger:
    global _global_logger
    if log_path: _global_logger = ActionLogger(log_path)
    if _global_logger is None: _global_logger = ActionLogger("actions.jsonl")
    return _global_logger

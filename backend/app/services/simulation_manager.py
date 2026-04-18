import os
import json
import uuid
import shutil
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..config import Config
from ..utils.logger import get_logger
from .zep_entity_reader import ZepEntityReader, FilteredEntities
from .oasis_profile_generator import OasisProfileGenerator, OasisAgentProfile
from .simulation_config_generator import SimulationConfigGenerator, SimulationParameters
from ..utils.locale import t
from ..utils.supabase_client import get_supabase

logger = get_logger('mirofish.simulation')


class SimulationStatus(str, Enum):
    """模拟状态"""
    CREATED = "created"
    PREPARING = "preparing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"      # 模拟被手动停止
    COMPLETED = "completed"  # 模拟自然完成
    FAILED = "failed"


class PlatformType(str, Enum):
    """平台类型"""
    TWITTER = "twitter"
    REDDIT = "reddit"


@dataclass
class SimulationState:
    """模拟状态"""
    simulation_id: str
    project_id: str
    graph_id: str
    
    # 平台启用状态
    enable_twitter: bool = True
    enable_reddit: bool = True
    
    # 状态
    status: SimulationStatus = SimulationStatus.CREATED
    
    # 准备阶段数据
    entities_count: int = 0
    profiles_count: int = 0
    entity_types: List[str] = field(default_factory=list)
    
    # 配置生成信息
    config_generated: bool = False
    config_reasoning: str = ""
    
    # 运行时数据
    current_round: int = 0
    twitter_status: str = "not_started"
    reddit_status: str = "not_started"
    
    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 错误信息
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """完整状态字典 (Supabase 兼容)"""
        return {
            "simulation_id": self.simulation_id,
            "project_id": self.project_id,
            "graph_id": self.graph_id,
            "enable_twitter": self.enable_twitter,
            "enable_reddit": self.enable_reddit,
            "status": self.status.value,
            "entities_count": self.entities_count,
            "profiles_count": self.profiles_count,
            "entity_types": self.entity_types,
            "config_generated": self.config_generated,
            "config_reasoning": self.config_reasoning,
            "current_round": self.current_round,
            "twitter_status": self.twitter_status,
            "reddit_status": self.reddit_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationState':
        """从字典创建"""
        return cls(
            simulation_id=data['simulation_id'],
            project_id=data.get("project_id", ""),
            graph_id=data.get("graph_id", ""),
            enable_twitter=data.get("enable_twitter", True),
            enable_reddit=data.get("enable_reddit", True),
            status=SimulationStatus(data.get("status", "created")),
            entities_count=data.get("entities_count", 0),
            profiles_count=data.get("profiles_count", 0),
            entity_types=data.get("entity_types", []),
            config_generated=data.get("config_generated", False),
            config_reasoning=data.get("config_reasoning", ""),
            current_round=data.get("current_round", 0),
            twitter_status=data.get("twitter_status", "not_started"),
            reddit_status=data.get("reddit_status", "not_started"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            error=data.get("error"),
        )


class SimulationManager:
    """模拟管理器 - Supabase版"""
    
    TABLE_NAME = 'simulations'
    BUCKET_NAME = 'uploads'
    
    def __init__(self):
        # 内存缓存 (可选)
        self._simulations: Dict[str, SimulationState] = {}
    
    def _save_simulation_state(self, state: SimulationState):
        """保存状态到 Supabase"""
        state.updated_at = datetime.now().isoformat()
        supabase = get_supabase()
        
        try:
            supabase.table(self.TABLE_NAME)\
                .update(state.to_dict())\
                .eq('simulation_id', state.simulation_id)\
                .execute()
            self._simulations[state.simulation_id] = state
        except Exception as e:
            logger.error(f"Gagal simpan state simulasi: {str(e)}")
            raise
    
    def _load_simulation_state(self, simulation_id: str) -> Optional[SimulationState]:
        """从 Supabase 加载状态"""
        supabase = get_supabase()
        
        try:
            response = supabase.table(self.TABLE_NAME)\
                .select("*")\
                .eq('simulation_id', simulation_id)\
                .execute()
            
            if not response.data:
                return None
            
            state = SimulationState.from_dict(response.data[0])
            self._simulations[simulation_id] = state
            return state
        except Exception as e:
            logger.error(f"Gagal load state simulasi: {str(e)}")
            return None
    
    def create_simulation(
        self,
        project_id: str,
        graph_id: str,
        enable_twitter: bool = True,
        enable_reddit: bool = True,
    ) -> SimulationState:
        """创建新的模拟 (Supabase)"""
        simulation_id = f"sim_{uuid.uuid4().hex[:12]}"
        
        state = SimulationState(
            simulation_id=simulation_id,
            project_id=project_id,
            graph_id=graph_id,
            enable_twitter=enable_twitter,
            enable_reddit=enable_reddit,
            status=SimulationStatus.CREATED,
        )
        
        supabase = get_supabase()
        try:
            supabase.table(self.TABLE_NAME).insert(state.to_dict()).execute()
            logger.info(f"Simulasi ditambahkan ke Supabase: {simulation_id}")
            self._simulations[simulation_id] = state
        except Exception as e:
            logger.error(f"Gagal tambah simulasi ke Supabase: {str(e)}")
            raise
            
        return state
    
    def prepare_simulation(
        self,
        simulation_id: str,
        simulation_requirement: str,
        document_text: str,
        defined_entity_types: Optional[List[str]] = None,
        use_llm_for_profiles: bool = True,
        progress_callback: Optional[callable] = None,
        parallel_profile_count: int = 3
    ) -> SimulationState:
        """准备模拟环境 - 适配 Cloud Storage"""
        state = self._load_simulation_state(simulation_id)
        if not state:
            raise ValueError(f"模拟不存在: {simulation_id}")
        
        supabase = get_supabase()
        
        try:
            state.status = SimulationStatus.PREPARING
            self._save_simulation_state(state)
            
            # ========== 阶段1: 读取实体 ==========
            if progress_callback:
                progress_callback("reading", 0, t('progress.connectingZepGraph'))
            
            reader = ZepEntityReader()
            filtered = reader.filter_defined_entities(
                graph_id=state.graph_id,
                defined_entity_types=defined_entity_types,
                enrich_with_edges=True
            )
            
            state.entities_count = filtered.filtered_count
            state.entity_types = list(filtered.entity_types)
            
            if filtered.filtered_count == 0:
                state.status = SimulationStatus.FAILED
                state.error = "No entities found."
                self._save_simulation_state(state)
                return state
            
            # ========== 阶段2: 生成 Profile ==========
            total_entities = len(filtered.entities)
            generator = OasisProfileGenerator(graph_id=state.graph_id)
            
            profiles = generator.generate_profiles_from_entities(
                entities=filtered.entities,
                use_llm=use_llm_for_profiles,
                graph_id=state.graph_id,
                parallel_count=parallel_profile_count
            )
            
            state.profiles_count = len(profiles)
            
            # Upload Profiles to Storage
            if state.enable_reddit:
                profiles_json = generator.format_profiles(profiles, "reddit")
                supabase.storage.from_(self.BUCKET_NAME).upload(
                    path=f"simulations/{simulation_id}/reddit_profiles.json",
                    file=json.dumps(profiles_json, ensure_ascii=False, indent=2).encode('utf-8'),
                    file_options={"content-type": "application/json"}
                )
            
            if state.enable_twitter:
                profiles_csv = generator.format_profiles(profiles, "twitter")
                supabase.storage.from_(self.BUCKET_NAME).upload(
                    path=f"simulations/{simulation_id}/twitter_profiles.csv",
                    file=profiles_csv.encode('utf-8'),
                    file_options={"content-type": "text/csv"}
                )
                
            # ========== 阶段3: 生成 Config ==========
            config_generator = SimulationConfigGenerator()
            sim_params = config_generator.generate_config(
                simulation_id=simulation_id,
                project_id=state.project_id,
                graph_id=state.graph_id,
                simulation_requirement=simulation_requirement,
                document_text=document_text,
                entities=filtered.entities,
                enable_twitter=state.enable_twitter,
                enable_reddit=state.enable_reddit
            )
            
            # Simpan config ke database
            state.config_generated = True
            state.config_reasoning = sim_params.generation_reasoning
            
            # Juga upload config ke storage agar runner bisa akses
            supabase.storage.from_(self.BUCKET_NAME).upload(
                path=f"simulations/{simulation_id}/simulation_config.json",
                file=sim_params.to_json().encode('utf-8'),
                file_options={"content-type": "application/json"}
            )
            
            # 更新状态
            state.status = SimulationStatus.READY
            self._save_simulation_state(state)
            
            return state
            
        except Exception as e:
            logger.error(f"Gagal prepare simulasi: {str(e)}")
            state.status = SimulationStatus.FAILED
            state.error = str(e)
            self._save_simulation_state(state)
            raise
    
    def list_simulations(self, project_id: Optional[str] = None) -> List[SimulationState]:
        """列出所有模拟 (Supabase)"""
        supabase = get_supabase()
        
        try:
            query = supabase.table(self.TABLE_NAME).select("*")
            if project_id:
                query = query.eq('project_id', project_id)
            
            response = query.order('created_at', desc=True).execute()
            return [SimulationState.from_dict(d) for d in response.data]
        except Exception as e:
            logger.error(f"Gagal list simulasi: {str(e)}")
            return []

    def get_simulation(self, simulation_id: str) -> Optional[SimulationState]:
        return self._load_simulation_state(simulation_id)
    
    def get_profiles(self, simulation_id: str, platform: str = "reddit") -> List[Dict[str, Any]]:
        """从 Storage 获取 Profile"""
        supabase = get_supabase()
        try:
            path = f"simulations/{simulation_id}/{platform}_profiles.json"
            response = supabase.storage.from_(self.BUCKET_NAME).download(path)
            return json.loads(response.decode('utf-8'))
        except Exception:
            return []

    def get_simulation_config(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """从 Storage 获取 Config"""
        supabase = get_supabase()
        try:
            path = f"simulations/{simulation_id}/simulation_config.json"
            response = supabase.storage.from_(self.BUCKET_NAME).download(path)
            return json.loads(response.decode('utf-8'))
        except Exception:
            return None

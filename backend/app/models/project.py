import os
import json
import uuid
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field, asdict
from ..config import Config
from ..utils.supabase_client import get_supabase
from ..utils.logger import get_logger

logger = get_logger('mirofish.project_manager')


class ProjectStatus(str, Enum):
    """项目状态"""
    CREATED = "created"              # 刚创建，文件已上传
    ONTOLOGY_GENERATED = "ontology_generated"  # 本体已生成
    GRAPH_BUILDING = "graph_building"    # 图谱构建中
    GRAPH_COMPLETED = "graph_completed"  # 图谱构建完成
    FAILED = "failed"                # 失败


@dataclass
class Project:
    """项目数据模型"""
    project_id: str
    name: str
    status: ProjectStatus
    created_at: str
    updated_at: str
    
    # 文件信息
    files: List[Dict[str, str]] = field(default_factory=list)  # [{filename, original_filename, path, size, storage_path}]
    total_text_length: int = 0
    
    # 本体信息（接口1生成后填充）
    ontology: Optional[Dict[str, Any]] = None
    analysis_summary: Optional[str] = None
    
    # 图谱信息（接口2完成后填充）
    graph_id: Optional[str] = None
    graph_build_task_id: Optional[str] = None
    
    # 配置
    simulation_requirement: Optional[str] = None
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # 错误信息
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "project_id": self.project_id,
            "name": self.name,
            "status": self.status.value if isinstance(self.status, ProjectStatus) else self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "files": self.files,
            "total_text_length": self.total_text_length,
            "ontology": self.ontology,
            "analysis_summary": self.analysis_summary,
            "graph_id": self.graph_id,
            "graph_build_task_id": self.graph_build_task_id,
            "simulation_requirement": self.simulation_requirement,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """从字典创建"""
        status = data.get('status', 'created')
        if isinstance(status, str):
            try:
                status = ProjectStatus(status)
            except ValueError:
                status = ProjectStatus.CREATED
        
        return cls(
            project_id=data['project_id'],
            name=data.get('name', 'Unnamed Project'),
            status=status,
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            files=data.get('files', []),
            total_text_length=data.get('total_text_length', 0),
            ontology=data.get('ontology'),
            analysis_summary=data.get('analysis_summary'),
            graph_id=data.get('graph_id'),
            graph_build_task_id=data.get('graph_build_task_id'),
            simulation_requirement=data.get('simulation_requirement'),
            chunk_size=data.get('chunk_size', 500),
            chunk_overlap=data.get('chunk_overlap', 50),
            error=data.get('error')
        )


class ProjectManager:
    """项目管理器 - 负责项目的持久化存储和检索 (Supabase版)"""
    
    # Supabase 表名
    TABLE_NAME = 'projects'
    # Supabase Storage Bucket 名
    BUCKET_NAME = 'uploads'
    
    @classmethod
    def create_project(cls, name: str = "Unnamed Project") -> Project:
        """
        创建新项目 (Supabase)
        """
        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        
        project = Project(
            project_id=project_id,
            name=name,
            status=ProjectStatus.CREATED,
            created_at=now,
            updated_at=now
        )
        
        supabase = get_supabase()
        try:
            supabase.table(cls.TABLE_NAME).insert(project.to_dict()).execute()
            logger.info(f"Project ditambahkan ke Supabase: {project_id}")
        except Exception as e:
            logger.error(f"Gagal menambahkan project ke Supabase: {str(e)}")
            raise
            
        return project
    
    @classmethod
    def save_project(cls, project: Project) -> None:
        """保存项目元数据 (Supabase)"""
        project.updated_at = datetime.now().isoformat()
        supabase = get_supabase()
        
        try:
            supabase.table(cls.TABLE_NAME)\
                .update(project.to_dict())\
                .eq('project_id', project.project_id)\
                .execute()
            logger.info(f"Project updated di Supabase: {project.project_id}")
        except Exception as e:
            logger.error(f"Gagal update project di Supabase: {str(e)}")
            raise
    
    @classmethod
    def get_project(cls, project_id: str) -> Optional[Project]:
        """获取项目 (Supabase)"""
        supabase = get_supabase()
        
        try:
            response = supabase.table(cls.TABLE_NAME)\
                .select("*")\
                .eq('project_id', project_id)\
                .execute()
            
            if not response.data:
                return None
            
            return Project.from_dict(response.data[0])
        except Exception as e:
            logger.error(f"Gagal mengambil project dari Supabase: {str(e)}")
            return None
    
    @classmethod
    def list_projects(cls, limit: int = 50) -> List[Project]:
        """列出所有项目 (Supabase)"""
        supabase = get_supabase()
        
        try:
            response = supabase.table(cls.TABLE_NAME)\
                .select("*")\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return [Project.from_dict(d) for d in response.data]
        except Exception as e:
            logger.error(f"Gagal list projects dari Supabase: {str(e)}")
            return []
    
    @classmethod
    def delete_project(cls, project_id: str) -> bool:
        """删除项目 (Supabase)"""
        supabase = get_supabase()
        
        try:
            # Hapus metadata
            supabase.table(cls.TABLE_NAME).delete().eq('project_id', project_id).execute()
            
            # TODO: Hapus file di Storage jika diperlukan
            # supabase.storage.from_(cls.BUCKET_NAME).remove([...])
            
            logger.info(f"Project dihapus dari Supabase: {project_id}")
            return True
        except Exception as e:
            logger.error(f"Gagal hapus project di Supabase: {str(e)}")
            return False
    
    @classmethod
    def save_file_to_project(cls, project_id: str, file_storage, original_filename: str) -> Dict[str, str]:
        """
        保存上传的文件到 Supabase Storage
        """
        ext = os.path.splitext(original_filename)[1].lower()
        safe_filename = f"{uuid.uuid4().hex[:8]}{ext}"
        storage_path = f"projects/{project_id}/{safe_filename}"
        
        supabase = get_supabase()
        
        try:
            # Baca data file
            file_data = file_storage.read()
            # Upload ke Supabase Storage
            supabase.storage.from_(cls.BUCKET_NAME).upload(
                path=storage_path,
                file=file_data,
                file_options={"content-type": file_storage.content_type}
            )
            
            logger.info(f"File uploaded ke Supabase Storage: {storage_path}")
            
            return {
                "original_filename": original_filename,
                "saved_filename": safe_filename,
                "storage_path": storage_path,
                "size": len(file_data),
                "content_type": file_storage.content_type
            }
        except Exception as e:
            logger.error(f"Gagal upload file ke Supabase Storage: {str(e)}")
            raise
    
    @classmethod
    def save_extracted_text(cls, project_id: str, text: str) -> None:
        """保存提取的文本 (Supabase - Kolom analysis_summary atau storage)"""
        # Di sini kita simpan ke kolom analysis_summary untuk akses cepat
        # Atau bisa juga upload sebagai file .txt ke Storage
        project = cls.get_project(project_id)
        if project:
            project.analysis_summary = text  # Sementara gunakan ini
            cls.save_project(project)
    
    @classmethod
    def get_extracted_text(cls, project_id: str) -> Optional[str]:
        """获取提取的文本"""
        project = cls.get_project(project_id)
        return project.analysis_summary if project else None
    
    @classmethod
    def get_project_files(cls, project_id: str) -> List[Dict[str, Any]]:
        """获取项目的所有文件信息 (Supabase)"""
        project = cls.get_project(project_id)
        return project.files if project else []


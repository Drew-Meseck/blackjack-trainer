"""Session manager for saving and loading blackjack simulation sessions."""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from .session_data import SessionData, SessionMetadata


class SessionManagerError(Exception):
    """Base exception for session manager errors."""
    pass


class SessionNotFoundError(SessionManagerError):
    """Raised when a requested session cannot be found."""
    pass


class SessionCorruptedError(SessionManagerError):
    """Raised when session data is corrupted or invalid."""
    pass


class SessionManager:
    """Manages saving, loading, and organizing blackjack simulation sessions."""
    
    def __init__(self, sessions_dir: str = "sessions"):
        """Initialize session manager with specified directory.
        
        Args:
            sessions_dir: Directory to store session files
        """
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
        
        # Create metadata index file path
        self.metadata_file = self.sessions_dir / "sessions_index.json"
        
        # Load existing metadata index
        self._metadata_index: Dict[str, SessionMetadata] = self._load_metadata_index()
    
    def _load_metadata_index(self) -> Dict[str, SessionMetadata]:
        """Load the metadata index from disk."""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    session_id: SessionMetadata.from_dict(metadata_dict)
                    for session_id, metadata_dict in data.items()
                }
        except (ValueError, KeyError) as e:
            # If index is corrupted, rebuild it from existing session files
            print(f"Warning: Corrupted metadata index, rebuilding: {e}")
            return self._rebuild_metadata_index()
    
    def _save_metadata_index(self) -> None:
        """Save the metadata index to disk."""
        try:
            data = {
                session_id: metadata.to_dict()
                for session_id, metadata in self._metadata_index.items()
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except (OSError, ValueError) as e:
            raise SessionManagerError(f"Failed to save metadata index: {e}")
    
    def _rebuild_metadata_index(self) -> Dict[str, SessionMetadata]:
        """Rebuild metadata index from existing session files."""
        metadata_index = {}
        
        for session_file in self.sessions_dir.glob("*.json"):
            if session_file.name == "sessions_index.json":
                continue
            
            try:
                session_data = self._load_session_file(session_file)
                metadata_index[session_data.session_id] = session_data.metadata
            except Exception as e:
                print(f"Warning: Could not load session file {session_file}: {e}")
        
        return metadata_index
    
    def _get_session_file_path(self, session_id: str) -> Path:
        """Get the file path for a session."""
        return self.sessions_dir / f"{session_id}.json"
    
    def _load_session_file(self, file_path: Path) -> SessionData:
        """Load session data from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return SessionData.from_dict(data)
        except (ValueError, KeyError) as e:
            raise SessionCorruptedError(f"Session file {file_path} is corrupted: {e}")
        except OSError as e:
            raise SessionManagerError(f"Failed to read session file {file_path}: {e}")
    
    def generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())
    
    def save_session(self, session: SessionData, name: Optional[str] = None) -> str:
        """Save a session to disk.
        
        Args:
            session: Session data to save
            name: Optional human-readable name for the session
            
        Returns:
            The session ID
            
        Raises:
            SessionManagerError: If saving fails
        """
        # Ensure session has an ID
        if not session.session_id:
            session.session_id = self.generate_session_id()
        
        # Update metadata
        session.update_metadata()
        if name:
            session.metadata.name = name
        
        # Save session file
        session_file = self._get_session_file_path(session.session_id)
        
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
        except (OSError, ValueError) as e:
            raise SessionManagerError(f"Failed to save session {session.session_id}: {e}")
        
        # Update metadata index
        self._metadata_index[session.session_id] = session.metadata
        self._save_metadata_index()
        
        return session.session_id
    
    def load_session(self, session_id: str) -> SessionData:
        """Load a session from disk.
        
        Args:
            session_id: ID of the session to load
            
        Returns:
            The loaded session data
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionCorruptedError: If session data is corrupted
            SessionManagerError: If loading fails
        """
        session_file = self._get_session_file_path(session_id)
        
        if not session_file.exists():
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        return self._load_session_file(session_file)
    
    def list_sessions(self) -> List[SessionMetadata]:
        """List all available sessions.
        
        Returns:
            List of session metadata, sorted by last modified time (newest first)
        """
        sessions = list(self._metadata_index.values())
        sessions.sort(key=lambda s: s.last_modified or datetime.min, reverse=True)
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session.
        
        Args:
            session_id: ID of the session to delete
            
        Returns:
            True if session was deleted, False if it didn't exist
            
        Raises:
            SessionManagerError: If deletion fails
        """
        session_file = self._get_session_file_path(session_id)
        
        if not session_file.exists():
            return False
        
        try:
            session_file.unlink()
        except OSError as e:
            raise SessionManagerError(f"Failed to delete session {session_id}: {e}")
        
        # Remove from metadata index
        if session_id in self._metadata_index:
            del self._metadata_index[session_id]
            self._save_metadata_index()
        
        return True
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists.
        
        Args:
            session_id: ID of the session to check
            
        Returns:
            True if session exists, False otherwise
        """
        return session_id in self._metadata_index
    
    def get_session_metadata(self, session_id: str) -> Optional[SessionMetadata]:
        """Get metadata for a specific session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Session metadata if found, None otherwise
        """
        return self._metadata_index.get(session_id)
    
    def cleanup_orphaned_files(self) -> int:
        """Remove session files that aren't in the metadata index.
        
        Returns:
            Number of orphaned files removed
        """
        removed_count = 0
        
        for session_file in self.sessions_dir.glob("*.json"):
            if session_file.name == "sessions_index.json":
                continue
            
            session_id = session_file.stem
            if session_id not in self._metadata_index:
                try:
                    session_file.unlink()
                    removed_count += 1
                except OSError as e:
                    print(f"Warning: Could not remove orphaned file {session_file}: {e}")
        
        return removed_count
    
    def validate_all_sessions(self) -> Dict[str, str]:
        """Validate all sessions and return any errors found.
        
        Returns:
            Dictionary mapping session_id to error message for corrupted sessions
        """
        errors = {}
        
        for session_id in list(self._metadata_index.keys()):
            try:
                self.load_session(session_id)
            except (SessionCorruptedError, SessionManagerError) as e:
                errors[session_id] = str(e)
        
        return errors
    
    def recover_corrupted_sessions(self, remove_corrupted: bool = False) -> Dict[str, str]:
        """Attempt to recover corrupted sessions or remove them.
        
        Args:
            remove_corrupted: If True, remove corrupted sessions from index and disk
            
        Returns:
            Dictionary mapping session_id to recovery action taken
        """
        recovery_actions = {}
        corrupted_sessions = self.validate_all_sessions()
        
        for session_id, error_msg in corrupted_sessions.items():
            if remove_corrupted:
                try:
                    # Remove from metadata index
                    if session_id in self._metadata_index:
                        del self._metadata_index[session_id]
                    
                    # Remove file if it exists
                    session_file = self._get_session_file_path(session_id)
                    if session_file.exists():
                        session_file.unlink()
                    
                    recovery_actions[session_id] = f"Removed corrupted session: {error_msg}"
                except Exception as e:
                    recovery_actions[session_id] = f"Failed to remove corrupted session: {e}"
            else:
                recovery_actions[session_id] = f"Corrupted session found: {error_msg}"
        
        if remove_corrupted and corrupted_sessions:
            # Save updated metadata index
            try:
                self._save_metadata_index()
            except Exception as e:
                recovery_actions["metadata_index"] = f"Failed to save updated index: {e}"
        
        return recovery_actions
    
    def delete_multiple_sessions(self, session_ids: List[str]) -> Dict[str, bool]:
        """Delete multiple sessions in batch.
        
        Args:
            session_ids: List of session IDs to delete
            
        Returns:
            Dictionary mapping session_id to deletion success status
        """
        results = {}
        
        for session_id in session_ids:
            try:
                results[session_id] = self.delete_session(session_id)
            except SessionManagerError as e:
                results[session_id] = False
                print(f"Warning: Failed to delete session {session_id}: {e}")
        
        return results
    
    def get_sessions_by_date_range(self, start_date: datetime, end_date: datetime) -> List[SessionMetadata]:
        """Get sessions within a specific date range.
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            
        Returns:
            List of session metadata within the date range
        """
        filtered_sessions = []
        
        for metadata in self._metadata_index.values():
            if metadata.created_time:
                if start_date <= metadata.created_time <= end_date:
                    filtered_sessions.append(metadata)
        
        # Sort by creation time (newest first)
        filtered_sessions.sort(key=lambda s: s.created_time or datetime.min, reverse=True)
        return filtered_sessions
    
    def get_sessions_by_hands_played(self, min_hands: int = 0, max_hands: Optional[int] = None) -> List[SessionMetadata]:
        """Get sessions filtered by number of hands played.
        
        Args:
            min_hands: Minimum number of hands played
            max_hands: Maximum number of hands played (None for no limit)
            
        Returns:
            List of session metadata matching the criteria
        """
        filtered_sessions = []
        
        for metadata in self._metadata_index.values():
            hands_played = metadata.hands_played
            if hands_played >= min_hands:
                if max_hands is None or hands_played <= max_hands:
                    filtered_sessions.append(metadata)
        
        # Sort by hands played (descending)
        filtered_sessions.sort(key=lambda s: s.hands_played, reverse=True)
        return filtered_sessions
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about session storage.
        
        Returns:
            Dictionary with storage statistics
        """
        total_sessions = len(self._metadata_index)
        total_size = 0
        
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                total_size += session_file.stat().st_size
            except OSError:
                pass
        
        return {
            "sessions_directory": str(self.sessions_dir.absolute()),
            "total_sessions": total_sessions,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "metadata_index_exists": self.metadata_file.exists()
        }
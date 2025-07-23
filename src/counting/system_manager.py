"""Manager for counting system selection and switching."""

from typing import Dict, List, Optional
from .counting_system import CountingSystem
from .hi_lo import HiLoSystem
from .ko import KOSystem
from .hi_opt_i import HiOptISystem


class CountingSystemManager:
    """Manages available counting systems and provides selection capabilities."""
    
    def __init__(self):
        """Initialize the manager with default counting systems."""
        self._systems: Dict[str, CountingSystem] = {}
        self._register_default_systems()
    
    def _register_default_systems(self) -> None:
        """Register the default counting systems."""
        self.register_system(HiLoSystem())
        self.register_system(KOSystem())
        self.register_system(HiOptISystem())
    
    def register_system(self, system: CountingSystem) -> None:
        """Register a counting system.
        
        Args:
            system: The counting system to register
        """
        self._systems[system.name()] = system
    
    def get_system(self, name: str) -> Optional[CountingSystem]:
        """Get a counting system by name.
        
        Args:
            name: The name of the counting system
            
        Returns:
            The counting system if found, None otherwise
        """
        return self._systems.get(name)
    
    def list_systems(self) -> List[str]:
        """Get a list of available counting system names.
        
        Returns:
            List of counting system names
        """
        return list(self._systems.keys())
    
    def get_default_system(self) -> CountingSystem:
        """Get the default counting system (Hi-Lo).
        
        Returns:
            The Hi-Lo counting system
        """
        return self._systems["Hi-Lo"]
    
    def is_system_available(self, name: str) -> bool:
        """Check if a counting system is available.
        
        Args:
            name: The name of the counting system
            
        Returns:
            True if the system is available, False otherwise
        """
        return name in self._systems
    
    def __len__(self) -> int:
        """Get the number of registered systems."""
        return len(self._systems)
    
    def __iter__(self):
        """Iterate over available systems."""
        return iter(self._systems.values())
    
    def __str__(self) -> str:
        """String representation of available systems."""
        systems = ", ".join(self.list_systems())
        return f"CountingSystemManager({systems})"
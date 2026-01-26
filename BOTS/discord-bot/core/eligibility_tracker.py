"""
╔══════════════════════════════════════════════════════════════╗
║              🤖 KAZUHA VIP DISCORD AUTO BOT                  ║
║                  Created by Kazuha VIP Only                  ║
╚══════════════════════════════════════════════════════════════╝
Role Eligibility Tracking
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict


class EligibilityTracker:
    """Tracks role eligibility and action limits per server"""
    
    def __init__(self):
        self.server_status: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.daily_actions: Dict[str, int] = defaultdict(int)
        self.hourly_actions: Dict[str, int] = defaultdict(int)
        self.last_reset: Dict[str, str] = {}
        
    def _get_date_key(self) -> str:
        return datetime.now().strftime('%Y-%m-%d')
    
    def _get_hour_key(self) -> str:
        return datetime.now().strftime('%Y-%m-%d-%H')
    
    def _check_reset(self, server_id: str):
        """Reset counters if day/hour changed"""
        current_date = self._get_date_key()
        current_hour = self._get_hour_key()
        
        if self.last_reset.get(f"{server_id}_daily") != current_date:
            self.daily_actions[server_id] = 0
            self.last_reset[f"{server_id}_daily"] = current_date
        
        if self.last_reset.get(f"{server_id}_hourly") != current_hour:
            self.hourly_actions[server_id] = 0
            self.last_reset[f"{server_id}_hourly"] = current_hour
    
    def update_roles(self, server_id: str, current_roles: List[str], 
                    target_roles: List[str]):
        """Update role status for server"""
        self.server_status[server_id]['current_roles'] = current_roles
        self.server_status[server_id]['target_roles'] = target_roles
        
        # Check which target roles are obtained
        obtained = set(current_roles) & set(target_roles)
        pending = set(target_roles) - obtained
        
        self.server_status[server_id]['obtained_roles'] = list(obtained)
        self.server_status[server_id]['pending_roles'] = list(pending)
        self.server_status[server_id]['last_updated'] = datetime.now().isoformat()
    
    def can_perform_action(self, server_id: str, 
                           daily_cap: int = 25,
                           hourly_cap: int = 5,
                           server_daily_cap: int = 3) -> tuple[bool, str]:
        """Check if action can be performed"""
        self._check_reset(server_id)
        
        # Check hourly limit
        if self.hourly_actions.get(server_id, 0) >= hourly_cap:
            return False, f"Hourly limit reached ({hourly_cap})"
        
        # Check daily limit for server
        if self.daily_actions.get(server_id, 0) >= server_daily_cap:
            return False, f"Daily server limit reached ({server_daily_cap})"
        
        # Check global daily limit
        total_daily = sum(self.daily_actions.values())
        if total_daily >= daily_cap:
            return False, f"Global daily limit reached ({daily_cap})"
        
        return True, "Action allowed"
    
    def record_action(self, server_id: str):
        """Record an action was performed"""
        self._check_reset(server_id)
        self.daily_actions[server_id] += 1
        self.hourly_actions[server_id] += 1
    
    def get_server_status(self, server_id: str) -> Dict[str, Any]:
        """Get full status for server"""
        self._check_reset(server_id)
        
        return {
            **self.server_status.get(server_id, {}),
            'daily_actions': self.daily_actions.get(server_id, 0),
            'hourly_actions': self.hourly_actions.get(server_id, 0)
        }
    
    def is_role_obtained(self, server_id: str, role_name: str) -> bool:
        """Check if specific role is obtained"""
        obtained = self.server_status.get(server_id, {}).get('obtained_roles', [])
        return role_name.lower() in [r.lower() for r in obtained]
    
    def get_progress_summary(self, server_id: str) -> str:
        """Get human-readable progress summary"""
        status = self.get_server_status(server_id)
        
        obtained = len(status.get('obtained_roles', []))
        total = len(status.get('target_roles', []))
        daily = status.get('daily_actions', 0)
        
        if total == 0:
            return f"No target roles | {daily} actions today"
        
        return f"Roles: {obtained}/{total} | Actions: {daily} today"
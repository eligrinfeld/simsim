"""
Supabase client configuration and database operations for the Event Dashboard.
"""
import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import asyncio
from datetime import datetime

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

# Environment variables
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "https://nzlibwnjcjzbfqjsgfwr.supabase.co")
# Prefer service role for server-side writes; fall back to anon for dev
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")

class SupabaseClient:
    """Wrapper for Supabase operations with fallback when not available."""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.enabled = SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_KEY
        
        if self.enabled:
            try:
                self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print(f"✅ Supabase client initialized: {SUPABASE_URL[:30]}...")
            except Exception as e:
                print(f"❌ Failed to initialize Supabase client: {e}")
                self.enabled = False
        else:
            print("⚠️ Supabase not available - running in local-only mode")
    
    async def save_pine_strategy(self, user_id: str, name: str, code: str, 
                                parameters: Dict[str, Any], description: str = "") -> Optional[str]:
        """Save a Pine strategy to Supabase."""
        if not self.enabled:
            print(f"📝 Would save Pine strategy '{name}' (local mode)")
            return f"local-{hash(code)}"
        
        try:
            data = {
                "user_id": user_id,
                "name": name,
                "code": code,
                "parameters": parameters,
                "description": description,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("pine_strategies").insert(data).execute()
            strategy_id = result.data[0]["id"] if result.data else None
            print(f"✅ Saved Pine strategy '{name}' with ID: {strategy_id}")
            return strategy_id
            
        except Exception as e:
            print(f"❌ Failed to save Pine strategy: {e}")
            return None
    
    async def save_pine_result(self, strategy_id: str, symbol: str, timeframe: str,
                              sharpe_ratio: float, total_return: float, max_drawdown: float,
                              trade_count: int, trades: List[Dict], equity_curve: List[Dict] = None) -> Optional[str]:
        """Save Pine backtest results to Supabase."""
        if not self.enabled:
            print(f"📊 Would save Pine result for strategy {strategy_id} (local mode)")
            return f"result-{hash(str(trades))}"
        
        try:
            data = {
                "strategy_id": strategy_id,
                "symbol": symbol,
                "timeframe": timeframe,
                "sharpe_ratio": sharpe_ratio,
                "total_return": total_return,
                "max_drawdown": max_drawdown,
                "trade_count": trade_count,
                "trades": trades,
                "equity_curve": equity_curve or [],
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("pine_results").insert(data).execute()
            result_id = result.data[0]["id"] if result.data else None
            print(f"✅ Saved Pine result with ID: {result_id}")
            return result_id
            
        except Exception as e:
            print(f"❌ Failed to save Pine result: {e}")
            return None
    
    async def get_user_strategies(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all Pine strategies for a user."""
        if not self.enabled:
            print(f"📋 Would fetch strategies for user {user_id} (local mode)")
            return []
        
        try:
            result = self.client.table("pine_strategies")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .execute()
            
            strategies = result.data or []
            print(f"📋 Found {len(strategies)} strategies for user {user_id}")
            return strategies
            
        except Exception as e:
            print(f"❌ Failed to fetch user strategies: {e}")
            return []
    
    async def get_strategy_results(self, strategy_id: str) -> List[Dict[str, Any]]:
        """Get all results for a Pine strategy."""
        if not self.enabled:
            print(f"📊 Would fetch results for strategy {strategy_id} (local mode)")
            return []
        
        try:
            result = self.client.table("pine_results")\
                .select("*")\
                .eq("strategy_id", strategy_id)\
                .order("created_at", desc=True)\
                .execute()
            
            results = result.data or []
            print(f"📊 Found {len(results)} results for strategy {strategy_id}")
            return results
            
        except Exception as e:
            print(f"❌ Failed to fetch strategy results: {e}")
            return []
    
    async def save_user_session(self, user_id: str, name: str, symbol: str,
                               timeframe: str, metadata: Dict[str, Any]) -> Optional[str]:
        """Save a user analysis session."""
        if not self.enabled:
            print(f"💾 Would save session '{name}' (local mode)")
            return f"session-{hash(name)}"

        try:
            data = {
                "user_id": user_id,
                "name": name,
                "symbol": symbol,
                "timeframe": timeframe,
                "metadata": metadata,
                "created_at": datetime.utcnow().isoformat()
            }

            result = self.client.table("user_sessions").insert(data).execute()
            session_id = result.data[0]["id"] if result.data else None
            print(f"✅ Saved session '{name}' with ID: {session_id}")
            return session_id

        except Exception as e:
            print(f"❌ Failed to save session: {e}")
            return None

    async def save_event(self, evt: Dict[str, Any]) -> None:
        """Save an event (raw or derived) to Supabase events table.
        Expects dict with fields: type, key, ts, data
        """
        if not self.enabled:
            return
        try:
            payload = {
                "ts": datetime.utcfromtimestamp(int(evt.get("ts", 0))).isoformat() + "Z",
                "type": evt.get("type"),
                "key": evt.get("key"),
                "data": evt.get("data", {}),
                "source": (evt.get("data", {}) or {}).get("source", "cep"),
                "derived": evt.get("type") not in ["Bar", "NewsItem", "MacroRelease", "EarningsReport"]
            }
            self.client.table("events").insert(payload).execute()
        except Exception as e:
            print(f"⚠️ Failed to save event: {e}")

    async def get_events(self, symbol: str = None, since_ts: int = None,
                        until_ts: int = None, event_types: List[str] = None) -> List[Dict[str, Any]]:
        """Query events from Supabase for replay functionality."""
        if not self.enabled:
            print(f"📋 Would fetch events for {symbol} since {since_ts} (local mode)")
            return []

        try:
            query = self.client.table("events").select("*")

            if symbol:
                query = query.eq("key", symbol)
            if since_ts:
                since_iso = datetime.utcfromtimestamp(since_ts).isoformat() + "Z"
                query = query.gte("ts", since_iso)
            if until_ts:
                until_iso = datetime.utcfromtimestamp(until_ts).isoformat() + "Z"
                query = query.lte("ts", until_iso)
            if event_types:
                query = query.in_("type", event_types)

            result = query.order("ts", desc=False).limit(1000).execute()
            events = result.data or []

            # Convert back to frontend format
            formatted_events = []
            for evt in events:
                formatted_events.append({
                    "type": evt["type"],
                    "key": evt["key"],
                    "ts": int(datetime.fromisoformat(evt["ts"].replace("Z", "+00:00")).timestamp()),
                    "data": evt["data"] or {}
                })

            print(f"📋 Found {len(formatted_events)} events for replay")
            return formatted_events

        except Exception as e:
            print(f"❌ Failed to fetch events: {e}")
            return []

# Global instance
supabase_client = SupabaseClient()

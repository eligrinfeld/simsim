# Supabase Setup Guide for Event Dashboard

## 1. Database Setup

### Step 1: Run the Schema
1. Go to your Supabase project: https://nzlibwnjcjzbfqjsgfwr.supabase.co
2. Navigate to **SQL Editor** in the left sidebar
3. Copy and paste the contents of `schema.sql` into a new query
4. Click **Run** to create all tables and policies

### Step 2: Verify Tables Created
In the **Table Editor**, you should see these tables:
- `users_profile`
- `pine_strategies` 
- `pine_results`
- `user_sessions`
- `cep_rules`
- `historical_events`
- `user_annotations`
- `user_alerts`

## 2. Test the Integration

### Backend Test
```bash
# Test save strategy
curl -X POST 'http://127.0.0.1:8010/strategy/pine/save' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "MA Cross Strategy",
    "code": "strategy(title=\"MA Cross\")\nfast = input.int(10)\nslow = input.int(20)\nf = ta.sma(close, fast)\ns = ta.sma(close, slow)\nif ta.crossover(f, s): strategy.entry(\"Long\", strategy.long)\nif ta.crossunder(f, s): strategy.close(\"Long\")",
    "description": "Simple moving average crossover strategy",
    "user_id": "anonymous"
  }'

# Test list strategies
curl 'http://127.0.0.1:8010/strategy/pine/list?user_id=anonymous'
```

### Frontend Test
1. Go to http://127.0.0.1:8010
2. Scroll to the Pine section
3. Paste a strategy and click **Save**
4. Fill in the name and description
5. Click **Load** to see saved strategies

## 3. Features Available

### ✅ Currently Working
- **Save Pine Strategies**: Store Pine scripts with metadata
- **Load Pine Strategies**: Browse and load saved strategies
- **Local Fallback**: Works without Supabase (logs to console)
- **Performance Metrics**: Sharpe, Return, Max DD with explanations
- **Error Handling**: Graceful degradation if Supabase unavailable

### 🚧 Next Steps (Future Enhancement)
- **User Authentication**: Replace "anonymous" with real user IDs
- **Strategy Results Caching**: Auto-save backtest results
- **Public Strategy Library**: Share strategies with `is_public` flag
- **Session Replay**: Save analysis sessions for later review
- **Real-time Collaboration**: Multiple users working on strategies

## 4. Environment Variables

The app uses these Supabase credentials (already configured):
```
NEXT_PUBLIC_SUPABASE_URL=https://nzlibwnjcjzbfqjsgfwr.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 5. Troubleshooting

### If Save/Load Doesn't Work
1. Check browser console for errors
2. Verify Supabase tables exist
3. Check Row Level Security policies are enabled
4. Ensure anonymous access is allowed (for testing)

### If Supabase is Down
- App continues to work in local-only mode
- Strategies won't persist but Pine preview still functions
- Console shows "⚠️ Supabase not available - running in local-only mode"

## 6. Data Model Summary

```sql
-- Core tables for Pine strategy management
pine_strategies: id, user_id, name, code, parameters, description, is_public
pine_results: id, strategy_id, symbol, sharpe_ratio, total_return, max_drawdown, trades
user_sessions: id, user_id, name, symbol, timeframe, metadata
```

The system is designed to be resilient - it works great with Supabase for persistence, but degrades gracefully to local-only mode if needed.

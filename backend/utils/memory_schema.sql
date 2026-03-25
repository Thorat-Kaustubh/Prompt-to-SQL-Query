-- 1. Create the memory_logs table
-- Responsibility: Long-term archival of user query history.
-- Security: RLS policies at the table level ensure users see only their own data.

CREATE TABLE IF NOT EXISTS public.memory_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL, -- Ties to auth.users if using internal users, or external IDs
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT now(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 2. Enable Row Level Security (RLS)
ALTER TABLE public.memory_logs ENABLE ROW LEVEL SECURITY;

-- 3. Policy: Users can only see their own memory entries
CREATE POLICY "Users can view their own memory" 
ON public.memory_logs 
FOR SELECT 
USING (auth.uid() = user_id);

-- 4. Policy: Users can only insert their own entries
CREATE POLICY "Users can insert their own memory" 
ON public.memory_logs 
FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- 5. Indexes for retrieval optimization
CREATE INDEX IF NOT EXISTS idx_memory_logs_user_id ON public.memory_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_logs_timestamp ON public.memory_logs(timestamp DESC);

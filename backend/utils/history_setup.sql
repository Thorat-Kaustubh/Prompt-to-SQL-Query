-- 0. Create a Mock User for Development Bypass (Optional but recommended for local dev)
-- This prevents foreign key violations when using 'local-dev-token'
INSERT INTO public.users (id, email, role)
VALUES ('00000000-0000-0000-0000-000000000000', 'dev@antigravity.ai', 'admin')
ON CONFLICT (id) DO NOTHING;

-- 1. Create Conversations Table
CREATE TABLE IF NOT EXISTS public.conversations (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id uuid REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    title text DEFAULT 'New Chat',
    created_at timestamptz DEFAULT now(),
    last_message_at timestamptz DEFAULT now()
);

-- 2. Create Messages Table
CREATE TABLE IF NOT EXISTS public.messages (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    conversation_id uuid REFERENCES public.conversations(id) ON DELETE CASCADE NOT NULL,
    role text CHECK (role IN ('user', 'assistant')),
    content text NOT NULL,
    data jsonb, -- Stores SQL, tables, insights, etc.
    created_at timestamptz DEFAULT now()
);

-- 3. Enable Security (RLS)
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- 4. Policies: Users can only see/edit THEIR OWN history
CREATE POLICY conv_user_own ON public.conversations FOR ALL USING (auth.uid() = user_id);
CREATE POLICY msg_user_own ON public.messages FOR ALL USING (
    EXISTS (SELECT 1 FROM public.conversations WHERE id = conversation_id AND user_id = auth.uid())
);

from crewai import Agent, Task
from orchestrator.tools import VerifyIdentityTool, SQLGeneratorTool, SQLValidatorTool, DBExecutorTool

# --- Agent Definitions ---

def create_filter_agent(llm=None):
    return Agent(
        role="Security Specialist",
        goal="Classify intent and verify auth.",
        backstory="Zero-trust security filter. Fast, concise logic only.",
        tools=[VerifyIdentityTool()],
        llm=llm,
        allow_delegation=False,
        verbose=False
    )

def create_analyzer_agent(llm=None):
    return Agent(
        role="Database Architect",
        goal="Structure SQL logic through deep schema reasoning.",
        backstory="Expert DB architect. Models JOINS and FILTERS step-by-step.",
        llm=llm,
        allow_delegation=False,
        verbose=False
    )

def create_generator_agent(llm=None):
    return Agent(
        role="SQL Generator",
        goal="Write valid PostgreSQL from structural plans.",
        backstory="High-speed SQL dev. Precision and alias consistency is mandatory.",
        llm=llm,
        allow_delegation=False,
        verbose=False
    )

def create_refiner_agent(llm=None):
    return Agent(
        role="QA Refiner",
        goal="Polish and optimize SQL into final JSON format.",
        backstory="Perfectionist auditor. Enforces security and best practices.",
        llm=llm,
        allow_delegation=False,
        verbose=False
    )

# --- Task Definitions ---

def create_filter_task(agent, jwt_token, user_query):
    return Task(
        description=f"1. Filter and verify user identity using token: {jwt_token}.\n2. Classify the complexity of query: '{user_query}'.\n3. Output a JSON object with keys: 'status' (VERIFIED/DENIED), 'role', and 'complexity' (low/high).",
        expected_output="A JSON object with authentication status and query complexity classification.",
        agent=agent
    )

def create_analysis_task(agent, user_query, schema, history):
    return Task(
        description=f"Analyze user query: '{user_query}' against schema: {schema} and history: {history}. Create a detailed structure for the SQL query.",
        expected_output="A structured reasoning/plan for the SQL query construction.",
        agent=agent
    )

def create_generation_task(agent, user_query, schema, history):
    return Task(
        description=f"Generate the fastest possible valid SQL draft for query: '{user_query}' using provided context.",
        expected_output="A raw but syntactically correct SQL draft.",
        agent=agent
    )

def create_refinement_task(agent, sql_draft, jwt_token):
    return Task(
        description=f"Refine, validate, and execute the SQL draft: '{sql_draft}'. Ensure it is safe and return results using JWT: {jwt_token}.",
        expected_output="A JSON object containing: 'sql' (the refined query), 'explanation' (step-by-step logic), 'complexity' (Low/Medium/High), 'confidence' (0.0-1.0), and 'suggested_visualization' (Table/Bar Chart/etc.).",
        agent=agent
    )

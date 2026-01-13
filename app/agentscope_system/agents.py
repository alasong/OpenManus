from agentscope.agent import AgentBase, ReActAgent
from agentscope.message import Msg
from agentscope.model import ChatModelBase
from agentscope.formatter import OpenAIChatFormatter
from agentscope.tool import Toolkit
from agentscope.message import TextBlock, ToolResultBlock
from app.agentscope_system.tools import get_tools_list, ToolContext
from app.agent.browser import BrowserContextHelper

# Define System Prompts
PLANNER_SYSTEM_PROMPT = """You are a Planner Agent.
Your goal is to understand the user's complex request and break it down into a sequence of actionable steps.
Output the plan as a numbered list.
Do not execute the steps yourself.
Example:
1. Search for "Python 3.13 new features" using the browser.
2. Summarize the key features found.
3. Save the summary to a file named "python_3.13_features.txt".
"""

EXECUTOR_SYSTEM_PROMPT = """You are an Executor Agent.
You have access to powerful tools: Browser, Python Executor, File Editor.
Your goal is to execute the task given to you by the Planner or the User.
Use the provided tools to achieve the goal.
- To search or browse, use `browser_use_async` with action='go_to_url' or 'google_search'.
- To calculate or process data, use `python_execute_async`.
- To create or edit files, use `str_replace_editor_async`. For creating a new file, use command='create', path='...', file_text='...'.
"""

REVIEWER_SYSTEM_PROMPT = """You are a Reviewer Agent.
Your goal is to review the output of the Executor Agent.
Check if the goal has been achieved based on the execution result.
If yes, confirm it with a brief summary of what was done.
If no, provide feedback on what is missing or wrong.
"""

class DialogAgent(AgentBase):
    def __init__(self, name: str, sys_prompt: str, model: ChatModelBase, **kwargs):
        super().__init__()
        self.name = name
        self.sys_prompt = sys_prompt
        self.model = model
        self.memory = None # Basic AgentBase doesn't have memory by default, but we might need it? 
        # Actually AgentBase doesn't enforce memory structure.

    async def reply(self, x: Msg | None = None) -> Msg:
        # Build OpenAI-style messages
        messages = [{"role": "system", "content": self.sys_prompt}]
        if x:
            messages.append({"role": "user", "content": x.content})
        
        # Call model
        response = await self.model(messages)

        # Convert ChatResponse content blocks to plain text
        out_text_parts: list[str] = []
        try:
            for block in getattr(response, "content", []) or []:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        if isinstance(block.get("text"), str):
                            out_text_parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_result":
                        output = block.get("output")
                        if isinstance(output, str):
                            out_text_parts.append(output)
                        elif isinstance(output, list):
                            for sub in output:
                                if isinstance(sub, dict) and sub.get("type") == "text":
                                    out_text_parts.append(sub.get("text", ""))
        except Exception:
            pass

        final_text = "\n".join([p for p in out_text_parts if p]).strip() or ""
        msg = Msg(self.name, content=final_text, role="assistant")
        await self.print(msg)
        return msg

class ManusPlanner(DialogAgent):
    def __init__(self, name: str, model: ChatModelBase):
        super().__init__(name=name, sys_prompt=PLANNER_SYSTEM_PROMPT, model=model)

class ManusExecutor(ReActAgent):
    def __init__(self, name: str, model: ChatModelBase):
        # Register Tools
        tools = get_tools_list()
        toolkit = Toolkit()
        for tool in tools:
            toolkit.register_tool_function(tool)
        
        # Initialize Formatter
        # Assuming OpenAI style for now
        formatter = OpenAIChatFormatter()
            
        super().__init__(
            name=name, 
            sys_prompt=EXECUTOR_SYSTEM_PROMPT, 
            model=model, 
            formatter=formatter,
            toolkit=toolkit, 
        )

class ManusReviewer(DialogAgent):
    def __init__(self, name: str, model: ChatModelBase):
        super().__init__(name=name, sys_prompt=REVIEWER_SYSTEM_PROMPT, model=model)

# --- Dummy Agent Classes for Dependency Injection ---
class DummyMemory:
    def to_string(self):
        return ""

class DummyManusAgent:
    """
    A dummy agent to satisfy BrowserContextHelper's dependency on an agent 
    with 'available_tools' and 'memory'.
    """
    def __init__(self):
        from app.tool.tool_collection import ToolCollection
        from app.tool.browser_use_tool import BrowserUseTool
        
        # Initialize ToolCollection with BrowserUseTool so get_tool("browser_use") works
        self.available_tools = ToolCollection(BrowserUseTool())
        self.memory = DummyMemory()

# Helper to initialize the environment for the executor
class ExecutorEnv:
    def __init__(self, manus_instance):
        self.manus_instance = manus_instance
        
    def setup(self):
        # Initialize ToolContext
        ctx = ToolContext.get_instance()
        
        # Helper needs an agent with available_tools and memory
        helper = BrowserContextHelper(self.manus_instance)
        ctx.set_browser_helper(helper)

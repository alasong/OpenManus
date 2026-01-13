import asyncio
from typing import Optional, Any
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.python_execute import PythonExecute
from app.tool.str_replace_editor import StrReplaceEditor
from app.tool.ask_human import AskHuman
from app.agent.browser import BrowserContextHelper
from app.tool.base import ToolResult
import json
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

# Global context holder to maintain state across tool calls
class ToolContext:
    _instance = None
    
    def __init__(self):
        self.browser_helper: Optional[BrowserContextHelper] = None
        self.browser_tool = BrowserUseTool()
        self.python_tool = PythonExecute()
        self.editor_tool = StrReplaceEditor()
        self.ask_human_tool = AskHuman()
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_browser_helper(self, helper: BrowserContextHelper):
        self.browser_helper = helper

# Helper to format ToolResult to ToolResponse
def _format_result(result: ToolResult | dict) -> ToolResponse:
    # Accept ToolResult or dict (PythonExecute returns dict)
    content_str = ""
    if isinstance(result, ToolResult):
        content_str = result.output or ""
        if result.error:
            content_str = f"Error: {result.error}\nOutput: {content_str}"
    elif isinstance(result, dict):
        obs = result.get("observation")
        success = result.get("success")
        if obs is None:
            content_str = json.dumps(result, ensure_ascii=False, indent=2)
        else:
            content_str = obs
        if success is False:
            content_str = f"Error: {content_str}"
    else:
        content_str = str(result)

    return ToolResponse(content=[TextBlock(type="text", text=content_str)])

# --- Wrapper Functions for AgentScope ---

async def browser_use_async(
    action: str,
    url: str = None,
    index: int = None,
    text: str = None,
    scroll_amount: int = None,
    actions: list = None,
    **kwargs
) -> ToolResponse:
    """
    Control a web browser to navigate, click, type, and extract information.
    
    Args:
        action (str): The action to perform (e.g., 'go_to_url', 'click_element', 'input_text', 'scroll_down', 'batch').
        url (str, optional): URL for navigation.
        index (int, optional): Element index for interaction.
        text (str, optional): Text to input.
        scroll_amount (int, optional): Pixels to scroll.
        actions (list, optional): List of actions for batch mode.
    """
    ctx = ToolContext.get_instance()
    if not ctx.browser_helper:
        return ToolResponse(content=[TextBlock(type="text", text="Error: Browser context not initialized.")])
    
    try:
        # Execute directly, tool handles context internally
        result = await ctx.browser_tool.execute(
            action=action,
            url=url,
            index=index,
            text=text,
            scroll_amount=scroll_amount,
            actions=actions,
            **kwargs
        )
        return _format_result(result)
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"Browser execution failed: {str(e)}")])

async def python_execute_async(code: str, **kwargs) -> ToolResponse:
    """
    Execute Python code.
    
    Args:
        code (str): The Python code to execute.
    """
    ctx = ToolContext.get_instance()
    try:
        result = await ctx.python_tool.execute(code=code, **kwargs)
        return _format_result(result)
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"Python execution failed: {str(e)}")])

async def str_replace_editor_async(
    command: str,
    path: str,
    file_text: str = None,
    view_range: list = None,
    old_str: str = None,
    new_str: str = None,
    insert_line: int = None,
    **kwargs
) -> ToolResponse:
    """
    Edit files using string replacement or view file content.
    
    Args:
        command (str): Command to execute (view, create, str_replace, insert, undo_edit).
        path (str): Path to the file.
        file_text (str, optional): Content for creating file.
        view_range (list, optional): [start_line, end_line] for viewing.
        old_str (str, optional): String to replace.
        new_str (str, optional): Replacement string.
        insert_line (int, optional): Line number for insertion.
    """
    ctx = ToolContext.get_instance()
    try:
        result = await ctx.editor_tool.execute(
            command=command,
            path=path,
            file_text=file_text,
            view_range=view_range,
            old_str=old_str,
            new_str=new_str,
            insert_line=insert_line,
            **kwargs
        )
        return _format_result(result)
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"Editor execution failed: {str(e)}")])

async def ask_human_async(question: str, **kwargs) -> ToolResponse:
    """
    Ask the human user a question.
    
    Args:
        question (str): The question to ask.
    """
    ctx = ToolContext.get_instance()
    try:
        result = await ctx.ask_human_tool.execute(question=question, **kwargs)
        return _format_result(result)
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"Ask human failed: {str(e)}")])

def get_tools_list():
    # AgentScope Toolkit expects functions
    return [
        browser_use_async,
        python_execute_async,
        str_replace_editor_async,
        ask_human_async
    ]

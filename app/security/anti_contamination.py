from app.llm import LLM
from app.logger import logger
from app.schema import Message

class AntiContamination:
    """Based on LLM anti-contamination system to purify user input."""
    
    def __init__(self):
        self.llm = LLM()

    async def purify(self, text: str, history: list[Message] = None) -> str:
        """
        Analyze and purify user input using LLM.
        Removes emotional, biased, subjective, and informal content while preserving intent.
        
        Args:
            text: The user input text to purify
            history: Optional list of previous conversation messages for context resolution
        """
        if not text or not text.strip():
            return text

        logger.debug("🛡️ Analyzing and purifying user input...")
        
        # Build context string from history if provided
        context_str = ""
        if history:
            # Use last 5 messages for context
            recent_history = history[-5:]
            context_str = "\n\nConversation Context (for reference ONLY to resolve pronouns like 'it', 'above', 'previous'):\n"
            for msg in recent_history:
                role = msg.role
                content = str(msg.content)[:200] + "..." if msg.content and len(str(msg.content)) > 200 else str(msg.content)
                context_str += f"{role}: {content}\n"
        
        system_prompt = """你是一个专业的文本分析与净化专家。你的任务是重写用户的输入以去除"污染"成分（如情绪化表达、偏见、歧视、过度主观臆断等），但必须严格保留用户的原始意图和核心事实。

关键规则：
1. **绝对禁止回答问题**：如果用户输入是一个问题，你必须保留该问题形式，而不能试图回答它。
2. **绝对禁止扩展内容**：不要添加任何用户未提及的信息、解释或背景知识。
3. **保留专业术语**：严禁修改任何技术名词、实体名称或专业术语（如 "上下文工程", "RAG", "Prompt Engineering" 等）。
4. **保持原意**：如果输入本身是干净的，请原样返回。
5. **上下文感知**：如果用户引用了之前的对话（如“上面的”、“之前提到的”），请参考提供的对话上下文来明确指代对象，但不要在输出中包含上下文本身，而是生成一个明确的、独立的意图描述。

示例：
输入："我非常生气！告诉我为什么Python这么慢？垃圾语言！"
输出："请解释为什么Python的运行速度较慢。"

输入："AI的上下文工程有哪些技术？"
输出："AI的上下文工程有哪些技术？"

输入："那个KV Cache技术，详细讲讲。" (假设上下文中提到了KV Cache)
输出："请详细讲解KV Cache技术。"

请处理以下输入，直接返回净化后的文本，不要包含任何解释或引号。"""

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"{context_str}\n\nUser Input to Purify: {text}")
        ]

        try:
            # Using non-streaming request for purification
            purified_text = await self.llm.ask(messages, stream=False)
            purified_text = purified_text.strip()
            
            # Simple check if text was modified significantly (ignoring whitespace)
            if purified_text != text.strip():
                logger.warning(f"✨ Input purified successfully")
                logger.info(f"Original: {text}")
                logger.warning(f"Purified: {purified_text}")
            else:
                logger.debug("✅ Input is clean")
                
            return purified_text
        except Exception as e:
            logger.error(f"Failed to purify input: {e}")
            # Fallback to original text if purification fails
            return text

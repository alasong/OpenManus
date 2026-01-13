from app.llm import LLM
from app.logger import logger
from app.schema import Message

class AntiContamination:
    """Based on LLM anti-contamination system to purify user input."""
    
    def __init__(self):
        self.llm = LLM()

    async def purify(self, text: str) -> str:
        """
        Analyze and purify user input using LLM.
        Removes emotional, biased, subjective, and informal content while preserving intent.
        """
        if not text or not text.strip():
            return text

        logger.debug("🛡️ Analyzing and purifying user input...")
        
        system_prompt = """你是一个专业的文本分析与净化专家。你的任务是检测用户输入中的"污染"成分，包括：
1. 情绪化表达（愤怒、焦虑、悲观等）
2. 偏见与歧视
3. 过度主观臆断
4. 不规范的表达（如果影响理解）

请重写用户的输入，去除上述污染成分，保持核心事实和意图不变。
如果输入本身是干净的，请原样返回，不要做任何修改。
直接返回文本，不要包含任何解释、引号或额外的前缀/后缀。"""

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=text)
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

from typing import List, Dict, Any
import agentscope
from app.config import config

def load_agentscope_config():
    """
    Load OpenManus config and convert to AgentScope configuration.
    """
    # Get LLM config from OpenManus config
    llm_settings = config.llm
    
    # We primarily use the default config (usually 'default' or the first one)
    # AgentScope expects a list of model configs
    
    model_configs = []
    
    # Iterate over all defined LLM settings
    for name, setting in llm_settings.items():
        # Map OpenManus config to AgentScope config
        # AgentScope supports: openai_chat, dashscope_chat, etc.
        
        # Determine model type
        model_type = "openai_chat" # Default fallback
        if "azure" in setting.api_type.lower():
            model_type = "azure_chat"
        # Add other mappings as needed
            
        cfg = {
            "config_name": name,  # Unique name for this config
            "model_type": model_type,
            "model_name": setting.model,
            "api_key": setting.api_key,
            "temperature": setting.temperature,
            "max_tokens": setting.max_tokens,
        }
        
        if setting.base_url:
            cfg["client_args"] = {"base_url": setting.base_url}
            
        # For Azure
        if model_type == "azure_chat":
            cfg["api_version"] = setting.api_version
            cfg["azure_endpoint"] = setting.base_url
        model_configs.append(cfg)
    
    # Initialize AgentScope logging/environment
    agentscope.init(logging_level="INFO")
    
    return model_configs

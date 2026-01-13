from typing import List, Optional, Dict, Any
import os

from alibabacloud_iqs20241111.client import Client
from alibabacloud_iqs20241111 import models as iqs_models
from alibabacloud_tea_openapi import models as open_api_models
from app.config import config
from app.logger import logger
from app.tool.search.base import SearchItem, WebSearchEngine


class AliUnifiedSearchEngine(WebSearchEngine):
    client: Optional[Any] = None

    def __init__(self):
        super().__init__()
        self.client = self._create_client()

    def _create_client(self) -> Optional[Client]:
        api_key = None
        api_secret = None
        endpoint = "iqs.cn-zhangjiakou.aliyuncs.com"

        if getattr(config, "search_config", None):
            api_key = getattr(config.search_config, "ali_api_key", None)
            api_secret = getattr(config.search_config, "ali_api_secret", None)
            endpoint = getattr(
                config.search_config,
                "ali_endpoint",
                "iqs.cn-zhangjiakou.aliyuncs.com",
            )

        # Fallback to environment variables
        if not api_key:
            api_key = os.environ.get("ALI_API_KEY")
        if not api_secret:
            api_secret = os.environ.get("ALI_API_SECRET")

        # Also check for ALI_ACCESS_ID / ALI_ACCESS_SECRET which are commonly used
        access_id = os.environ.get("ALI_ACCESS_ID")
        access_secret = os.environ.get("ALI_ACCESS_SECRET")
        
        # Heuristic: If api_key looks invalid (e.g. not starting with LTAI) and access_id looks valid, use access_id
        # Note: Some STS tokens might not start with LTAI, but for simple integration LTAI is common.
        # If api_key is set but doesn't look like a standard ID, and we have a standard looking ID in env, prefer env.
        if access_id and (not api_key or (not api_key.startswith("LTAI") and access_id.startswith("LTAI"))):
            logger.info("Using ALI_ACCESS_ID from environment as it appears more valid than configured api_key")
            api_key = access_id
            
        if access_secret and (not api_secret or len(str(api_secret)) < 10 or str(api_secret).startswith("${")): 
             logger.info("Using ALI_ACCESS_SECRET from environment")
             api_secret = access_secret

        endpoint = os.environ.get("ALI_ENDPOINT") or endpoint

        if not api_key or not api_secret:
            logger.warning("AliUnifiedSearch is not configured with credentials.")
            return None

        try:
            c = open_api_models.Config(
                access_key_id=api_key, access_key_secret=api_secret
            )
            c.endpoint = endpoint
            return Client(c)
        except Exception as e:
            logger.error(f"Failed to create AliUnifiedSearch client: {e}")
            return None

    def perform_search(
        self, query: str, num_results: int = 20, **kwargs
    ) -> List[SearchItem]:
        if not self.client:
            logger.warning(
                "AliUnifiedSearch client is not initialized. Check configuration."
            )
            return []

        try:
            advanced_params: Dict[str, Any] = {}
            if num_results:
                advanced_params["page_size"] = num_results

            time_range = kwargs.get("time_range", None)

            unified_input = iqs_models.UnifiedSearchInput(
                query=query,
                time_range=time_range,
                advanced_params=advanced_params,
            )

            request = iqs_models.UnifiedSearchRequest(body=unified_input)
            response = self.client.unified_search(request)

            if not response.body or not response.body.page_items:
                return []

            search_items: List[SearchItem] = []
            for item in response.body.page_items:
                search_items.append(
                    SearchItem(
                        title=item.title or "",
                        url=item.link or "",
                        snippet=item.snippet or item.summary or "",
                        description=item.summary or item.snippet or "",
                        extra={
                            "markdown_text": item.markdown_text,
                            "main_text": item.main_text,
                            "published_time": item.published_time,
                        },
                    )
                )

            return search_items[:num_results]

        except Exception as e:
            logger.error(f"AliUnifiedSearch failed: {e}")
            return []

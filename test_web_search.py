import asyncio
from app.tool.web_search import WebSearch

async def main():
    ws = WebSearch()
    resp = await ws.execute(query="AI办公助手 平台 对比", num_results=8, fetch_content=False)
    print("error:", resp.error)
    print("total:", len(resp.results))
    for r in resp.results:
        print(f"[{r.position}] {r.source} | {r.title} -> {r.url}")
    if resp.metadata:
        print("metadata:", resp.metadata.model_dump())

if __name__ == "__main__":
    asyncio.run(main())

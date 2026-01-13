import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agentscope_system.config_loader import load_agentscope_config
from app.agentscope_system.agents import ManusPlanner, ManusExecutor, ManusReviewer, ExecutorEnv, DummyManusAgent
from agentscope.agent import UserAgent
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel

async def main():
    try:
        # 1. Load Config
        print("Loading AgentScope configuration...")
        model_configs = load_agentscope_config()
        if not model_configs:
            print("Error: No valid LLM configuration found in config.toml")
            return
            
        default_config = model_configs[0]
        print(f"Using model config: {default_config['config_name']}")
        
        # Instantiate Model
        client_kwargs = default_config.get("client_args", {})
        generate_kwargs = {
            "temperature": default_config.get("temperature", 0.0),
            "max_tokens": default_config.get("max_tokens", 4096)
        }
        
        model = OpenAIChatModel(
                    model_name=default_config["model_name"],
                    api_key=default_config["api_key"],
                    client_kwargs=client_kwargs,
                    generate_kwargs=generate_kwargs,
                    stream=False  # Disable streaming for easier handling
                )
        
        # 2. Setup Environment (Browser Context)
        print("Setting up Executor Environment...")
        dummy_agent = DummyManusAgent()
        env = ExecutorEnv(dummy_agent)
        env.setup()
        
        # 3. Initialize Agents
        print("Initializing Agents...")
        user_agent = UserAgent(name="User")
        planner = ManusPlanner(name="Planner", model=model)
        executor = ManusExecutor(name="Executor", model=model)
        reviewer = ManusReviewer(name="Reviewer", model=model)
        
        # 4. Define the Flow
        print("\n=== AgentScope OpenManus System Ready ===")
        
        # Check for command line arguments for non-interactive mode
        if len(sys.argv) > 1:
            query = " ".join(sys.argv[1:])
            print(f"Executing in non-interactive mode with query: {query}")
            msg = Msg(name="User", content=query, role="user")
            non_interactive = True
        else:
            print("Enter your request (or 'exit' to quit):")
            msg = await user_agent()
            non_interactive = False
        
        while True:
            if msg.content.lower() in ["exit", "quit", "done"]:
                break
                
            print("\n--- Planning Phase ---")
            # Planner creates a plan
            plan_msg = await planner(msg)
            # plan_msg is a Msg object, access content via plan_msg.content
            
            print("\n--- Execution Phase ---")
            # Executor executes (ReAct loop inside)
            exec_msg = await executor(plan_msg)
            print(f"Executor Output: {exec_msg.content}")
            
            print("\n--- Review Phase ---")
            # Reviewer checks
            # Construct context for reviewer
            review_context = f"""
Original Request: {msg.content}
Plan:
{plan_msg.content}

Execution Result:
{exec_msg.content}
"""
            review_input_msg = Msg(name="System", content=review_context, role="user")
            review_msg = await reviewer(review_input_msg)
            
            # Output final result to user
            print(f"\nFinal Result:\n{review_msg.content}\n")
            
            if non_interactive:
                break
            
            # Ask user for next step
            msg = await user_agent(review_msg)
            
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

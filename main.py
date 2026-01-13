import argparse
import asyncio

from app.agent.manus import Manus
from app.logger import logger
from app.security.anti_contamination import AntiContamination


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run Manus agent with a prompt")
    parser.add_argument(
        "--prompt", type=str, required=False, help="Input prompt for the agent"
    )
    args = parser.parse_args()

    # Create and initialize Manus agent
    agent = await Manus.create()
    try:
        while True:
            # Use command line prompt if provided, otherwise ask for input
            if args.prompt:
                prompt = args.prompt
                args.prompt = None # Only use it once
            else:
                try:
                    prompt = input("\nEnter your prompt (or 'exit' to quit): ")
                except EOFError:
                    break

            if prompt.lower() in ['exit', 'quit']:
                logger.info("Goodbye!")
                break
            
            if not prompt.strip():
                logger.warning("Empty prompt provided.")
                continue

            # Purify user input
            anti_contamination = AntiContamination()
            prompt = await anti_contamination.purify(prompt, history=agent.memory.messages)

            logger.warning("Processing your request...")
            await agent.run(prompt)
            logger.info("Request processing completed.")
            
    except KeyboardInterrupt:
        logger.warning("Operation interrupted.")
    finally:
        # Ensure agent resources are cleaned up before exiting
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

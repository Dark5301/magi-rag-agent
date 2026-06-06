import asyncio 
import logfire
from agent import story_agent
from core.dependencies import AgentDeps  
from tools.RAG import RAGPipeline

class CLIOrchestrator:
    """
    Manages the lifecycle, user interaction loop, and telemetry for the terminal-based literary assistant.
    """
    def __init__(self):
        self.rag_pipeline = None
        self.message_history = []

    def initialise_system(self) -> bool:
        """
        Boots heavy infrastructure and handles early degradation.
        """
        with logfire.span('orchestrator.startup') as span:
            logfire.info('Initialising persistent database connections...')
            try:
                # Initialise the persistent pipeline once
                self.rag_pipeline = RAGPipeline()
                logfire.info('Database connection successfully established.')
                return True 
            except Exception as e:
                logfire.error('System boot failed. Qdrant connection unreachable.', error=str(e))
                print(f'\nCRITICAL: Failed to connect to the database. {e}')
                return False 
    
    async def handle_turn(self, user_input: str):
        """
        Executes a single interaction turn with struct logging and schema utilisation.
        """
        # 1. Mint a fresh backpack for this specific turn 
        current_deps = AgentDeps(rag_pipeline=self.rag_pipeline)

        with logfire.span('orchestrator.chat_turn', user_input=user_input) as span:
            try:
                # 2. Execute the agent pass
                result = await story_agent.run(
                    user_input,
                    deps=current_deps,
                    message_history=self.message_history
                )

                # 3. Safely update our evolutionary history timeline 
                self.message_history = result.new_messages()
                logfire.info('Agent execution completed successfully. Updating conversation timeline.')

                answer = result.output.answer 
                confidence = result.output.confidence
                reasoning = result.output.reasoning 
                tool_used = result.output.action_taken

                # 4. UI Presentation 
                print(f"\n" + "="*40)
                print(f"🛠️  TOOL UTILIZED : {tool_used}")
                print(f"🧠 AGENT REASONING: {reasoning}")
                print(f"📊 CONFIDENCE     : {confidence.value}/10")
                print(f"临" + "="*40)
                print(f"\nAgent:\n{answer}\n")

                span.set_attribute('agent_confidenc', confidence)
                span.set_attribute('tool_selection', tool_used)
            except Exception as e:
                logfire.error('Agent encountered a runtime execution failure.', error=str(e))
                print(f'\nSystem Error during processing: {e}')

    
    async def start(self):
        """
        Triggers the infinite human interactive shell loop.
        """
        if not self.initialise_system():
            return
        
        print('\nSystem Online! You are now talking to the "Gift of the Magi" Agent.')
        print("Type 'quit' or 'exit' to shut down.\n")
        print('-'*50)

        while True:
            try:
                user_input = input('You: ')

                if user_input.lower() in ['quit', 'exit']:
                    logfire.info('User initiated manual application shutdown.')
                    print('Shutting down the system. Goodbye!')
                    break

                if not user_input.strip():
                    continue

                await self.handle_turn(user_input)
            except (KeyboardInterrupt, EOFError):
                logfire.info('System process interrupted via terminal signal.')
                print('\nInterrupted. Exiting cleanly.')
                break

if __name__ == '__main__':
    orchestrator = CLIOrchestrator()
    asyncio.run(orchestrator.start())
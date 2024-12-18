from metagpt.actions import Action

class AskLLM(Action):
    name: str = "AskLLLM"
    profile: str = "Ask LLLM for the result of the DataInterpreter"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def run(self, question: str, system="") -> str:
        if system:
            rsp = await self._aask(question, [system])
        else:
            rsp = await self._aask(question)
        return rsp

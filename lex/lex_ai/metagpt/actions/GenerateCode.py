from lex_ai.metagpt.generate_project_code import generate_project_code_prompt_old, regenerate_project_code_prompt
from metagpt.actions import Action

class GenerateCode(Action):
    name: str = "GenerateCode"

    async def run(self, project, lex_app_context: str, code: str, class_to_generate, user_feedback, import_pool, stderr=None, reflection_context=None):
        if not stderr:
            prompt = generate_project_code_prompt_old(project, lex_app_context, code, class_to_generate, user_feedback, import_pool)
        else:
            prompt = regenerate_project_code_prompt(project, lex_app_context, code, class_to_generate, user_feedback, import_pool, stderr, reflection_context=reflection_context)

        code = await self._aask(prompt, [
            "** [YOU ARE A SOFTWARE ENGINEER AND YOU ARE TASKED TO COMPLETE EVERYTHING IN THE PROJECT] **"
        ])

        return code
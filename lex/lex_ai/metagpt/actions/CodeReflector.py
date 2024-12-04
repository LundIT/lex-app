from lex_ai.metagpt.generate_project_code import regenerate_project_code_prompt
from lex.lex_ai.metagpt.roles.LLM import LLM




class CodeReflector:
    def __init__(self, error_info, code_context, original_prompt, context, project):
        self.error_info = error_info
        self.code_context = code_context
        self.original_prompt = original_prompt
        self.context = context
        self.project = project

    def analyze_error(self):
        """
        Analyzes test errors and provides structured insights for code regeneration
        """
        prompt = f"""
        [ORIGINAL SPEFICIATION]
        {self.original_prompt}
        
        [CONTEXT]
        {self.context}
        
        [CODE CONTEXT]
        {self.code_context}
        
        
        [FILES AND THEIR COLUMNS]
        {self.project.files_with_analysis}
        
        Analyze the following test error and provide insights:
        
        [ERROR ANALYSIS]
        Test Code: {self.error_info['test_code']}
        Class Code: {self.error_info['class_code']}
        Error Message: {self.error_info['error_message']}
        Corrected Code (Not tested yet): {self.error_info['corrected_code']}    

        Please analyze:
        0. The data/files are always correct (columns/rows) and the error is always due to the code.
        1. What is the root cause of this error assuming the code is incorrect somewhere?
        2. Don't provide any code, just give a comprehensive analysis of the error and the potential fix (Adhering to the **Context** and **Original Prompt's Specification**)
        3. Be structured and detailed and don't give generic answers (Adhering to the **Context** and **Original Prompt's Specification**)
        4. Keep it really short and direct (Write the reason and where is the problem in the code)
        
        Questions to answer:
        1. Are the models field aligned with the columns in the data in the uploaded file (According to [FILES AND THEIR COLUMNS]? (If it's a data upload error)
        2. Are imports correct ?

        Provide a structured analysis of maximum 10 sentences that can guide code regeneration.
        """

        return prompt

    def create_regeneration_context(self, reflection_result, original_error):
        """
        Creates context for code regeneration based on reflection
        """
        return {
            # 'original_error': original_error,
            'analysis': reflection_result
            # 'regeneration_guidelines': {
            #     'focus_areas': [],
            #     'constraints': [],
            #     'patterns_to_follow': []
            # }
        }

    async def regenerate(self, regen_context, regeneration_func):
        return await regeneration_func(regen_context)

    async def reflect(self):
        llm = LLM()
        # Step 1: Reflect on the error
        reflection_prompt = self.analyze_error()

        # Step 2: Get LLM analysis
        reflection_result = await llm.run(reflection_prompt)

        # Step 3: Create regeneration context
        regen_context = self.create_regeneration_context(
            reflection_result.content,
            self.error_info
        )

        # Step 4: Use existing regeneration prompt with added insights
        return regen_context
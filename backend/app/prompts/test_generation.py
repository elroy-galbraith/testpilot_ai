"""Prompt templates for test generation."""

from langchain.prompts import PromptTemplate

# Template for generating test cases from product specifications
TEST_GENERATION_TEMPLATE = PromptTemplate(
    input_variables=["specification", "framework", "language"],
    template="""You are an expert QA engineer tasked with generating comprehensive test cases.

Product Specification:
{specification}

Framework: {framework}
Programming Language: {language}

Please generate test cases that cover:
1. Happy path scenarios
2. Edge cases and error conditions
3. Input validation
4. Performance considerations
5. Security aspects

For each test case, provide:
- Test name and description
- Test steps
- Expected results
- Test data requirements

Format the output as structured test cases that can be executed by automated testing tools.

Test Cases:"""
)

# Template for generating Playwright test scripts
PLAYWRIGHT_TEMPLATE = PromptTemplate(
    input_variables=["test_case", "base_url"],
    template="""Generate a Playwright test script for the following test case:

Test Case: {test_case}
Base URL: {base_url}

Create a complete, executable Playwright test that:
- Uses proper page object patterns
- Includes proper assertions
- Handles async operations correctly
- Includes error handling
- Uses descriptive test names and comments

Playwright Test Script:"""
)

# Template for generating English test descriptions
ENGLISH_TEMPLATE = PromptTemplate(
    input_variables=["test_case"],
    template="""Convert the following test case into clear, human-readable English:

Test Case: {test_case}

Provide a detailed description that includes:
- What the test is checking
- Step-by-step instructions
- Expected outcomes
- Any prerequisites or setup requirements
- Business value and importance

English Test Description:"""
) 
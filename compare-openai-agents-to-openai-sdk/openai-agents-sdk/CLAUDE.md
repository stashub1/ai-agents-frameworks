### Each change should be added to /docs folder to *.md file.
## Coding Standards
- **SOLID Principles**: Ensure single responsibilities; favor composition over inheritance.
- **KISS**: Prioritize simple, readable Python over "clever" or over-engineered solutions.
- **Clean Code**: Follow PEP 8, use descriptive variable names, and include type hints.
- **YAGNI**: Implement only the functionality currently required.
- **TESTS**: Perform testing after your changes
- **BEST_PRACTICES**: Implement only according to best practices of framework you are working with.
- For a complex funcions and methods add description in comment what the function is doing. Without description of parameters or return statement

## Comments
- Section dividers use wide separator style: `# ---------------------------------------- Section ----------------------------------------`
- For each file on top write file name and path

## Project Structure
- `src/database.py` — schema init only (`init_db`)
- `src/services/storage.py` — all session and message queries
- `src/workflows/chat_workflow.py` — streaming response logic
- `src/agents/chat_agent.py` — agent definition

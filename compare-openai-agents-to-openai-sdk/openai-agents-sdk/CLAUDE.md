## Coding Standards
- **SOLID Principles**: Ensure single responsibilities; favor composition over inheritance.
- **KISS**: Prioritize simple, readable Python over "clever" or over-engineered solutions.
- **Clean Code**: Follow PEP 8, use descriptive variable names, and include type hints.
- **YAGNI**: Implement only the functionality currently required.
- **BEST_PRACTICES**: Implement only according to best practices of framework you are working with.

## Comments
- Section dividers use wide separator style: `# ---------------------------------------- Section ----------------------------------------`

## Project Structure
- `src/database.py` — schema init only (`init_db`)
- `src/services/storage.py` — all session and message queries
- `src/workflows/chat_workflow.py` — streaming response logic
- `src/agents/chat_agent.py` — agent definition

# Skill Selection
Select the best skill based on prompt keywords.

## Guidelines
- Map user prompts to specific skills based on matching keywords. In case of multiple matches, prioritize based on the first relevant keywords.
- **Workflow**:
  - `cleanup`, `refactor`, `format`: Use `CodeCleanupSkill`.
  - `documentation`, `docu`, `update`: Use `UpdateDocumentationSkill`.
  - `test`, `validate`, `verify`: Use `TestingAndCleanupSkill`.
  - `task`, `todo`, `track`: Use `TaskManagementSkill`.
  - always add `ResponseQualitySkill` to any response.

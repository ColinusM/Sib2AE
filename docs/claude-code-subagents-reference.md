# Claude Code Sub-Agents Reference

## Overview

Sub-agents are specialized AI assistants within Claude Code that operate with their own context window and custom configuration. They solve the "context pollution" problem by isolating specific tasks into focused conversations.

## Key Features

- **Context Isolation**: Each sub-agent operates with a separate context window
- **Specialized Functionality**: Task-specific configurations with custom system prompts
- **Tool Access Control**: Granular control over which tools each agent can access
- **Proactive Invocation**: Can be automatically selected based on task context

## Configuration

Sub-agents are defined in Markdown files with YAML frontmatter:

```markdown
---
name: agent-name
description: Purpose and when to invoke this agent
tools: [Read, Grep, Glob, Bash]  # Optional - specific tools only
---

# System Prompt Content
Your detailed system prompt defining the agent's role, capabilities, and behavior.
```

### Storage Locations

1. **Project-level**: `.claude/agents/` (highest priority)
2. **User-level**: `~/.claude/agents/`

Project-level agents take precedence over user-level ones.

## Available Tools

Sub-agents can access any of Claude Code's internal tools:
- Read, Write, Edit
- Grep, Glob, LS
- Bash
- Task (for invoking other sub-agents)
- TodoWrite
- WebFetch, WebSearch
- NotebookRead, NotebookEdit
- MCP tools from configured servers

## Best Practices

### Agent Design
- **Single Responsibility**: Each agent should have one clear purpose
- **Focused Scope**: Narrow expertise area for better performance
- **Clear Descriptions**: Include "PROACTIVELY" or "MUST BE USED" for automatic invocation
- **Tool Limitation**: Only grant necessary tools to prevent scope creep

### Workflow Optimization
- **Task Chaining**: Use multiple specialized agents for complex workflows
- **Context Preservation**: Keep main conversation focused by delegating to sub-agents
- **Version Control**: Store project sub-agents in git for team consistency

## Advanced Patterns

### Multi-Agent Orchestration
```markdown
---
name: workflow-orchestrator
description: PROACTIVELY orchestrates complex multi-agent workflows for large-scale projects
tools: [Task, TodoWrite, Read]
---

You coordinate multiple specialized agents to handle complex development tasks.
Break down large projects into specialized sub-tasks and delegate appropriately.
```

### Specialized Domain Experts
```markdown
---
name: music-notation-specialist
description: PROACTIVELY analyzes music notation, MusicXML, and MIDI processing patterns
tools: [Read, Grep, Glob]
---

You are an expert in musical notation processing, MusicXML parsing, and MIDI analysis.
Focus on music-specific algorithms and data structures.
```

## Task Tool Usage

The Task tool allows invoking sub-agents programmatically:

```python
# Invoke a specific sub-agent
Task(
    description="Analyze music notation",
    prompt="Analyze the MusicXML structure for tied notes and timing relationships",
    subagent_type="music-notation-specialist"
)
```

## Performance Considerations

### Benefits
- Prevents context pollution in main conversation
- Enables specialized expertise for complex domains
- Allows parallel task execution
- Maintains clean separation of concerns

### Trade-offs
- Slight latency when gathering context
- Need to manage multiple agent configurations
- Potential for over-fragmentation of simple tasks

## Implementation Strategy for Music Animation Project

Based on our task requirements, here's a recommended sub-agent architecture:

### 1. Analysis Specialists
```markdown
---
name: musicxml-analyzer
description: PROACTIVELY analyzes MusicXML structure, tied notes, and musical timing
tools: [Read, Grep, Glob]
---
```

```markdown
---
name: midi-pattern-analyzer
description: PROACTIVELY analyzes MIDI timing, note sequences, and audio processing patterns
tools: [Read, Grep, Glob]
---
```

### 2. Integration Coordinators
```markdown
---
name: pipeline-coordinator
description: PROACTIVELY coordinates XML-MIDI-SVG matching and synchronization workflows
tools: [Task, TodoWrite, Read, Bash]
---
```

```markdown
---
name: timing-synchronizer
description: PROACTIVELY handles tied note timing calculations and MIDI-visual matching
tools: [Read, Edit, Write, Bash]
---
```

### 3. Implementation Specialists
```markdown
---
name: json-generator
description: PROACTIVELY creates After Effects compatible JSON keyframe data
tools: [Read, Write, Edit]
---
```

```markdown
---
name: tolerance-matcher
description: PROACTIVELY handles unquantized MIDI matching with configurable tolerance
tools: [Read, Write, Edit, Bash]
---
```

## Usage Examples

### Automatic Invocation
Claude Code will automatically select appropriate sub-agents based on task context when descriptions include proactive keywords.

### Explicit Invocation
```bash
# Direct sub-agent request
"Use the musicxml-analyzer to examine the tied note structure in this score"

# Task tool invocation
Task(prompt="Analyze MIDI timing patterns", subagent_type="midi-pattern-analyzer")
```

### Workflow Orchestration
```python
# Multi-step workflow
1. musicxml-analyzer → analyze structure
2. midi-pattern-analyzer → extract timing
3. timing-synchronizer → create mappings
4. json-generator → create AE output
```

## Integration with Existing Pipeline

For our Sib2Ae project, sub-agents should:

1. **Enhance Existing Tools**: Don't replace current pipeline, add coordination layer
2. **Preserve Functionality**: Maintain backward compatibility
3. **Add Intelligence**: Use sub-agents for complex analysis and coordination
4. **Optimize Workflows**: Parallel processing where safe, coordination where needed

## Next Steps

1. Create `.claude/agents/` directory in project
2. Define specialized sub-agents for music processing tasks
3. Implement coordination patterns for complex workflows
4. Test integration with existing pipeline
5. Document team usage patterns

---

*Reference: Anthropic Claude Code Documentation - Sub-Agents (2025)*
*Last Updated: July 27, 2025*
# 16. AI Integration

## Overview
The project contains AI-assisted functionality in the CBT subsystem.

## AI Components
- cbt/ai_provider.py
- cbt/gemini_service.py

## Purpose
The AI integration is used to generate or assist with question creation. It is a service-oriented integration layer around an external LLM provider.

## Current Implementation Notes
- The project includes test coverage for the AI provider in cbt/test_ai_provider.py
- The module is wired as a support layer for the CBT question-generation workflow

## Workflow
1. Teacher/admin requests AI-assisted question generation
2. The view routes the request to the AI service layer
3. The provider constructs a prompt and sends it to the external model
4. The response is parsed and returned to the UI

## Dependencies
- Depends on the CBT question model and the exams domain
- Requires environment configuration or API credentials for production use

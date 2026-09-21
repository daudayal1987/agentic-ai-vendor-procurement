# Architecture

## Architecture Principles

1. Microservice-oriented architecture
2. Clean Architecture principles
3. Local-first development
4. Cloud-portable application design
5. AWS serverless deployment target
6. Tenant isolation
7. Infrastructure abstraction

## Initial Logical Services

- Identity / Tenant
- Document
- Retrieval
- Agent Orchestration
- Workflow / Job
- Approval
- Notification

## Important Principle

Agent != Microservice.

Specialized agents such as Contract Agent, Security Agent,
Policy Agent and Risk Agent will initially run inside the
Agent Orchestration boundary.

## Local Development

Local infrastructure will be introduced progressively
using Docker Compose.

## AWS Deployment

AWS infrastructure will be introduced after the local
application architecture is validated.
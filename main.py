# main.py - FastAPI Multi-Agent Development Orchestrator
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import asyncio
import uuid
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Development Team Orchestrator",
    description="Open-source multi-agent development workflow orchestration",
    version="1.0.0",
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API
class TaskCreate(BaseModel):
    description: str
    agent: str
    dependencies: List[str] = []
    priority: str = "medium"
    metadata: Optional[Dict[str, Any]] = {}


class TaskComplete(BaseModel):
    output: str
    artifacts: Optional[List[str]] = []
    next_agent_hint: Optional[str] = None


class WorkflowCreate(BaseModel):
    type: str
    description: str
    project_context: Optional[Dict[str, Any]] = {}


class AgentResponse(BaseModel):
    agent: str
    analysis: str
    recommendation: str
    next_steps: str
    handoff: Optional[str] = None
    artifacts: Optional[List[str]] = []


@dataclass
class Task:
    id: str
    description: str
    agent: str
    status: str  # pending, in_progress, completed, blocked
    dependencies: List[str]
    priority: str = "medium"
    output: Optional[str] = None
    artifacts: List[str] = None
    metadata: Dict[str, Any] = None
    created_at: str = datetime.now().isoformat()
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_duration: Optional[int] = None  # minutes

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AgentCapability:
    name: str
    role: str
    expertise: List[str]
    handoff_targets: List[str]
    constraints: List[str]
    tools: List[str] = None
    output_format: str = ""

    def __post_init__(self):
        if self.tools is None:
            self.tools = []


class DevelopmentOrchestrator:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.workflows: Dict[str, Dict] = {}
        self.agents = self._initialize_agents()
        self.workflow_templates = self._initialize_workflow_templates()
        self.active_sessions: Dict[str, str] = {}  # session_id -> current_task_id

    def _initialize_agents(self) -> Dict[str, AgentCapability]:
        """Initialize all development team agents with enhanced capabilities"""
        return {
            "product-manager": AgentCapability(
                name="product-manager",
                role="Product Strategy & Requirements",
                expertise=[
                    "market research",
                    "user story creation",
                    "feature prioritization",
                    "stakeholder management",
                    "acceptance criteria",
                    "roadmap planning",
                    "competitive analysis",
                    "user persona development",
                ],
                handoff_targets=["architect", "designer", "qa"],
                constraints=[
                    "no technical implementation decisions",
                    "no UI/UX specific designs",
                    "no infrastructure choices",
                ],
                tools=["user research templates", "priority matrices", "story mapping"],
                output_format="""
📋 PRODUCT ANALYSIS
Business Value: [Revenue/user impact assessment]
Market Context: [Competitive landscape, user needs]
User Stories: [As a... I want... So that...]
Acceptance Criteria: [Specific, testable requirements]
Success Metrics: [KPIs to measure success]
Priority: [High/Medium/Low with business justification]
Dependencies: [What needs to exist first]
Next Action: [Specific handoff with context]
""",
            ),
            "architect": AgentCapability(
                name="architect",
                role="System Design & Technical Strategy",
                expertise=[
                    "system architecture",
                    "scalability design",
                    "performance optimization",
                    "security architecture",
                    "technology evaluation",
                    "API design",
                    "database architecture",
                    "microservices",
                    "integration patterns",
                ],
                handoff_targets=["backend-dev", "frontend-dev", "devops", "security"],
                constraints=[
                    "no UI/UX design decisions",
                    "no business priority decisions",
                    "no specific implementation code",
                ],
                tools=[
                    "architecture diagrams",
                    "tech stack evaluation",
                    "performance modeling",
                ],
                output_format="""
🏗️ ARCHITECTURE DESIGN
System Overview: [High-level architecture diagram description]
Technology Stack: [Languages, frameworks, databases with rationale]
Scalability Strategy: [How system handles growth]
Security Architecture: [Authentication, authorization, data protection]
API Design: [REST/GraphQL structure and standards]
Data Architecture: [Database design, data flow, caching strategy]
Integration Points: [External services, third-party APIs]
Performance Considerations: [Bottlenecks, optimization strategies]
Next Action: [Specific handoff with technical context]
""",
            ),
            "frontend-dev": AgentCapability(
                name="frontend-dev",
                role="User Interface & Client-Side Development",
                expertise=[
                    "React/Vue/Angular",
                    "responsive design",
                    "CSS/Sass/Tailwind",
                    "JavaScript/TypeScript",
                    "state management",
                    "accessibility",
                    "performance optimization",
                    "browser compatibility",
                    "PWA development",
                ],
                handoff_targets=["backend-dev", "designer", "qa"],
                constraints=[
                    "no backend/server logic",
                    "no infrastructure decisions",
                    "no business requirements definition",
                ],
                tools=["component libraries", "bundlers", "testing frameworks"],
                output_format="""
🎨 FRONTEND IMPLEMENTATION
Component Architecture: [React/Vue component structure]
State Management: [Redux/Vuex/Context API strategy]
Styling Strategy: [CSS modules, Tailwind, styled-components approach]
Responsive Design: [Mobile-first, breakpoint strategy]
Accessibility: [WCAG compliance, screen reader support]
Performance: [Bundle optimization, lazy loading, caching]
Testing Approach: [Unit tests, integration tests, E2E tests]
Browser Support: [Compatibility requirements and polyfills]
Next Action: [API requirements, design clarifications needed]
""",
            ),
            "backend-dev": AgentCapability(
                name="backend-dev",
                role="Server-Side Logic & API Development",
                expertise=[
                    "Node.js/Python/Java",
                    "API development",
                    "database design",
                    "authentication/authorization",
                    "business logic",
                    "data validation",
                    "caching strategies",
                    "background jobs",
                    "third-party integrations",
                ],
                handoff_targets=["frontend-dev", "devops", "qa", "architect"],
                constraints=[
                    "no UI/frontend decisions",
                    "no product strategy decisions",
                    "no infrastructure provisioning",
                ],
                tools=["API frameworks", "database ORMs", "testing suites"],
                output_format="""
⚡ BACKEND IMPLEMENTATION
API Endpoints: [REST/GraphQL endpoint specifications]
Database Schema: [Tables, relationships, indexes, constraints]
Authentication: [JWT, OAuth, session management strategy]
Business Logic: [Core algorithms, validation rules, workflows]
Data Validation: [Input sanitization, schema validation]
Error Handling: [Exception handling, logging, monitoring]
Performance: [Query optimization, caching, rate limiting]
Security: [Input validation, SQL injection prevention, data encryption]
Next Action: [Frontend API contracts, deployment requirements]
""",
            ),
            "qa": AgentCapability(
                name="qa",
                role="Quality Assurance & Testing Strategy",
                expertise=[
                    "test planning",
                    "automated testing",
                    "manual testing",
                    "performance testing",
                    "security testing",
                    "usability testing",
                    "regression testing",
                    "test case design",
                    "bug tracking",
                ],
                handoff_targets=["frontend-dev", "backend-dev", "devops"],
                constraints=[
                    "no feature implementation",
                    "no architecture decisions",
                    "no business priority setting",
                ],
                tools=["testing frameworks", "automation tools", "performance testing"],
                output_format="""
🧪 TESTING STRATEGY
Test Plan: [Comprehensive testing approach]
Test Cases: [Detailed scenarios with expected outcomes]
Automation Strategy: [Unit, integration, E2E test automation]
Performance Tests: [Load testing, stress testing, benchmarks]
Security Tests: [Vulnerability scanning, penetration testing]
Usability Tests: [User experience validation]
Regression Tests: [Change impact validation]
Bug Tracking: [Issue identification and reporting process]
Next Action: [Implementation feedback, deployment validation]
""",
            ),
            "devops": AgentCapability(
                name="devops",
                role="Infrastructure & Deployment Operations",
                expertise=[
                    "containerization",
                    "CI/CD pipelines",
                    "cloud infrastructure",
                    "monitoring & alerting",
                    "backup & disaster recovery",
                    "security operations",
                    "performance monitoring",
                    "log management",
                ],
                handoff_targets=["backend-dev", "qa", "security"],
                constraints=[
                    "no application business logic",
                    "no feature prioritization",
                    "no UI/UX decisions",
                ],
                tools=["Docker", "Kubernetes", "CI/CD tools", "monitoring systems"],
                output_format="""
🚀 INFRASTRUCTURE & DEPLOYMENT
Containerization: [Docker strategy, image optimization]
CI/CD Pipeline: [Build, test, deploy automation]
Infrastructure: [Cloud provider, resource allocation]
Monitoring: [Application monitoring, alerting, logging]
Security: [Infrastructure security, secrets management]
Backup Strategy: [Data backup, disaster recovery plan]
Scaling: [Auto-scaling, load balancing strategy]
Cost Optimization: [Resource efficiency, cost monitoring]
Next Action: [Application deployment requirements, security validation]
""",
            ),
            "security": AgentCapability(
                name="security",
                role="Security Architecture & Compliance",
                expertise=[
                    "threat modeling",
                    "security auditing",
                    "compliance (GDPR, HIPAA)",
                    "penetration testing",
                    "vulnerability assessment",
                    "secure coding",
                    "identity management",
                    "data protection",
                    "incident response",
                ],
                handoff_targets=["backend-dev", "devops", "architect"],
                constraints=[
                    "no business feature decisions",
                    "no UI/UX implementations",
                    "no infrastructure provisioning",
                ],
                tools=["security scanners", "audit tools", "compliance frameworks"],
                output_format="""
🔒 SECURITY ANALYSIS
Threat Model: [Security risks and attack vectors]
Vulnerabilities: [Identified security weaknesses]
Compliance: [GDPR, HIPAA, SOC2 requirements]
Security Controls: [Authentication, authorization, encryption]
Data Protection: [PII handling, data classification, retention]
Incident Response: [Security breach response plan]
Audit Trail: [Logging, monitoring, forensic capabilities]
Recommendations: [Security improvements and best practices]
Next Action: [Implementation requirements, ongoing monitoring]
""",
            ),
        }

    def _initialize_workflow_templates(self) -> Dict[str, List[str]]:
        """Enhanced workflow templates for different development scenarios"""
        return {
            "new-feature": [
                "product-manager",  # Requirements & user impact
                "architect",  # Technical design & feasibility
                "security",  # Security implications
                "frontend-dev",  # UI implementation plan
                "backend-dev",  # API & business logic
                "qa",  # Testing strategy
                "devops",  # Deployment planning
            ],
            "mvp-development": [
                "product-manager",  # Core feature identification
                "architect",  # MVP architecture design
                "security",  # Essential security requirements
                "backend-dev",  # Core API development
                "frontend-dev",  # Essential UI components
                "devops",  # Basic infrastructure
                "qa",  # MVP testing strategy
            ],
            "bug-fix": [
                "qa",  # Bug reproduction & root cause
                "backend-dev",  # Server-side investigation
                "frontend-dev",  # Client-side investigation
                "security",  # Security impact assessment
                "qa",  # Fix validation
                "devops",  # Deployment coordination
            ],
            "performance-optimization": [
                "architect",  # Performance bottleneck analysis
                "backend-dev",  # Database & API optimization
                "frontend-dev",  # Client-side optimization
                "devops",  # Infrastructure optimization
                "qa",  # Performance testing validation
            ],
            "security-audit": [
                "security",  # Comprehensive security assessment
                "architect",  # Architecture security review
                "backend-dev",  # Code security analysis
                "devops",  # Infrastructure security review
                "qa",  # Security testing validation
            ],
            "refactoring": [
                "architect",  # Refactoring strategy & design
                "backend-dev",  # Server-side refactoring
                "frontend-dev",  # Client-side refactoring
                "qa",  # Regression testing
                "devops",  # Deployment impact assessment
            ],
        }

    async def create_workflow(
        self,
        workflow_type: str,
        description: str,
        project_context: Dict[str, Any] = None,
    ) -> Dict:
        """Create a new development workflow"""
        if workflow_type not in self.workflow_templates:
            raise HTTPException(
                status_code=400, detail=f"Unknown workflow type: {workflow_type}"
            )

        workflow_id = str(uuid.uuid4())
        workflow = self.workflow_templates[workflow_type]
        task_ids = []

        # Create tasks for the workflow
        for i, agent in enumerate(workflow):
            task_id = str(uuid.uuid4())
            dependencies = [task_ids[-1]] if i > 0 else []

            # Estimate duration based on agent type and complexity
            estimated_duration = self._estimate_task_duration(agent, workflow_type)

            task = Task(
                id=task_id,
                description=f"{agent}: {description}",
                agent=agent,
                status="pending",
                dependencies=dependencies,
                estimated_duration=estimated_duration,
                metadata={
                    "workflow_id": workflow_id,
                    "workflow_type": workflow_type,
                    "project_context": project_context or {},
                },
            )

            self.tasks[task_id] = task
            task_ids.append(task_id)

        # Store workflow metadata
        self.workflows[workflow_id] = {
            "id": workflow_id,
            "type": workflow_type,
            "description": description,
            "task_ids": task_ids,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "project_context": project_context or {},
        }

        logger.info(f"Created workflow {workflow_type} with {len(task_ids)} tasks")
        return {
            "workflow_id": workflow_id,
            "task_ids": task_ids,
            "next_task": asdict(self.get_next_tasks()[0])
            if self.get_next_tasks()
            else None,
        }

    def _estimate_task_duration(self, agent: str, workflow_type: str) -> int:
        """Estimate task duration in minutes based on agent and workflow complexity"""
        base_durations = {
            "product-manager": 30,
            "architect": 45,
            "frontend-dev": 60,
            "backend-dev": 60,
            "qa": 40,
            "devops": 35,
            "security": 50,
        }

        complexity_multipliers = {
            "new-feature": 1.0,
            "mvp-development": 1.5,
            "bug-fix": 0.7,
            "performance-optimization": 1.2,
            "security-audit": 1.8,
            "refactoring": 1.1,
        }

        base = base_durations.get(agent, 30)
        multiplier = complexity_multipliers.get(workflow_type, 1.0)
        return int(base * multiplier)

    def get_next_tasks(self) -> List[Task]:
        """Get tasks ready for execution"""
        ready_tasks = []

        for task in self.tasks.values():
            if task.status != "pending":
                continue

            # Check dependencies
            deps_completed = all(
                self.tasks.get(dep_id, Task("", "", "", "", "completed")).status
                == "completed"
                for dep_id in task.dependencies
            )

            if deps_completed:
                ready_tasks.append(task)

        # Sort by priority and creation time
        priority_order = {"high": 0, "medium": 1, "low": 2}
        ready_tasks.sort(
            key=lambda t: (priority_order.get(t.priority, 1), t.created_at)
        )

        return ready_tasks

    async def complete_task(
        self, task_id: str, output: str, artifacts: List[str] = None
    ) -> Dict:
        """Complete a task and advance workflow"""
        if task_id not in self.tasks:
            raise HTTPException(status_code=404, detail="Task not found")

        task = self.tasks[task_id]
        task.status = "completed"
        task.output = output
        task.completed_at = datetime.now().isoformat()
        task.artifacts = artifacts or []

        logger.info(f"Completed task {task_id} for agent {task.agent}")

        # Get next ready tasks
        next_tasks = self.get_next_tasks()

        return {
            "task_completed": True,
            "completed_task": asdict(task),
            "next_tasks": [asdict(t) for t in next_tasks],
            "workflow_progress": self._calculate_workflow_progress(
                task.metadata.get("workflow_id")
            ),
        }

    def _calculate_workflow_progress(self, workflow_id: str) -> Dict:
        """Calculate progress for a specific workflow"""
        if not workflow_id or workflow_id not in self.workflows:
            return {}

        workflow = self.workflows[workflow_id]
        task_ids = workflow["task_ids"]

        total_tasks = len(task_ids)
        completed_tasks = sum(
            1
            for task_id in task_ids
            if self.tasks.get(task_id, Task("", "", "", "", "")).status == "completed"
        )

        return {
            "workflow_id": workflow_id,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "progress_percentage": (completed_tasks / total_tasks * 100)
            if total_tasks > 0
            else 0,
        }


# Global orchestrator instance
orchestrator = DevelopmentOrchestrator()


# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "AI Development Team Orchestrator",
        "version": "1.0.0",
        "status": "active",
        "available_workflows": list(orchestrator.workflow_templates.keys()),
        "active_agents": len(orchestrator.agents),
    }


@app.post("/workflows")
async def create_workflow(workflow: WorkflowCreate):
    """Create a new development workflow"""
    result = await orchestrator.create_workflow(
        workflow.type, workflow.description, workflow.project_context
    )
    return result


@app.get("/workflows")
async def list_workflows():
    """Get all workflows"""
    return orchestrator.workflows


@app.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get specific workflow details"""
    if workflow_id not in orchestrator.workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = orchestrator.workflows[workflow_id]
    tasks = [orchestrator.tasks[task_id] for task_id in workflow["task_ids"]]

    return {
        **workflow,
        "tasks": [asdict(task) for task in tasks],
        "progress": orchestrator._calculate_workflow_progress(workflow_id),
    }


@app.get("/tasks/next")
async def get_next_tasks():
    """Get next ready tasks across all workflows"""
    ready_tasks = orchestrator.get_next_tasks()
    return [asdict(task) for task in ready_tasks]


@app.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str, completion: TaskComplete):
    """Complete a specific task"""
    result = await orchestrator.complete_task(
        task_id, completion.output, completion.artifacts
    )
    return result


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get specific task details"""
    if task_id not in orchestrator.tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    return asdict(orchestrator.tasks[task_id])


@app.get("/agents")
async def get_agents():
    """Get all available agents and their capabilities"""
    return {
        agent_name: asdict(agent) for agent_name, agent in orchestrator.agents.items()
    }


@app.get("/agents/{agent_name}")
async def get_agent(agent_name: str):
    """Get specific agent capabilities"""
    if agent_name not in orchestrator.agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    return asdict(orchestrator.agents[agent_name])


@app.post("/agents/{agent_name}/response")
async def log_agent_response(agent_name: str, response: AgentResponse):
    """Log an agent response for workflow tracking"""
    # This endpoint allows Cursor to log agent responses
    # Can be used for analytics and workflow optimization
    logger.info(f"Agent {agent_name} response logged: {response.analysis[:100]}...")
    return {"logged": True, "agent": agent_name}


@app.get("/status")
async def get_system_status():
    """Get overall system status and metrics"""
    all_tasks = list(orchestrator.tasks.values())

    total_tasks = len(all_tasks)
    completed_tasks = sum(1 for t in all_tasks if t.status == "completed")
    pending_tasks = sum(1 for t in all_tasks if t.status == "pending")
    in_progress_tasks = sum(1 for t in all_tasks if t.status == "in_progress")

    return {
        "system_status": "healthy",
        "active_workflows": len(orchestrator.workflows),
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "in_progress_tasks": in_progress_tasks,
        "progress_percentage": (completed_tasks / total_tasks * 100)
        if total_tasks > 0
        else 0,
        "next_tasks": [asdict(task) for task in orchestrator.get_next_tasks()[:3]],
    }


@app.get("/templates")
async def get_workflow_templates():
    """Get available workflow templates"""
    return {
        "templates": orchestrator.workflow_templates,
        "descriptions": {
            "new-feature": "Complete feature development from requirements to deployment",
            "mvp-development": "Minimal Viable Product development workflow",
            "bug-fix": "Bug investigation, fixing, and validation workflow",
            "performance-optimization": "System performance analysis and optimization",
            "security-audit": "Comprehensive security assessment and remediation",
            "refactoring": "Code refactoring with proper testing and validation",
        },
    }


if __name__ == "__main__":
    import uvicorn

    print("🚀 AI Development Team Orchestrator starting...")
    print("📊 Dashboard: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)

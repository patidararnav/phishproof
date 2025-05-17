from dataclasses import dataclass, field
from typing import Optional, List, Any

@dataclass
class Company:
    """Represents a target company."""
    name: str
    domain: str

@dataclass
class Employee:
    """Represents an employee within a company."""
    name: str
    role: str
    reports_to: str  # Could be an Employee ID or manager's name
    start_date: str  # e.g., "2023-01-01"
    email: str
    phone: str
    # Additional fields that might be useful from recon
    linkedin_profile_url: Optional[str] = None


@dataclass
class ReconInput:
    """Input parameters for the reconnaissance phase."""
    company_name: str
    company_domain: str
    scope: str  # e.g., "all employees", "marketing department", "executives and their direct reports"

@dataclass
class OrganizationData:
    """Aggregated data collected during reconnaissance."""
    company: Company
    employees: List[Employee] = field(default_factory=list)
    # org_chart_representation could be a dictionary, a graph, or other structured data
    org_chart_representation: Optional[Any] = None 
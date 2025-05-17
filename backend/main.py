from fastapi import FastAPI, HTTPException, Request
import httpx
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import json
from dotenv import load_dotenv
from models import Employee, EmailRequest, OrganizationData, Company  # Import the dataclass models
import mailslurp_client
import logging
from datetime import datetime
import hashlib
import base64
from typing import Dict, List
from fastapi.responses import HTMLResponse

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Store clicks with user information
click_tracker: Dict[str, List[Dict]] = {}

app = FastAPI()

def generate_tracking_link(employee: Employee, company_name: str) -> str:
    """Generate a unique tracking link for an employee"""
    # Create a unique identifier that includes employee info but is encoded
    payload = f"{employee.email}:{company_name}:{datetime.now().isoformat()}"
    encoded_payload = base64.urlsafe_b64encode(payload.encode()).decode()
    return encoded_payload

@app.get("/track/{tracking_id}")
async def track_click(tracking_id: str, request: Request):
    """Track when a link is clicked"""
    try:
        # Decode the tracking ID to get employee information
        decoded_payload = base64.urlsafe_b64decode(tracking_id.encode()).decode()
        email, company_name, timestamp = decoded_payload.split(":", 2)
        
        click_data = {
            "timestamp": datetime.now().isoformat(),
            "email": email,
            "company": company_name,
            "ip": request.client.host,
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        
        if tracking_id not in click_tracker:
            click_tracker[tracking_id] = []
        
        click_tracker[tracking_id].append(click_data)
        logger.info(f"Tracked click for email {email}: {click_data}")
        
    except Exception as e:
        logger.error(f"Error tracking click: {str(e)}")
    
    # Return a warning page
    return HTMLResponse(
        """<html><body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>⚠️ Security Test</h1>
        <p>This was a simulated phishing test. Please contact your IT department.</p>
        </body></html>"""
    )

@app.get("/api/click-stats")
async def get_click_stats():
    """Get detailed statistics about link clicks"""
    all_clicks = []
    user_clicks = {}  # Track clicks per user
    
    for tracking_id, clicks in click_tracker.items():
        for click in clicks:
            all_clicks.append(click)
            
            # Count clicks per user
            email = click["email"]
            if email not in user_clicks:
                user_clicks[email] = {
                    "count": 0,
                    "first_click": None,
                    "last_click": None,
                    "company": click["company"]
                }
            user_clicks[email]["count"] += 1
            
            click_time = datetime.fromisoformat(click["timestamp"])
            if (not user_clicks[email]["first_click"] or 
                click_time < datetime.fromisoformat(user_clicks[email]["first_click"])):
                user_clicks[email]["first_click"] = click["timestamp"]
            if (not user_clicks[email]["last_click"] or 
                click_time > datetime.fromisoformat(user_clicks[email]["last_click"])):
                user_clicks[email]["last_click"] = click["timestamp"]
    
    # Sort clicks by timestamp
    recent_clicks = sorted(
        all_clicks,
        key=lambda x: x["timestamp"],
        reverse=True
    )[:5]
    
    return {
        "total_clicks": len(all_clicks),
        "unique_users": len(user_clicks),
        "user_stats": user_clicks,
        "recent_clicks": recent_clicks
    }

async def generate_phishing_email(scope: str, employee: Employee, company_name: str) -> str:
    """Generate phishing email content using Claude API"""
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="Anthropic API key not configured")

    tracking_id = generate_tracking_link(employee, company_name)
    tracking_link = f"http://your-domain.com/track/{tracking_id}"

    prompt = f"""Generate a phishing email from security department with the following context:
    Company: {company_name}
    Target Employee: {employee.first_name} {employee.last_name}
    Role: {employee.role}
    
    The email should be an urgent request to change their password due to a security vulnerability.
    Include a sense of urgency and importance.
    The email should be professional and tailored to the employee's role.
    
    Provide the email body in HTML format with appropriate paragraphs and styling. Do not pretext it with anything
    """

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-opus-20240229",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                error_msg = f"API Error (Status {response.status_code}): {response.text}"
                print(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
            
            response_data = response.json()
            
            if "content" not in response_data or not response_data["content"]:
                raise HTTPException(status_code=500, detail="No content in API response")
                
            return response_data["content"][0]["text"].strip()

    except httpx.RequestError as e:
        error_msg = f"Request failed: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    


@app.post("/send-email")
async def send_email(request: EmailRequest):
    results = []
    
    for employee in request.data.employees:
        try:
            # Generate phishing email content
            email_content = await generate_phishing_email(
                request.scope,
                employee,
                request.data.company.name
            )
            
            results.append({
                "employee": {
                    "first_name": employee.first_name,
                    "last_name": employee.last_name,
                    "email": employee.email
                },
                "status": "success",
                "email_content": email_content
            })
            
        except Exception as e:
            results.append({
                "employee": {
                    "first_name": employee.first_name,
                    "last_name": employee.last_name,
                    "email": employee.email
                },
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "message": f"Generated content for {len(request.data.employees)} employees",
        "results": results
    }

@app.get("/test")
async def test_send_email():
    logger.info("Starting test email generation and sending process")
    
    # Create sample test data with all required fields
    test_data = EmailRequest(
        scope="test phishing simulation",
        data=OrganizationData(
            company=Company(
                name="Test Company",
                domain="testcompany.com"
            ),
            employees=[
                Employee(
                    first_name="Test",
                    last_name="User",
                    role="Software Engineer",
                    email="adel.muursepp@gmail.com",
                    reports_to="Test Manager",
                    start_date="2024-01-01",
                    phone="123-456-7890",
                    linkedin_profile_url="https://linkedin.com/in/testuser"
                )
            ]
        )
    )
    
    try:
        # Generate tracking link for the test employee
        employee = test_data.data.employees[0]
        tracking_id = generate_tracking_link(employee, test_data.data.company.name)
        tracking_link = f"http://localhost:8000/track/{tracking_id}"  # Update with your domain
        
        logger.info(f"Generated tracking link: {tracking_link}")
        
        # Get SMTP settings from environment
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        if not all([smtp_host, smtp_port, smtp_username, smtp_password]):
            raise ValueError("Missing SMTP configuration")
        
        logger.info(f"Using SMTP server: {smtp_host}:{smtp_port}")
        
        # Create email message with tracking link
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Urgent: Security Update Required"
        msg['From'] = f"IT Security <{smtp_username}>"
        msg['To'] = employee.email
        
        # Create HTML content with tracking link
        html_content = f"""
        <html>
            <body>
                <p>Dear {employee.first_name},</p>
                <p>Our security team has detected unusual activity in your account. 
                Please click the link below to verify your identity and secure your account:</p>
                <p><a href="{tracking_link}">Verify Account Security</a></p>
                <p>If you did not request this verification, please contact IT security immediately.</p>
                <p>Best regards,<br>IT Security Team</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email
        logger.info("Connecting to SMTP server...")
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            logger.info("Logging into SMTP server...")
            server.login(smtp_username, smtp_password)
            logger.info("Sending email...")
            server.send_message(msg)
            
        logger.info("Email sent successfully")
        return {
            "status": "success",
            "message": "Test email sent successfully",
            "tracking_link": tracking_link,
            "sent_to": employee.email
        }
        
    except Exception as e:
        logger.error(f"Failed to send test email: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



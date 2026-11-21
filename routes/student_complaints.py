from functools import wraps
import secrets
import uuid

from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from models.student import Student
from models.complaint import Complaint
from services.complaint_ai_service import ComplaintAIService


student_complaints_bp = Blueprint(
    "student_complaints",
    __name__,
    url_prefix="/student/complaints"
)


# ================================================================
# STUDENT ACCESS CONTROL
# ================================================================

def student_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:

            return redirect(
                url_for("auth.login_user")
            )

        if session.get("role") != "student":

            return jsonify({
                "success": False,
                "message": "Student access required."
            }), 403

        return function(*args, **kwargs)

    return decorated_function


# ================================================================
# CSRF
# ================================================================

def ensure_csrf_token():

    if "csrf_token" not in session:

        session["csrf_token"] = secrets.token_hex(32)

    return session["csrf_token"]


def validate_csrf():

    token = request.form.get(
        "csrf_token",
        ""
    )

    if not token:

        token = request.headers.get(
            "X-CSRF-Token",
            ""
        )

    session_token = session.get(
        "csrf_token",
        ""
    )

    if not token or not session_token:

        return False

    return secrets.compare_digest(
        token,
        session_token
    )


# ================================================================
# GET CURRENT STUDENT
# ================================================================

def get_current_student():

    user_id = session.get("user_id")

    if not user_id:

        return None

    return Student.get_by_user_id(
        user_id
    )


# ================================================================
# AI ASSISTANT PAGE
# ================================================================

@student_complaints_bp.route(
    "/",
    methods=["GET"]
)
@student_required
def assistant():

    student = get_current_student()

    if not student:

        return render_template(
            "errors/404.html"
        ), 404

    csrf_token = ensure_csrf_token()

    # ------------------------------------------------------------
    # Keep one AI conversation session for the current browser
    # ------------------------------------------------------------

    if "ai_session_id" not in session:

        session["ai_session_id"] = str(
            uuid.uuid4()
        )

    ai_session_id = session[
        "ai_session_id"
    ]

    conversation = Complaint.get_ai_conversation(
        student_id=student["id"],
        session_id=ai_session_id
    )

    complaints = Complaint.get_student_complaints(
        student["id"]
    )

    statistics = Complaint.get_student_statistics(
        student["id"]
    )

    return render_template(
        "student/complaints.html",
        student=student,
        csrf_token=csrf_token,
        ai_session_id=ai_session_id,
        conversation=conversation,
        complaints=complaints,
        statistics=statistics,
        categories=Complaint.CATEGORIES
    )


# ================================================================
# START NEW AI CHAT
# ================================================================

@student_complaints_bp.route(
    "/new-chat",
    methods=["POST"]
)
@student_required
def new_chat():

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403

    session["ai_session_id"] = str(
        uuid.uuid4()
    )

    return jsonify({
        "success": True,
        "message": "New AI conversation started.",
        "session_id": session[
            "ai_session_id"
        ]
    })


# ================================================================
# AI CHAT MESSAGE
# ================================================================

@student_complaints_bp.route(
    "/chat",
    methods=["POST"]
)
@student_required
def chat():

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403

    student = get_current_student()

    if not student:

        return jsonify({
            "success": False,
            "message": "Student profile not found."
        }), 404

    message = request.form.get(
        "message",
        ""
    ).strip()

    if not message:

        return jsonify({
            "success": False,
            "message": "Please enter a message."
        }), 400

    if len(message) > 2000:

        return jsonify({
            "success": False,
            "message": (
                "Message is too long. "
                "Please keep it within 2000 characters."
            )
        }), 400

    # ------------------------------------------------------------
    # AI SESSION
    # ------------------------------------------------------------

    if "ai_session_id" not in session:

        session["ai_session_id"] = str(
            uuid.uuid4()
        )

    ai_session_id = session[
        "ai_session_id"
    ]

    # ------------------------------------------------------------
    # SAVE STUDENT MESSAGE
    # ------------------------------------------------------------

    Complaint.save_ai_message(
        student_id=student["id"],
        session_id=ai_session_id,
        sender="student",
        message=message
    )

    # ------------------------------------------------------------
    # CHECK WHETHER MESSAGE LOOKS LIKE A COMPLAINT
    # ------------------------------------------------------------

    complaint_indicators = [
    "complaint",
    "problem",
    "issue",
    "not working",
    "not working properly",
    "broken",
    "repair",
    "damaged",
    "damage",
    "leak",
    "leaking",
    "leakage",
    "flood",
    "flooding",
    "water leakage",
    "water problem",
    "no water",
    "no electricity",
    "power cut",
    "wifi problem",
    "internet problem",
    "dirty",
    "cleaning problem",
    "food problem",
    "food quality",
    "security problem",
    "theft",
    "stolen",
    "danger",
    "dangerous",
    "emergency",
    "can't",
    "cannot",
    "unable",
    "malfunction",
    "maintenance"
    ]   

    lower_message = message.lower()

    is_complaint = any(
        indicator in lower_message
        for indicator in complaint_indicators
    )

    # ------------------------------------------------------------
    # GENERATE RESPONSE
    # ------------------------------------------------------------

    if is_complaint:

        analysis = ComplaintAIService.analyze_complaint(
            message
        )

        ai_response = (
            ComplaintAIService.generate_acknowledgement(
                analysis
            )
        )

        response_type = "complaint_analysis"

        analysis_data = analysis

    else:

        ai_response = (
            ComplaintAIService.generate_general_response(
                message
            )
        )

        response_type = "general"

        analysis_data = None

    # ------------------------------------------------------------
    # SAVE AI RESPONSE
    # ------------------------------------------------------------

    Complaint.save_ai_message(
        student_id=student["id"],
        session_id=ai_session_id,
        sender="assistant",
        message=ai_response
    )

    return jsonify({
        "success": True,
        "message": ai_response,
        "response_type": response_type,
        "analysis": analysis_data
    })


# ================================================================
# SUBMIT AI-ANALYZED COMPLAINT
# ================================================================

@student_complaints_bp.route(
    "/submit",
    methods=["POST"]
)
@student_required
def submit_complaint():

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403

    student = get_current_student()

    if not student:

        return jsonify({
            "success": False,
            "message": "Student profile not found."
        }), 404

    description = request.form.get(
        "description",
        ""
    ).strip()

    if not description:

        return jsonify({
            "success": False,
            "message": "Please describe your complaint."
        }), 400

    if len(description) < 5:

        return jsonify({
            "success": False,
            "message": (
                "Please provide a little more "
                "information about the issue."
            )
        }), 400

    if len(description) > 5000:

        return jsonify({
            "success": False,
            "message": (
                "Complaint description cannot "
                "exceed 5000 characters."
            )
        }), 400

    # ------------------------------------------------------------
    # AI ANALYSIS
    # ------------------------------------------------------------

    analysis = ComplaintAIService.analyze_complaint(
        description
    )

    category = analysis["category"]

    subject = analysis["subject"]

    priority = analysis["priority"]

    # ------------------------------------------------------------
    # CREATE COMPLAINT
    # ------------------------------------------------------------

    complaint_id = Complaint.create_complaint(
        student_id=student["id"],
        category=category,
        subject=subject,
        description=description,
        priority=priority,
        ai_generated=1
    )

    # ------------------------------------------------------------
    # SAVE ORIGINAL STUDENT MESSAGE
    # ------------------------------------------------------------

    Complaint.add_message(
        complaint_id=complaint_id,
        sender_type="student",
        message=description
    )

    # ------------------------------------------------------------
    # AI ACKNOWLEDGEMENT
    # ------------------------------------------------------------

    acknowledgement = (
        ComplaintAIService.generate_acknowledgement(
            analysis
        )
    )

    Complaint.add_message(
        complaint_id=complaint_id,
        sender_type="ai",
        message=acknowledgement
    )

    return jsonify({
        "success": True,
        "message": acknowledgement,
        "complaint_id": complaint_id,
        "complaint": {
            "category": category,
            "subject": subject,
            "priority": priority,
            "status": "open",
            "ai_generated": 1
        }
    })


# ================================================================
# GET STUDENT COMPLAINTS
# ================================================================

@student_complaints_bp.route(
    "/history",
    methods=["GET"]
)
@student_required
def complaint_history():

    student = get_current_student()

    if not student:

        return jsonify({
            "success": False,
            "message": "Student profile not found."
        }), 404

    complaints = Complaint.get_student_complaints(
        student["id"]
    )

    statistics = Complaint.get_student_statistics(
        student["id"]
    )

    return jsonify({
        "success": True,
        "complaints": complaints,
        "statistics": statistics
    })


# ================================================================
# GET SINGLE COMPLAINT
# ================================================================

@student_complaints_bp.route(
    "/<int:complaint_id>",
    methods=["GET"]
)
@student_required
def complaint_details(complaint_id):

    student = get_current_student()

    if not student:

        return jsonify({
            "success": False,
            "message": "Student profile not found."
        }), 404

    complaint = Complaint.get_by_id(
        complaint_id
    )

    if not complaint:

        return jsonify({
            "success": False,
            "message": "Complaint not found."
        }), 404

    # ------------------------------------------------------------
    # SECURITY:
    # A student can only see their own complaint.
    # ------------------------------------------------------------

    if int(complaint["student_id"]) != int(
        student["id"]
    ):

        return jsonify({
            "success": False,
            "message": "You are not authorized to view this complaint."
        }), 403

    messages = Complaint.get_messages(
        complaint_id
    )

    return jsonify({
        "success": True,
        "complaint": complaint,
        "messages": messages
    })


# ================================================================
# GET CURRENT AI CONVERSATION
# ================================================================

@student_complaints_bp.route(
    "/conversation",
    methods=["GET"]
)
@student_required
def conversation():

    student = get_current_student()

    if not student:

        return jsonify({
            "success": False,
            "message": "Student profile not found."
        }), 404

    if "ai_session_id" not in session:

        session["ai_session_id"] = str(
            uuid.uuid4()
        )

    ai_session_id = session[
        "ai_session_id"
    ]

    messages = Complaint.get_ai_conversation(
        student_id=student["id"],
        session_id=ai_session_id
    )

    return jsonify({
        "success": True,
        "session_id": ai_session_id,
        "messages": messages
    })


# ================================================================
# COMPLAINT CATEGORIES
# ================================================================

@student_complaints_bp.route(
    "/categories",
    methods=["GET"]
)
@student_required
def categories():

    return jsonify({
        "success": True,
        "categories": Complaint.CATEGORIES
    })


# ================================================================
# QUICK COMPLAINT ANALYSIS
# ================================================================

@student_complaints_bp.route(
    "/analyze",
    methods=["POST"]
)
@student_required
def analyze():

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403

    description = request.form.get(
        "description",
        ""
    ).strip()

    if not description:

        return jsonify({
            "success": False,
            "message": "Please enter a complaint."
        }), 400

    if len(description) > 5000:

        return jsonify({
            "success": False,
            "message": (
                "Complaint description cannot "
                "exceed 5000 characters."
            )
        }), 400

    analysis = ComplaintAIService.analyze_complaint(
        description
    )

    return jsonify({
        "success": True,
        "analysis": analysis
    })
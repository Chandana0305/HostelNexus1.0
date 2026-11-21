from flask import Flask, render_template, redirect, url_for

from config import Config

from routes.auth import auth_bp
from routes.admin_students import admin_students_bp
from routes.student_profile import student_profile_bp
from routes.admin_hostel import admin_hostel_bp
from routes.admin_allocation import admin_allocation_bp
from routes.admin_fees import admin_fees_bp
from routes.fee_documents import fee_documents_bp
from routes.student_fees import student_fees_bp
from routes.student_fee_receipts import student_fee_receipts_bp
from routes.student_complaints import student_complaints_bp
from routes.admin_complaints import admin_complaints_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_students_bp)
    app.register_blueprint(student_profile_bp)
    app.register_blueprint(admin_hostel_bp)
    app.register_blueprint(admin_allocation_bp)
    app.register_blueprint(admin_fees_bp)
    app.register_blueprint(fee_documents_bp)
    app.register_blueprint(student_fees_bp)
    app.register_blueprint(student_fee_receipts_bp)
    app.register_blueprint(student_complaints_bp)
    app.register_blueprint(admin_complaints_bp)

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains"
            )
        return response

    @app.route("/")
    def home():
        return render_template("landing.html")

    @app.route("/login")
    def login():
        return redirect(url_for("auth.login_user"))

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def request_too_large(error):
        return render_template("errors/500.html"), 413

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template("errors/500.html"), 500

    return app


app = create_app()


if __name__ == "__main__":
    # Local development only. Use a production WSGI server for deployment.
    app.run(host="127.0.0.1", port=5000, debug=False)

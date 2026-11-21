document.addEventListener("DOMContentLoaded", function () {

    /*
     * Find the login form.
     *
     * We first look for the /auth/login action.
     * If that is not available, we use the first form
     * on the page.
     */
    const loginForm =
        document.querySelector('form[action*="/auth/login"]') ||
        document.querySelector("form");

    if (!loginForm) {
        console.warn("HostelNexus: Login form not found.");
        return;
    }

    console.log("HostelNexus: Login JavaScript loaded.");

    loginForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        console.log("HostelNexus: Login form intercepted.");

        const submitButton = loginForm.querySelector(
            'button[type="submit"], input[type="submit"]'
        );

        const originalButtonText = submitButton
            ? submitButton.innerHTML
            : null;

        if (submitButton) {

            submitButton.disabled = true;

            submitButton.innerHTML = `
                <span class="button-spinner"></span>
                Signing in...
            `;
        }

        const formData = new FormData(loginForm);

        try {

            const response = await fetch(
                loginForm.getAttribute("action") ||
                "/auth/login",
                {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "application/json"
                    }
                }
            );

            const contentType =
                response.headers.get("content-type") || "";

            /*
             * Flask should return JSON.
             */
            if (!contentType.includes("application/json")) {

                console.error(
                    "Unexpected server response:",
                    contentType
                );

                throw new Error(
                    "The server returned an unexpected response."
                );
            }

            const data = await response.json();

            console.log(
                "HostelNexus: Login response:",
                data
            );

            if (data.success) {

                if (typeof showToast === "function") {

                    showToast(
                        data.message || "Login successful.",
                        "success"
                    );
                }

                /*
                 * Redirect to the dashboard returned by Flask.
                 */
                setTimeout(function () {

                    if (data.redirect) {

                        window.location.assign(
                            data.redirect
                        );

                    } else {

                        window.location.assign(
                            "/auth/admin/dashboard"
                        );
                    }

                }, 300);

                return;
            }

            /*
             * Login failed.
             */
            if (typeof showToast === "function") {

                showToast(
                    data.message || "Login failed.",
                    "error"
                );

            } else {

                alert(
                    data.message || "Login failed."
                );
            }

            restoreButton();

        } catch (error) {

            console.error(
                "HostelNexus Login Error:",
                error
            );

            if (typeof showToast === "function") {

                showToast(
                    error.message ||
                    "Unable to connect to the server.",
                    "error"
                );

            } else {

                alert(
                    error.message ||
                    "Unable to connect to the server."
                );
            }

            restoreButton();
        }


        function restoreButton() {

            if (!submitButton) {
                return;
            }

            submitButton.disabled = false;

            if (originalButtonText !== null) {
                submitButton.innerHTML =
                    originalButtonText;
            }
        }

    });

});
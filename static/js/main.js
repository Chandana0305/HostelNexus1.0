/* =========================================================
   HOSTELNEXUS - MAIN JAVASCRIPT
   Step 4C - UI Foundation
   ========================================================= */


/* =========================================================
   1. PAGE LOADER
   ========================================================= */

window.addEventListener("load", function () {
    const loader = document.getElementById("page-loader");

    if (loader) {
        loader.classList.add("hidden");

        setTimeout(function () {
            loader.style.display = "none";
        }, 400);
    }
});


/* =========================================================
   2. TOAST NOTIFICATIONS
   ========================================================= */

function showToast(message, type = "info", duration = 3500) {

    const container = document.getElementById("toast-container");

    if (!container) {
        console.warn("Toast container not found.");
        return;
    }

    const toast = document.createElement("div");

    toast.className = `toast toast-${type}`;

    let icon = "ℹ";

    if (type === "success") {
        icon = "✓";
    } else if (type === "error") {
        icon = "✕";
    } else if (type === "warning") {
        icon = "!";
    }

    toast.innerHTML = `
        <div class="toast-icon">${icon}</div>

        <div class="toast-message">
            ${message}
        </div>

        <button class="toast-close" type="button">
            &times;
        </button>
    `;

    container.appendChild(toast);

    requestAnimationFrame(function () {
        toast.classList.add("show");
    });

    const closeButton = toast.querySelector(".toast-close");

    closeButton.addEventListener("click", function () {
        removeToast(toast);
    });

    const timeout = setTimeout(function () {
        removeToast(toast);
    }, duration);

    toast.dataset.timeout = timeout;
}


function removeToast(toast) {

    if (!toast) {
        return;
    }

    toast.classList.remove("show");

    setTimeout(function () {

        if (toast.parentElement) {
            toast.parentElement.removeChild(toast);
        }

    }, 300);
}


/* =========================================================
   3. MODAL SYSTEM
   ========================================================= */

function openModal(modalId) {

    const modal = document.getElementById(modalId);

    if (!modal) {
        console.warn(`Modal "${modalId}" not found.`);
        return;
    }

    modal.classList.add("active");

    document.body.classList.add("modal-open");
}


function closeModal(modalId) {

    const modal = document.getElementById(modalId);

    if (!modal) {
        return;
    }

    modal.classList.remove("active");

    document.body.classList.remove("modal-open");
}


function closeAllModals() {

    document.querySelectorAll(".modal.active").forEach(function (modal) {
        modal.classList.remove("active");
    });

    document.body.classList.remove("modal-open");
}


/* Close modal when clicking outside */

document.addEventListener("click", function (event) {

    if (event.target.classList.contains("modal")) {
        event.target.classList.remove("active");
        document.body.classList.remove("modal-open");
    }

});


/* Close modal with ESC */

document.addEventListener("keydown", function (event) {

    if (event.key === "Escape") {
        closeAllModals();
    }

});


/* =========================================================
   4. CONFIRMATION DIALOG
   ========================================================= */

function confirmAction(message, callback) {

    const result = window.confirm(message);

    if (result && typeof callback === "function") {
        callback();
    }

    return result;
}


/* =========================================================
   5. PASSWORD VISIBILITY TOGGLE
   ========================================================= */

function togglePassword(inputId, button) {

    const input = document.getElementById(inputId);

    if (!input) {
        return;
    }

    if (input.type === "password") {

        input.type = "text";

        if (button) {
            button.textContent = "Hide";
        }

    } else {

        input.type = "password";

        if (button) {
            button.textContent = "Show";
        }
    }
}


/* =========================================================
   6. BUTTON LOADING STATE
   ========================================================= */

function setButtonLoading(button, loading = true, loadingText = "Please wait...") {

    if (!button) {
        return;
    }

    if (loading) {

        if (!button.dataset.originalText) {
            button.dataset.originalText = button.innerHTML;
        }

        button.disabled = true;

        button.classList.add("loading");

        button.innerHTML = `
            <span class="button-spinner"></span>
            <span>${loadingText}</span>
        `;

    } else {

        button.disabled = false;

        button.classList.remove("loading");

        if (button.dataset.originalText) {
            button.innerHTML = button.dataset.originalText;
        }
    }
}


/* =========================================================
   7. COPY TO CLIPBOARD
   ========================================================= */

function copyToClipboard(text, successMessage = "Copied successfully.") {

    if (!text) {
        showToast("Nothing to copy.", "warning");
        return;
    }

    if (navigator.clipboard && window.isSecureContext) {

        navigator.clipboard.writeText(text)
            .then(function () {

                showToast(successMessage, "success");

            })
            .catch(function () {

                fallbackCopy(text, successMessage);

            });

    } else {

        fallbackCopy(text, successMessage);

    }
}


function fallbackCopy(text, successMessage) {

    const textarea = document.createElement("textarea");

    textarea.value = text;

    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";

    document.body.appendChild(textarea);

    textarea.select();

    try {

        document.execCommand("copy");

        showToast(successMessage, "success");

    } catch (error) {

        showToast("Unable to copy text.", "error");

    }

    document.body.removeChild(textarea);
}


/* =========================================================
   8. SMOOTH ANCHOR SCROLLING
   ========================================================= */

document.addEventListener("click", function (event) {

    const link = event.target.closest('a[href^="#"]');

    if (!link) {
        return;
    }

    const targetId = link.getAttribute("href");

    if (!targetId || targetId === "#") {
        return;
    }

    const target = document.querySelector(targetId);

    if (!target) {
        return;
    }

    event.preventDefault();

    target.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

});


/* =========================================================
   9. GLOBAL ERROR LOGGING
   ========================================================= */

window.addEventListener("error", function (event) {

    console.error(
        "HostelNexus JavaScript Error:",
        event.message
    );

});


/* =========================================================
   HOSTELNEXUS JS READY
   ========================================================= */

console.log("HostelNexus JavaScript UI Foundation loaded successfully.");

/* =========================================================
   STEP 4C PART 2
   ADVANCED UI UTILITIES
   ========================================================= */


/* =========================================================
   10. SCROLL REVEAL ANIMATIONS
   ========================================================= */

function initScrollReveal() {

    const elements = document.querySelectorAll(".reveal");

    if (!elements.length) {
        return;
    }

    const observer = new IntersectionObserver(
        function (entries) {

            entries.forEach(function (entry) {

                if (entry.isIntersecting) {

                    entry.target.classList.add("revealed");

                    observer.unobserve(entry.target);
                }

            });

        },
        {
            threshold: 0.15
        }
    );

    elements.forEach(function (element) {
        observer.observe(element);
    });
}


/* =========================================================
   11. ANIMATED COUNTERS
   ========================================================= */

function animateCounter(element) {

    const target = parseInt(
        element.dataset.target || "0",
        10
    );

    const duration = parseInt(
        element.dataset.duration || "1500",
        10
    );

    const startTime = performance.now();


    function updateCounter(currentTime) {

        const elapsed = currentTime - startTime;

        const progress = Math.min(
            elapsed / duration,
            1
        );

        /*
         * Ease-out effect
         */
        const easedProgress =
            1 - Math.pow(1 - progress, 3);

        const currentValue = Math.floor(
            easedProgress * target
        );

        element.textContent =
            currentValue.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        } else {
            element.textContent =
                target.toLocaleString();
        }
    }


    requestAnimationFrame(updateCounter);
}


function initCounters() {

    const counters =
        document.querySelectorAll(".counter");

    if (!counters.length) {
        return;
    }

    const observer = new IntersectionObserver(
        function (entries) {

            entries.forEach(function (entry) {

                if (entry.isIntersecting) {

                    animateCounter(entry.target);

                    observer.unobserve(entry.target);
                }

            });

        },
        {
            threshold: 0.5
        }
    );


    counters.forEach(function (counter) {

        counter.textContent = "0";

        observer.observe(counter);

    });
}


/* =========================================================
   12. IMAGE PREVIEW
   ========================================================= */

function previewImage(input, previewElementId) {

    const preview =
        document.getElementById(previewElementId);

    if (!preview) {
        console.warn(
            `Image preview "${previewElementId}" not found.`
        );
        return;
    }

    if (!input.files || !input.files[0]) {
        return;
    }

    const file = input.files[0];


    /*
     * Only allow image files
     */

    if (!file.type.startsWith("image/")) {

        showToast(
            "Please select a valid image file.",
            "error"
        );

        input.value = "";

        return;
    }


    /*
     * Maximum size: 5 MB
     */

    const maxSize =
        5 * 1024 * 1024;

    if (file.size > maxSize) {

        showToast(
            "Image size must be less than 5 MB.",
            "warning"
        );

        input.value = "";

        return;
    }


    const reader =
        new FileReader();


    reader.onload = function (event) {

        preview.src =
            event.target.result;

        preview.classList.add("image-preview-visible");
    };


    reader.onerror = function () {

        showToast(
            "Unable to preview the image.",
            "error"
        );
    };


    reader.readAsDataURL(file);
}


/* =========================================================
   13. DROPDOWN SYSTEM
   ========================================================= */

function toggleDropdown(dropdownId) {

    const menu =
        document.getElementById(dropdownId);

    if (!menu) {
        console.warn(
            `Dropdown "${dropdownId}" not found.`
        );
        return;
    }

    /*
     * Find the parent .dropdown
     */

    const dropdown =
        menu.closest(".dropdown");

    if (!dropdown) {
        console.warn(
            `Parent dropdown for "${dropdownId}" not found.`
        );
        return;
    }


    /*
     * Close all other dropdowns
     */

    document.querySelectorAll(".dropdown.active")
        .forEach(function (item) {

            if (item !== dropdown) {
                item.classList.remove("active");
            }

        });


    /*
     * Toggle current dropdown
     */

    dropdown.classList.toggle("active");
}


/*
 * Close dropdown when clicking outside
 */

document.addEventListener("click", function (event) {

    const clickedDropdown =
        event.target.closest(".dropdown");

    if (clickedDropdown) {
        return;
    }

    document.querySelectorAll(".dropdown.active")
        .forEach(function (dropdown) {

            dropdown.classList.remove("active");

        });

});


/* =========================================================
   14. CONFIRMATION MODAL
   ========================================================= */

function confirmModal(
    modalId,
    message,
    callback
) {

    const modal =
        document.getElementById(modalId);

    if (!modal) {

        /*
         * Fallback to browser confirmation
         */

        confirmAction(message, callback);

        return;
    }


    const messageElement =
        modal.querySelector(
            ".confirm-message"
        );

    const confirmButton =
        modal.querySelector(
            ".confirm-action"
        );


    if (messageElement) {
        messageElement.textContent = message;
    }


    if (confirmButton) {

        /*
         * Remove previous click handlers
         * by cloning the button.
         */

        const newButton =
            confirmButton.cloneNode(true);

        confirmButton.parentNode.replaceChild(
            newButton,
            confirmButton
        );


        newButton.addEventListener(
            "click",
            function () {

                closeModal(modalId);

                if (
                    typeof callback === "function"
                ) {
                    callback();
                }

            }
        );
    }


    openModal(modalId);
}


/* =========================================================
   15. INITIALIZE UI UTILITIES
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        initScrollReveal();

        initCounters();

        console.log(
            "HostelNexus advanced UI utilities initialized."
        );

    }
);

/* =========================================================
   STEP 4C PART 3
   PRODUCTION UI HELPERS
   ========================================================= */


/* =========================================================
   16. ESCAPE HTML
   ========================================================= */

function escapeHtml(value) {

    const div = document.createElement("div");

    div.textContent = value ?? "";

    return div.innerHTML;
}


/* =========================================================
   17. SAFE TOAST
   ========================================================= */

function showSafeToast(message, type = "info", duration = 3500) {

    showToast(
        escapeHtml(message),
        type,
        duration
    );
}


/* =========================================================
   18. INPUT VALIDATION
   ========================================================= */

function setInputError(input, message) {

    if (!input) {
        return;
    }

    input.classList.add("input-error");
    input.classList.remove("input-success");

    let errorElement =
        input.parentElement.querySelector(
            ".field-error"
        );

    if (!errorElement) {

        errorElement =
            document.createElement("small");

        errorElement.className =
            "field-error";

        input.parentElement.appendChild(
            errorElement
        );
    }

    errorElement.textContent = message;
}


function clearInputError(input) {

    if (!input) {
        return;
    }

    input.classList.remove("input-error");

    const errorElement =
        input.parentElement.querySelector(
            ".field-error"
        );

    if (errorElement) {
        errorElement.remove();
    }
}


function setInputSuccess(input) {

    if (!input) {
        return;
    }

    input.classList.remove("input-error");

    input.classList.add("input-success");

    const errorElement =
        input.parentElement.querySelector(
            ".field-error"
        );

    if (errorElement) {
        errorElement.remove();
    }
}


/* =========================================================
   19. REQUIRED FIELD VALIDATION
   ========================================================= */

function validateRequired(input, fieldName = "This field") {

    if (!input) {
        return false;
    }

    const value =
        input.value.trim();

    if (!value) {

        setInputError(
            input,
            `${fieldName} is required.`
        );

        return false;
    }

    clearInputError(input);

    return true;
}


/* =========================================================
   20. EMAIL VALIDATION
   ========================================================= */

function validateEmail(input) {

    if (!input) {
        return false;
    }

    const email =
        input.value.trim();

    const emailPattern =
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailPattern.test(email)) {

        setInputError(
            input,
            "Please enter a valid email address."
        );

        return false;
    }

    setInputSuccess(input);

    return true;
}


/* =========================================================
   21. PASSWORD VALIDATION
   ========================================================= */

function validatePassword(
    input,
    minimumLength = 6
) {

    if (!input) {
        return false;
    }

    const password =
        input.value;

    if (password.length < minimumLength) {

        setInputError(
            input,
            `Password must contain at least ${minimumLength} characters.`
        );

        return false;
    }

    setInputSuccess(input);

    return true;
}


/* =========================================================
   22. CONFIRM PASSWORD
   ========================================================= */

function validatePasswordMatch(
    passwordInput,
    confirmInput
) {

    if (!passwordInput || !confirmInput) {
        return false;
    }

    if (
        passwordInput.value !==
        confirmInput.value
    ) {

        setInputError(
            confirmInput,
            "Passwords do not match."
        );

        return false;
    }

    setInputSuccess(confirmInput);

    return true;
}


/* =========================================================
   23. FORM VALIDATION
   ========================================================= */

function validateForm(form) {

    if (!form) {
        return false;
    }

    let valid = true;

    const requiredFields =
        form.querySelectorAll(
            "[required]"
        );


    requiredFields.forEach(function (input) {

        if (!input.value.trim()) {

            const label =
                input.dataset.label ||
                input.getAttribute("name") ||
                "This field";

            setInputError(
                input,
                `${label} is required.`
            );

            valid = false;

        } else {

            clearInputError(input);
        }

    });


    /*
     * Email fields
     */

    const emailFields =
        form.querySelectorAll(
            'input[type="email"]'
        );


    emailFields.forEach(function (input) {

        if (
            input.value.trim() &&
            !validateEmail(input)
        ) {
            valid = false;
        }

    });


    /*
     * Password fields
     */

    const passwordFields =
        form.querySelectorAll(
            'input[data-password-validation="true"]'
        );


    passwordFields.forEach(function (input) {

        if (
            input.value &&
            !validatePassword(input)
        ) {
            valid = false;
        }

    });


    /*
     * Confirm password
     */

    const confirmPassword =
        form.querySelector(
            '[data-confirm-password]'
        );


    if (confirmPassword) {

        const passwordInput =
            form.querySelector(
                '[data-confirm-password-target]'
            );

        if (
            passwordInput &&
            !validatePasswordMatch(
                passwordInput,
                confirmPassword
            )
        ) {
            valid = false;
        }
    }


    /*
     * Scroll to first error
     */

    if (!valid) {

        const firstError =
            form.querySelector(
                ".input-error"
            );

        if (firstError) {

            firstError.scrollIntoView({
                behavior: "smooth",
                block: "center"
            });

            firstError.focus();
        }

        showToast(
            "Please correct the highlighted fields.",
            "error"
        );
    }

    return valid;
}


/* =========================================================
   24. FORM SUBMIT LOADING
   ========================================================= */

function setFormLoading(
    form,
    loading = true,
    loadingText = "Processing..."
) {

    if (!form) {
        return;
    }

    const submitButton =
        form.querySelector(
            'button[type="submit"], input[type="submit"]'
        );

    if (!submitButton) {
        return;
    }

    if (loading) {

        if (!submitButton.dataset.originalText) {

            submitButton.dataset.originalText =
                submitButton.innerHTML;
        }

        submitButton.disabled = true;

        submitButton.classList.add(
            "loading"
        );

        if (
            submitButton.tagName === "BUTTON"
        ) {

            submitButton.innerHTML = `
                <span class="button-spinner"></span>
                <span>${loadingText}</span>
            `;
        }

    } else {

        submitButton.disabled = false;

        submitButton.classList.remove(
            "loading"
        );

        if (
            submitButton.dataset.originalText
        ) {

            submitButton.innerHTML =
                submitButton.dataset.originalText;
        }
    }
}


/* =========================================================
   25. CONFIRM DELETE
   ========================================================= */

function confirmDelete(
    itemName,
    callback
) {

    const message =
        `Are you sure you want to delete ${itemName}? This action cannot be undone.`;

    return confirmAction(
        message,
        callback
    );
}


/* =========================================================
   26. CURRENT YEAR
   ========================================================= */

function setCurrentYear() {

    const yearElements =
        document.querySelectorAll(
            ".current-year"
        );

    const year =
        new Date().getFullYear();

    yearElements.forEach(function (element) {
        element.textContent = year;
    });
}


/* =========================================================
   27. CLEAR FORM ERRORS
   ========================================================= */

function clearFormErrors(form) {

    if (!form) {
        return;
    }

    form.querySelectorAll(
        ".input-error, .input-success"
    ).forEach(function (input) {

        input.classList.remove(
            "input-error",
            "input-success"
        );

    });


    form.querySelectorAll(
        ".field-error"
    ).forEach(function (error) {

        error.remove();

    });
}


/* =========================================================
   28. FINAL UI INITIALIZATION
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        setCurrentYear();

        console.log(
            "HostelNexus production UI helpers initialized."
        );

    }
);
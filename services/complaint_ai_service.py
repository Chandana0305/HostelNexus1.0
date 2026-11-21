import re


class ComplaintAIService:

    # ============================================================
    # CATEGORY KEYWORDS
    # ============================================================

    CATEGORY_KEYWORDS = {

        "Electrical": [
            "light",
            "bulb",
            "fan",
            "switch",
            "socket",
            "electricity",
            "power",
            "current",
            "charging",
            "wire",
            "wiring",
            "tube light",
            "plug"
        ],

        "Water & Plumbing": [
            "water",
            "tap",
            "pipe",
            "plumbing",
            "leak",
            "leaking",
            "leakage",
            "bathroom water",
            "washroom water",
            "flush",
            "drain",
            "drainage",
            "shower"
        ],

        "Room Maintenance": [
            "room",
            "wall",
            "ceiling",
            "door",
            "window",
            "lock",
            "paint",
            "maintenance",
            "repair",
            "damaged",
            "broken"
        ],

        "Cleaning": [
            "clean",
            "cleaning",
            "dirty",
            "dust",
            "garbage",
            "waste",
            "smell",
            "toilet",
            "washroom",
            "bathroom",
            "hygiene"
        ],

        "Mess & Food": [
            "mess",
            "food",
            "breakfast",
            "lunch",
            "dinner",
            "rice",
            "sambar",
            "curry",
            "meal",
            "quality",
            "menu",
            "plate",
            "food quality"
        ],

        "Internet & Wi-Fi": [
            "wifi",
            "wi-fi",
            "internet",
            "network",
            "connection",
            "connectivity",
            "router",
            "slow internet",
            "no internet"
        ],

        "Furniture": [
            "bed",
            "chair",
            "table",
            "desk",
            "mattress",
            "cupboard",
            "wardrobe",
            "furniture",
            "shelf"
        ],

        "Security": [
            "security",
            "guard",
            "gate",
            "unauthorized",
            "stranger",
            "theft",
            "stolen",
            "safety",
            "visitor",
            "entry"
        ],

        "Hostel Facilities": [
            "facility",
            "facilities",
            "common room",
            "gym",
            "laundry",
            "parking",
            "water cooler",
            "recreation"
        ]
    }


    # ============================================================
    # PRIORITY KEYWORDS
    # ============================================================

    URGENT_KEYWORDS = [
        "fire",
        "smoke",
        "electric shock",
        "shock",
        "short circuit",
        "gas leak",
        "danger",
        "dangerous",
        "emergency",
        "threat",
        "break in",
        "break-in",
        "violence",
        "fight",
        "injury",
        "injured"
    ]

    HIGH_PRIORITY_KEYWORDS = [
        "no water",
        "no electricity",
        "power cut",
        "major leak",
        "flood",
        "severe",
        "broken door",
        "broken lock",
        "security issue",
        "theft",
        "stolen",
        "cannot use",
        "can't use"
    ]


    # ============================================================
    # TEXT NORMALIZATION
    # ============================================================

    @staticmethod
    def normalize_text(text):

        if not text:
            return ""

        text = text.lower().strip()

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text


    # ============================================================
    # CATEGORY DETECTION
    # ============================================================

    @classmethod
    def detect_category(cls, text):

        text = cls.normalize_text(text)

        scores = {}

        for category, keywords in cls.CATEGORY_KEYWORDS.items():

            score = 0

            for keyword in keywords:

                keyword = keyword.lower()

                if keyword in text:

                    # Exact phrase matches get slightly higher
                    # importance.

                    if " " in keyword:

                        score += 3

                    else:

                        score += 1

            scores[category] = score


        if not scores:

            return "Other"


        best_category = max(
            scores,
            key=scores.get
        )

        if scores[best_category] == 0:

            return "Other"

        return best_category


    # ============================================================
    # PRIORITY DETECTION
    # ============================================================

    @classmethod
    def detect_priority(cls, text):

        text = cls.normalize_text(text)


        # Emergency / safety related issues

        for keyword in cls.URGENT_KEYWORDS:

            if keyword in text:

                return "urgent"


        # High impact hostel issues

        for keyword in cls.HIGH_PRIORITY_KEYWORDS:

            if keyword in text:

                return "high"


        # Medium is the normal default

        return "medium"


    # ============================================================
    # SUBJECT GENERATION
    # ============================================================

    @classmethod
    def generate_subject(
        cls,
        text,
        category
    ):

        text = cls.normalize_text(text)

        subject_map = {

            "Electrical":
                "Electrical maintenance issue",

            "Water & Plumbing":
                "Water or plumbing issue",

            "Room Maintenance":
                "Room maintenance issue",

            "Cleaning":
                "Hostel cleaning issue",

            "Mess & Food":
                "Mess and food related issue",

            "Internet & Wi-Fi":
                "Internet / Wi-Fi issue",

            "Furniture":
                "Furniture maintenance issue",

            "Security":
                "Hostel security issue",

            "Hostel Facilities":
                "Hostel facility issue",

            "Other":
                "Hostel support request"
        }


        # More specific subjects

        if "fan" in text:

            return "Room fan issue"

        if "light" in text or "bulb" in text:

            return "Room lighting issue"

        if "water" in text and (
            "no water" in text
            or "not coming" in text
        ):

            return "No water supply"

        if "leak" in text or "leaking" in text:

            return "Water leakage issue"

        if "wifi" in text or "wi-fi" in text:

            return "Wi-Fi connectivity issue"

        if "internet" in text:

            return "Internet connectivity issue"

        if "food" in text:

            return "Food quality issue"

        if "mess" in text:

            return "Mess related issue"

        if "bed" in text:

            return "Bed / mattress issue"

        if "chair" in text:

            return "Chair issue"

        if "table" in text:

            return "Table issue"

        if "clean" in text or "dirty" in text:

            return "Hostel cleaning issue"

        if "security" in text:

            return "Hostel security issue"

        if "theft" in text or "stolen" in text:

            return "Security / theft complaint"


        return subject_map.get(
            category,
            "Hostel support request"
        )


    # ============================================================
    # COMPLETE COMPLAINT ANALYSIS
    # ============================================================

    @classmethod
    def analyze_complaint(cls, text):

        if not text:

            return {
                "category": "Other",
                "subject": "Hostel support request",
                "priority": "medium",
                "confidence": 0
            }


        category = cls.detect_category(text)

        priority = cls.detect_priority(text)

        subject = cls.generate_subject(
            text,
            category
        )


        # Calculate a simple confidence indicator
        # based on keyword evidence.

        normalized = cls.normalize_text(text)

        matched_keywords = []

        category_keywords = cls.CATEGORY_KEYWORDS.get(
            category,
            []
        )

        for keyword in category_keywords:

            if keyword.lower() in normalized:

                matched_keywords.append(
                    keyword
                )


        if category == "Other":

            confidence = 35

        elif len(matched_keywords) >= 3:

            confidence = 95

        elif len(matched_keywords) == 2:

            confidence = 85

        else:

            confidence = 75


        return {
            "category": category,
            "subject": subject,
            "priority": priority,
            "confidence": confidence,
            "matched_keywords": matched_keywords
        }


    # ============================================================
    # AI ACKNOWLEDGEMENT
    # ============================================================

    @classmethod
    def generate_acknowledgement(
        cls,
        analysis
    ):

        category = analysis.get(
            "category",
            "Other"
        )

        subject = analysis.get(
            "subject",
            "Hostel support request"
        )

        priority = analysis.get(
            "priority",
            "medium"
        )


        priority_messages = {

            "urgent":
                "This has been marked as an urgent issue because it may require immediate attention.",

            "high":
                "This has been marked as a high-priority issue so it can receive prompt attention.",

            "medium":
                "This has been recorded as a medium-priority issue.",

            "low":
                "This has been recorded as a low-priority issue."
        }


        priority_message = priority_messages.get(
            priority,
            priority_messages["medium"]
        )


        return (
            "Thank you for reporting this issue. "
            f"I have identified it as a {category} complaint "
            f"with the subject '{subject}'. "
            f"{priority_message} "
            "Your complaint has been recorded in HostelNexus. "
            "The hostel administrator can review and handle "
            "the issue from the complaint management panel. "
            "You can track the complaint status from your "
            "complaint history."
        )


    # ============================================================
    # GENERAL HOSTEL ASSISTANT RESPONSE
    # ============================================================

    @classmethod
    def generate_general_response(
        cls,
        message
    ):

        text = cls.normalize_text(message)


        # Greetings

        greetings = [
            "hi",
            "hello",
            "hey",
            "good morning",
            "good afternoon",
            "good evening"
        ]

        if any(
            greeting in text
            for greeting in greetings
        ):

            return (
                "Hello! 👋 I am the HostelNexus AI Assistant. "
                "I can help you report hostel issues, understand "
                "complaint categories, and guide you through "
                "the hostel support process. "
                "How can I help you today?"
            )


        # Complaint guidance

        if (
            "how to complain" in text
            or "how can i complain" in text
            or "register complaint" in text
            or "raise complaint" in text
        ):

            return (
                "You can report a hostel issue directly through "
                "the complaint section. Describe the problem clearly "
                "and HostelNexus AI will analyse the complaint, "
                "identify a category, estimate its priority, and "
                "create the complaint record for administrator review."
            )


        # Complaint status

        if (
            "complaint status" in text
            or "status of my complaint" in text
            or "my complaint" in text
        ):

            return (
                "You can check your submitted complaints in the "
                "Complaint History section. Each complaint can "
                "show its category, priority, current status, "
                "and administrator responses."
            )


        # Fee related

        if (
            "fee" in text
            or "fees" in text
            or "payment" in text
        ):

            return (
                "For hostel fee and payment information, please "
                "open the My Fees section of your Student Dashboard. "
                "You can view your fee summary, payment history, "
                "and available receipts there."
            )


        # Room related

        if (
            "room" in text
            or "roommate" in text
            or "allocation" in text
        ):

            return (
                "For your hostel room and allocation information, "
                "please check the hostel or room section available "
                "from your Student Dashboard."
            )


        # Mess

        if (
            "mess menu" in text
            or "food menu" in text
            or "today food" in text
        ):

            return (
                "You can check the hostel mess menu from the "
                "Mess section when the current menu has been "
                "published by the administrator."
            )


        # Leave

        if (
            "leave" in text
            or "leave request" in text
        ):

            return (
                "Leave requests can be submitted through the "
                "Leave section of HostelNexus. You can also "
                "track the status of submitted requests there."
            )


        # Default response

        return (
            "I can help you with HostelNexus hostel support. "
            "You can describe a hostel problem, ask about "
            "complaints, fees, room allocation, mess, leave "
            "requests, or other available hostel services."
        )
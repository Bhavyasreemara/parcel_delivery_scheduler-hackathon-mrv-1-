# from flask import Flask, render_template, request
# import heapq

# app = Flask(__name__)


# # ---------------------------------------------------
# # PARCEL PRIORITY CALCULATION
# # ---------------------------------------------------

# def calculate_priority(urgency, distance, deadline):
#     """
#     Higher priority means the parcel should be delivered earlier.

#     Factors:
#     - Urgency: higher urgency increases priority
#     - Distance: shorter distance increases priority
#     - Deadline: earlier deadline increases priority
#     """

#     # Convert deadline to a number
#     deadline = int(deadline)

#     # Higher urgency = higher priority
#     urgency_score = urgency * 50

#     # Shorter distance = higher priority
#     distance_score = max(0, 100 - distance)

#     # Earlier deadline = higher priority
#     deadline_score = max(0, 100 - deadline)

#     total_priority = (
#         urgency_score
#         + distance_score
#         + deadline_score
#     )

#     return total_priority


# # ---------------------------------------------------
# # SCHEDULING ALGORITHM
# # ---------------------------------------------------

# def schedule_parcels(parcels):

#     priority_queue = []

#     for parcel in parcels:

#         priority = calculate_priority(
#             parcel["urgency"],
#             parcel["distance"],
#             parcel["deadline"]
#         )

#         parcel["priority"] = priority

#         # Negative priority because Python heapq
#         # is a min-heap.
#         heapq.heappush(
#             priority_queue,
#             (-priority, parcel["id"], parcel)
#         )

#     scheduled_parcels = []

#     while priority_queue:

#         _, _, parcel = heapq.heappop(priority_queue)

#         scheduled_parcels.append(parcel)

#     return scheduled_parcels


# # ---------------------------------------------------
# # HOME PAGE
# # ---------------------------------------------------

# @app.route("/")
# def index():

#     return render_template(
#         "index.html",
#         parcels=[]
#     )


# # ---------------------------------------------------
# # ADD AND SCHEDULE PARCELS
# # ---------------------------------------------------

# @app.route("/schedule", methods=["POST"])
# def schedule():

#     parcel_ids = request.form.getlist("parcel_id")
#     urgencies = request.form.getlist("urgency")
#     distances = request.form.getlist("distance")
#     deadlines = request.form.getlist("deadline")

#     parcels = []

#     for i in range(len(parcel_ids)):

#         parcel = {
#             "id": parcel_ids[i],
#             "urgency": int(urgencies[i]),
#             "distance": float(distances[i]),
#             "deadline": int(deadlines[i])
#         }

#         parcels.append(parcel)

#     scheduled_parcels = schedule_parcels(parcels)

#     return render_template(
#         "result.html",
#         parcels=scheduled_parcels
#     )


# # ---------------------------------------------------
# # RUN FLASK SERVER
# # ---------------------------------------------------

# if __name__ == "__main__":
#     app.run(debug=True)

from flask import Flask, render_template, request
import heapq

app = Flask(__name__)

# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------

# A parcel is considered critical when its deadline
# is this many hours or less.
CRITICAL_DEADLINE = 2


# ---------------------------------------------------------
# WEIGHTED PRIORITY SCORE
# ---------------------------------------------------------

def calculate_priority(urgency, distance, deadline):
    """
    Calculates the normal weighted priority score.

    Higher urgency       -> higher priority
    Shorter distance     -> higher priority
    Closer deadline      -> higher priority
    """

    urgency_score = urgency * 50

    # Shorter distance gets a higher score
    distance_score = max(0, 100 - distance)

    # Smaller remaining deadline gets a higher score
    deadline_score = max(0, 100 - deadline)

    total_priority = (
        urgency_score
        + distance_score
        + deadline_score
    )

    return total_priority


# ---------------------------------------------------------
# DYNAMIC SCHEDULER
# ---------------------------------------------------------

def schedule_parcels(parcels):

    remaining_parcels = parcels.copy()
    scheduled_parcels = []

    while remaining_parcels:

        # -------------------------------------------------
        # STEP 1: Find currently critical parcels
        # -------------------------------------------------

        critical_parcels = [
            parcel
            for parcel in remaining_parcels
            if parcel["deadline"] <= CRITICAL_DEADLINE
        ]

        # -------------------------------------------------
        # RULE 1: EMERGENCY DEADLINE RULE
        # -------------------------------------------------

        if critical_parcels:

            # Deadline is the most important factor now.
            #
            # The parcel with the least remaining time
            # is selected first.
            #
            # If deadlines are equal:
            #   1. Higher urgency wins
            #   2. Shorter distance wins

            selected_parcel = min(
                critical_parcels,
                key=lambda parcel: (
                    parcel["deadline"],
                    -parcel["urgency"],
                    parcel["distance"]
                )
            )

            selected_parcel["rule_used"] = (
                "Emergency Deadline Rule"
            )

            selected_parcel["priority"] = calculate_priority(
                selected_parcel["urgency"],
                selected_parcel["distance"],
                selected_parcel["deadline"]
            )

        # -------------------------------------------------
        # RULE 2: WEIGHTED PRIORITY RULE
        # -------------------------------------------------

        else:

            # No parcel is critically close to its deadline.
            #
            # Therefore, compare:
            #   Urgency + Distance + Deadline

            priority_queue = []

            for parcel in remaining_parcels:

                priority = calculate_priority(
                    parcel["urgency"],
                    parcel["distance"],
                    parcel["deadline"]
                )

                parcel["priority"] = priority
                parcel["rule_used"] = (
                    "Weighted Priority Rule"
                )

                # Python heapq is a MIN heap.
                # Negative priority makes it behave
                # like a MAX priority queue.

                heapq.heappush(
                    priority_queue,
                    (
                        -priority,
                        parcel["id"],
                        parcel
                    )
                )

            _, _, selected_parcel = heapq.heappop(
                priority_queue
            )

        # -------------------------------------------------
        # ADD SELECTED PARCEL TO FINAL SCHEDULE
        # -------------------------------------------------

        scheduled_parcels.append(selected_parcel)

        # Remove selected parcel from remaining parcels
        remaining_parcels.remove(selected_parcel)

    return scheduled_parcels


# ---------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------------------------------------------------
# SCHEDULE ROUTE
# ---------------------------------------------------------

@app.route("/schedule", methods=["POST"])
def schedule():

    parcel_ids = request.form.getlist("parcel_id")
    urgencies = request.form.getlist("urgency")
    distances = request.form.getlist("distance")
    deadlines = request.form.getlist("deadline")

    parcels = []

    for i in range(len(parcel_ids)):

        # Ignore completely empty rows
        if not parcel_ids[i].strip():
            continue

        urgency = int(urgencies[i])
        distance = float(distances[i])
        deadline = float(deadlines[i])

        parcel = {
            "id": parcel_ids[i].strip(),
            "urgency": urgency,
            "distance": distance,
            "deadline": deadline
        }

        parcels.append(parcel)

    # Make sure at least one parcel exists
    if not parcels:
        return "Please enter at least one parcel."

    # Schedule parcels using the dynamic rules
    scheduled_parcels = schedule_parcels(parcels)

    return render_template(
        "result.html",
        parcels=scheduled_parcels,
        critical_deadline=CRITICAL_DEADLINE
    )


# ---------------------------------------------------------
# RUN APPLICATION
# ---------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)


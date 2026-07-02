from ...models.task import ToolSchema

SEARCH_FLIGHTS = ToolSchema(
    name="search_flights",
    description="Search available flights between two airports.",
    input_schema={
        "type": "object",
        "properties": {
            "origin": {"type": "string", "description": "Origin airport code, e.g. SFO"},
            "dest": {"type": "string", "description": "Destination airport code, e.g. JFK"},
        },
        "required": ["origin", "dest"],
    },
)

BOOK_FLIGHT = ToolSchema(
    name="book_flight",
    description="Book a specific flight for a passenger. For bookings over $500/ticket, you "
    "must first call request_budget_exception for that flight.",
    input_schema={
        "type": "object",
        "properties": {
            "flight_id": {"type": "string"},
            "passenger_name": {"type": "string"},
        },
        "required": ["flight_id", "passenger_name"],
    },
)

REQUEST_BUDGET_EXCEPTION = ToolSchema(
    name="request_budget_exception",
    description="Request an exception to book a flight over the $500/ticket budget policy.",
    input_schema={
        "type": "object",
        "properties": {
            "flight_id": {"type": "string"},
            "justification": {"type": "string"},
        },
        "required": ["flight_id", "justification"],
    },
)

ALL_TOOLS = [SEARCH_FLIGHTS, BOOK_FLIGHT, REQUEST_BUDGET_EXCEPTION]

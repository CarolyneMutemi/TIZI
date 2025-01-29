from fastapi import Request
def get_ussd_steps(request: Request):
    """
    Outline USSD steps.
    """
    session_id = request.query_params.get("sessionId")
    service_code = request.query_params.get("serviceCode")
    phone_number = request.query_params.get("phoneNumber")
    text = request.query_params.get("text", "default")

    groups = get_groups()
    group_events

    if text == "":
        response = "CON Heyah! Welcome to TIZI. Choose a group below to explore their events. \n"
        


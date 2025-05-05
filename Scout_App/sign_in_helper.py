# TODO: add TRY/CATCH for call to api?
import logging

logger = logging.getLogger(__name__)


def get_display_name(request):
    # Get user's display name for the navbar
    display_name = None
    try:
        user = request.session.get("user")
        if user:
            userinfo = user.get("userinfo", {})
            display_name = userinfo.get("name")
            # If the user's display name is their email, strip the domain
            display_name = display_name.split("@")[0] if display_name and "@" in display_name else display_name
            # Follow the same logic for users without display names
            if not display_name:
                email = userinfo.get("email", "")
                display_name = email.split("@")[0] if "@" in email else email
    except (AttributeError, TypeError) as e:
        logger.warning(f"error retrieving display name: {e}")
        display_name = None
    return display_name

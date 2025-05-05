import base64
import json
from django.shortcuts import render
# inference for Roboflow model
from inference_sdk import InferenceHTTPClient
from .forms import ImageUploadForm
from .sign_in_helper import get_display_name
from .validate_roboflow_reponse import validate_api_response
# imports below are for auth0
from authlib.integrations.django_client import OAuth
from django.conf import settings
from django.urls import reverse
from urllib.parse import quote_plus, urlencode

from functools import wraps
from django.shortcuts import redirect
import os

oauth = OAuth()

oauth.register(
    "auth0",
    client_id=settings.AUTH0_CLIENT_ID,
    client_secret=settings.AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration",
)


# login decoder to check if the current user is logged in, called by upload and account pages
def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.session.get("user"):
            return redirect(reverse("login"))
        return view_func(request, *args, **kwargs)

    return wrapped_view


# Pages for auth0
def login(request):
    redirect_uri = request.build_absolute_uri(reverse("callback"))
    response = oauth.auth0.authorize_redirect(request, redirect_uri)

    return response


def callback(request):
    token = oauth.auth0.authorize_access_token(request)
    request.session["user"] = token
    return redirect(request.build_absolute_uri(reverse("index")))


def logout(request):
    request.session.clear()

    return redirect(
        f"https://{settings.AUTH0_DOMAIN}/v2/logout?"
        + urlencode(
            {
                "returnTo": request.build_absolute_uri(reverse("index")),
                "client_id": settings.AUTH0_CLIENT_ID,
            },
            quote_via=quote_plus,
        ),
    )


def index(request):
    # var to hold display name, created to trim display names that are same as email
    display_name = get_display_name(request)

    return render(
        request,
        "index.html",

        context={
            "session": request.session.get("user"),
            "pretty": json.dumps(request.session.get("user"), indent=4),
            "display_name": display_name
        },
    )


def about(request):
    # get user's display name for nav bar
    display_name = get_display_name(request)

    return render(
        request,
        "about.html",

        context={
            "session": request.session.get("user"),
            "display_name": display_name,
        },
    )


@login_required
def account_page(request):
    # var to hold display name, created to trim display names that are same as email
    display_name = get_display_name(request)
    email_verify = None
    last_update = None
    user_email = None

    user = request.session.get("user")
    if user:
        userinfo = user.get("userinfo", {})
        user_email = userinfo.get("email")
        # get email verification status
        email_verify = userinfo.get("email_verified")
        last_update = userinfo.get("updated_at")

    return render(
        request,
        "account.html",

        context={
            "session": request.session.get("user"),
            "pretty": json.dumps(request.session.get("user"), indent=4),
            "display_name": display_name,
            "user_email": user_email,
            "email_verify": email_verify,
            "last_update": last_update,
        },
    )


# get vars for calling the api from roboflow
client = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    # TODO: remove hard coded values before deployment
    api_key=os.environ.get('key', None))


# if the user is signed in, allow them to upload a file, send it to Roboflow for inference,
# then parse and display the returned inference results.
@login_required
def upload_image(request):
    # values to store result from api and the extracted formation
    result = None
    formation_class = None
    confidence = None
    img_base64 = None
    response_error = None

    # get user's display name for nav bar
    display_name = get_display_name(request)

    if request.method == 'POST' and request.FILES.get('image'):

        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = request.FILES['image']

            # Convert image to Base64 string to send to api
            image_base64 = base64.b64encode(image.read()).decode('utf-8')
            # TODO: limit file upload size. CHECK DIFFERENCE IN VERSIONS FROM HEROKU ROLLBACK

            try:
                # Call Roboflow API
                api_response = client.run_workflow(
                    # TODO: remove hard coded values before deployment
                    workspace_name=os.environ.get('workspace_name', None),
                    workflow_id=os.environ.get('workflow_id2', None),

                    images={"image": f"data:image/jpeg;base64,{image_base64}"},
                    use_cache=True
                )

                # validate Roboflow API response
                valid_response = validate_api_response(api_response)
                if not valid_response:
                    response_error = True

                if valid_response:

                    # get data for potentially displaying on page
                    result = json.dumps(api_response, indent=2)

                    # extract specific data like the image and formation prediction from the JSON
                    data = api_response
                    first_result = data[0]

                    # get the predicted class data from the json
                    prediction_data = first_result.get("predictions")
                    # if it is a string parse it
                    if isinstance(prediction_data, str):
                        prediction_data = json.loads(prediction_data)

                    predictions_list = prediction_data.get("predictions", [])  # Get list of predictions
                    # if there is no class/formation found in the image, prediction will be empty
                    if not predictions_list:
                        formation_class = "None"
                    else:
                        # get the predicted class and confidence
                        formation_class = predictions_list[0].get("class")
                        confidence = predictions_list[0].get("confidence")
                        # make confidence a percentage
                        confidence = confidence * 100
                        confidence = (str(confidence)[:4])

                    img_base64 = first_result.get("output_image")

            except Exception as e:
                result = f"API request unsuccessful: {str(e)}"

    else:
        form = ImageUploadForm()

    return render(request, 'uploads2.html', {
        'form': form, 'result': result, 'formation_class': formation_class, 'image': img_base64,
        'display_name': display_name, 'session': request.session.get("user"), 'confidence': confidence,
        'response_error': response_error,
    })


# Views for each formation info page

def formations(request):
    # get user's display name for the nav bar
    display_name = get_display_name(request)

    return render(
        request, "formations.html",
        context={
            "session": request.session.get("user"),
            "display_name": display_name,
        },
    )


def pistol(request):
    # get user's display name for nav bar
    display_name = get_display_name(request)

    return render(
        request, "formations/pistol.html",
        context={
            "session": request.session.get("user"),
            "display_name": display_name,
        },
    )


def empty(request):
    # get user's display name for nav bar
    display_name = get_display_name(request)

    return render(
        request, "formations/empty.html",
        context={
            "session": request.session.get("user"),
            "display_name": display_name,
        },
    )


def i(request):
    # get user's display name for nav bar
    display_name = get_display_name(request)

    return render(
        request, "formations/i.html",
        context={
            "session": request.session.get("user"),
            "display_name": display_name,
        },
    )


def shotgun(request):
    # get user's display name for nav bar
    display_name = get_display_name(request)

    return render(
        request, "formations/shotgun.html",
        context={
            "session": request.session.get("user"),
            "display_name": display_name,
        },
    )


def singleback(request):
    # get user's display name for nav bar
    display_name = get_display_name(request)

    return render(
        request, "formations/singleback.html",
        context={
            "session": request.session.get("user"),
            "display_name": display_name,
        },
    )

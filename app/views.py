import gspread
from oauth2client.service_account import ServiceAccountCredentials
from .models import Shopify_data_model, Shopify_product_model
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.http import HttpResponse, JsonResponse
from . models import *
import requests
from datetime import datetime
from django.utils import timezone
from google_auth_oauthlib.flow import Flow
import csv
import pytz
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

CLIENT_CONFIG = {
    'web': {
        "client_id": "512212752155-oq6l5a9cql3jnha6227uibhjhm3si4l6.apps.googleusercontent.com",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_secret": "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",
        "redirect_uris": ["http://127.0.0.1:8000", "http://127.0.0.1:8000/accounts/google/login/callback/"],
    }
}

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def google_spreadsheet(request):
    try:
        if 'credentials' not in request.session:
            return redirect('google_authenticate')

        # Ensure include_granted_scopes is set correctly
        oauth_state = request.session.get('oauth_state', '')
        credentials = Flow.from_client_config(
            CLIENT_CONFIG,
            scopes=SCOPES,
            state=oauth_state,
            include_granted_scopes='true'  # Ensure it's a string
        ).fetch_token(authorization_response=request.build_absolute_uri())

        # Build the Google Sheets service
        service = build('sheets', 'v4', credentials=credentials)

        # Create a new spreadsheet
        spreadsheet = service.spreadsheets().create(
            body={'properties': {'title': 'New Spreadsheet'}}).execute()

        spreadsheet_id = spreadsheet['spreadsheetId']

        return JsonResponse({'spreadsheet_id': spreadsheet_id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def google_authenticate(request):
    redirect_uri = request.build_absolute_uri('google_auth_callback')
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=redirect_uri,
        state='',
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes=True,
    )
    request.session['oauth_state'] = state
    return redirect(authorization_url)


def google_auth_callback(request):
    try:
        code = request.GET.get('code')
        if not code:
            return JsonResponse({'error': 'Authorization code not found'}, status=400)

        token_params = {
            'code': code,
            'client_id': CLIENT_CONFIG['web']['client_id'],
            'client_secret': CLIENT_CONFIG['web']['client_secret'],
            'redirect_uri': CLIENT_CONFIG['web']['redirect_uris'][0],
            'grant_type': 'authorization_code'
        }

        response = request.post(
            CLIENT_CONFIG['web']['token_uri'], data=token_params)

        if response.status_code == 200:
            response_data = response.json()
            access_token = response_data.get('access_token')

            if access_token:
                return JsonResponse({'access_token': access_token})
            else:
                return JsonResponse({'error': 'Access token not found in response'}, status=500)
        else:
            return JsonResponse({'error': 'Failed to obtain access token'}, status=response.status_code)

    except Exception as e:
        return JsonResponse({'error': 'str(e)'}, status=500)


def google_home(request):
    return render(request, 'google_home.html')


def google_signout(request):
    logout(request)
    return redirect('/')


def dashboard(request):
    context = {'button_clicked': None}
    return render(request, 'dashboard.html', context)


def get_shopify_data(request):
    if request.method == "GET":
        print(request.method)
        shop_token = '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'
        # shop_token = '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'
        shop_domain = 'vabhas-test.myshopify.com'
        # shop_domain = 'e7030e-4f.myshopify.com'

        print(shop_token, shop_domain)

        if not shop_token or not shop_domain:
            return HttpResponse('Error: Token or domain is missing in the request')

        try:
            endpoint = f"https://{shop_domain}/admin/api/2023-10/shop.json"
            headers = {'X-Shopify-Access-Token': shop_token}
            response = requests.get(endpoint, headers=headers)

            if response.status_code == 200:
                shop_data = response.json().get('shop')
                if shop_data:
                    shopify_api_instance = Shopify_data_model.objects.create(
                        name=shop_data.get('name'),
                        email=shop_data.get('email'),
                        domain=shop_data.get('domain'),
                        token=shop_token
                    )
                    print("Shopify data saved successfully:",
                          shopify_api_instance)
                else:
                    print("Shop data is missing from the response:",
                          response.json())
            else:
                print("Failed to fetch Shopify data. Status code:",
                      response.status_code)

        except requests.exceptions.RequestException as e:
            print("Request error occurred:", e)
            return HttpResponse('Error: ' + str(e))
        except Exception as e:
            print("Error occurred:", e)
            return HttpResponse('Error: ' + str(e))
        else:
            return HttpResponse('Shopify data saved successfully')
    else:
        return HttpResponse('Invalid request method')


def get_shopify_order(request):
    if request.method == "GET":
        try:
            last_order_id = request.GET.get('last_order_id')

            shopify_data = Shopify_data_model.objects.first()
            if not shopify_data:
                return HttpResponse("Shopify order not found.", status=500)

            token = shopify_data.token

            user_updated = Shopify_order_model.objects.filter(
                user=request.user).order_by('-updated_at').first()
            if user_updated is not None:
                last_updated = user_updated.updated_at.strftime(
                    "%Y-%m-%dT%H:%M:%S%z")
                endpoint = f"https://{
                    shopify_data.domain}/admin/api/2023-10/orders.json?limit=50&order=updated_at ASC&updated_at_min={last_updated}"
            else:
                endpoint = f"https://{
                    shopify_data.domain}/admin/api/2023-10/orders.json?limit=50&order=updated_at ASC"

            headers = {
                'X-Shopify-Access-Token': token,
            }
            params = {'limit': 50}
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()

            if response.status_code == 200:
                orders_data = response.json().get('orders')
                for order in orders_data:
                    created_at = datetime.strptime(
                        order["created_at"], "%Y-%m-%dT%H:%M:%S%z")
                    updated_at = datetime.strptime(
                        order["updated_at"], "%Y-%m-%dT%H:%M:%S%z")
                    data = Shopify_order_model.objects.create(
                        user=request.user,
                        name=order.get('name'),
                        email=order.get('email'),
                        created_at=created_at,
                        updated_at=updated_at,
                        price=order.get('price'),
                        order_id=order.get('id'),
                    )

                saved_orders = Shopify_order_model.objects.order_by(
                    '-updated_at')[:50]
                return render(request, 'shopify_order.html', {'saved_orders': saved_orders})
            else:
                error_message = f"Unable to fetch orders. Status Code :{
                    response.status_code}"
                return HttpResponse(error_message, status=response.status_code)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            return HttpResponse(error_message, status=500)
    else:
        return HttpResponse("Invalid request method.", status=405)


def download_shopify_csv(request):
    try:
        # Get the first 50 products, you can adjust this limit as needed
        products = Shopify_product_model.objects.all()[:50]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="shopify_products.csv"'

        fields = ['product_id', 'name', 'status', 'updated_at']

        writer = csv.DictWriter(response, fieldnames=fields)
        writer.writeheader()

        for product in products:
            writer.writerow({
                'product_id': product.product_id,
                'name': product.name,
                'status': product.status,
                'updated_at': product.updated_at,
            })

        return response
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        return HttpResponse(error_message, status=500)


def get_shopify_product(request):
    if request.method == 'GET':
        try:
            shopify_data = Shopify_data_model.objects.first()
            if not shopify_data:
                return HttpResponse("Shopify Products not found.", status=500)

            last_update_timestamp = shopify_data.last_update_timestamp

            endpoint = f"https://{shopify_data.domain}/admin/api/2023-10/products.json"
            headers = {'X-Shopify-Access-Token': shopify_data.token}

            params = {'limit': 50, 'updated_at_min': last_update_timestamp} if last_update_timestamp else {
                'limit': 50}

            response = requests.get(endpoint, headers=headers, params=params)

            response.raise_for_status()

            if response.status_code == 200:
                products_data = response.json().get('products', [])
                updated_at = timezone.now()

                for product in products_data:
                    product_id = product.get('id')

                    existing_product = Shopify_product_model.objects.filter(
                        product_id=product_id).first()
                    if existing_product:
                        # Update existing product data
                        existing_product.name = product.get('title')
                        existing_product.price = product.get('price')
                        existing_product.status = product.get('status')
                        existing_product.updated_at = updated_at.strftime(
                            "%Y-%m-%d %H:%M:%S")
                        existing_product.save()
                    else:
                        # Create new product entry
                        data = Shopify_product_model.objects.create(
                            product_id=product_id,
                            name=product.get('title'),
                            price=product.get('price'),
                            status=product.get('status'),
                            updated_at=updated_at.strftime(
                                "%Y-%m-%d %H:%M:%S"),
                        )
                        data.save()

                shopify_data.last_update_timestamp = updated_at.strftime(
                    "%Y-%m-%d %H:%M:%S")
                shopify_data.save()

                saved_products = Shopify_product_model.objects.all()[:50]
                return render(request, 'shopify_product.html', {'saved_products': saved_products})
            else:
                error_message = f"Unable to fetch Products. Status Code: {
                    response.status_code}"
                return HttpResponse(error_message, status=response.status_code)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            return HttpResponse(error_message, status=500)
    else:
        return HttpResponse("Invalid request method.", status=405)

from flask import Flask, render_template, request
from datetime import datetime
import requests
import base64

app = Flask(__name__)
@app.template_filter('formatdate')
def format_date(value):
    if value is None:
        return ""

    return datetime.fromisoformat(value[:19]).strftime("%B %d, %Y")  # Use fromisoformat to parse the datetime string

app.jinja_env.filters['formatdate'] = format_date

API_KEY = 'l78412a897ffb54c5ea9c05efe3be49157'
API_SECRET = '298da5801bb94e6999fc8288221d9d2a'

def get_auth_token(api_key, api_secret):
    auth_url = 'https://apigtwb2c.us.dell.com/auth/oauth/v2/token'
    auth_str = f'{api_key}:{api_secret}'
    auth_bytes = auth_str.encode('ascii')
    encoded_auth_str = base64.b64encode(auth_bytes).decode('ascii')

    headers = {'Authorization': f'Basic {encoded_auth_str}'}
    body = {'grant_type': 'client_credentials'}
    
    response = requests.post(auth_url, headers=headers, data=body)
    
    if response.status_code != 200:
        return 'Failed to get auth token', False

    return response.json()['access_token'], True

def get_warr_from_dell(api_key, api_secret, svctag, brand):
    if brand == 'HP':
        return "We apologize, HP warranty lookups are currently unavailable.", False
    elif brand == 'Lenovo':
        return "We apologize, Lenovo warranty lookups are currently unavailable.", False

    token, success = get_auth_token(api_key, api_secret)
    if not success:
        return token, False

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    params = {
        'servicetags': svctag,
        'Method': 'GET'
    }

    response = requests.get('https://apigtwb2c.us.dell.com/PROD/sbil/eapi/v5/asset-entitlements', headers=headers, params=params)

    if response.status_code == 404:
        return 'No warranty information found for the provided service tag.', False
    elif response.status_code != 200:
        return f'Caught {response.status_code} as the response code. Unable to get details for the given service tag.', False

    results = response.json()
    return results, True


@app.route('/', methods=['GET', 'POST'])
def home():
    original_brand = ['Select...', 'Dell', 'HP', 'Lenovo']
    brand = original_brand[:]
    serial_number = ''
    results = []
    success = True
    error_message = None

    if request.method == 'POST':
        brand_input = request.form.get('brand')
        serial_number = request.form.get('serial_number')

        if not brand_input or brand_input == 'Select...':
            error_message = 'Please select a valid manufacturer.'
        elif brand_input == 'Dell' and not serial_number:
            error_message = 'Please enter a serial number for Dell products.'
        elif brand_input == 'HP' and not serial_number:
            error_message = 'Please enter a serial number for HP products.'
        elif brand_input == 'Lenovo' and not serial_number:
            error_message = 'Please enter a serial number for Lenovo products.'

        if not error_message:
            brand = brand_input
            if brand == 'Dell' and serial_number:
                results, success = get_warr_from_dell(API_KEY, API_SECRET, serial_number, brand)  # Pass the brand to the function
            elif brand in ['HP', 'Lenovo'] and serial_number:
                results, success = get_warr_from_dell(API_KEY, API_SECRET, serial_number, brand)  # Pass the brand to the function

            return render_template('results.html', results=results, success=success)

    return render_template('index.html', brand=brand, serial_number=serial_number, error_message=error_message)



if __name__ == '__main__':
    app.run(debug=True)

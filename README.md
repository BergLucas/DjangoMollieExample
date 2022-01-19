# DjangoMollieExample

An example of a Django application using Mollie as a payment system.

## Requirements

The requirements can be found in:

-   environment.yml (for conda)
-   requirements.txt (for pip)

## Config

You can change different parameters in the project configuration file:

-   MOLLIE_API_KEY: Your Mollie API key.
-   MOLLIE_DESCRIPTION_TEMPLATE: The description template of the Mollie payments.
-   MOLLIE_BASE_URL: The base URL of the server. This is required to create a webhook for Mollie. (You may want to use a tool like [ngrok](https://ngrok.com/) for testing purposes.)
-   MOLLIE_REDIRECT_URL_TEMPLATE: The redirection url template that will be used by Mollie.
-   MOLLIE_PAYMENT_METHOD: The payment method.

## Setup the database

How to setup the database:

```bash
cd src
python manage.py makemigrations
python manage.py migrate
```

## Run

How to run the app:

```bash
cd src
python manage.py runserver
```

## License

All code is licensed for others under MIT License (see LICENSE).

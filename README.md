# Attribute Based Alert API

This is an API that support creation of users, alerts and rules.
Users are the users that will recibe the alerts.
Alerts generate "webhooks" that other applications can activate when they need to send an alert.
Rules match alerts and users to select to wich users to send the alerts.

## Getting started

1. Clone the repository

```bash
> git clone https://github.com/axelwass/python-attribute-based-alert-API.git
```

2. Move into directory

```bash
> cd python-attribute-based-alert-API
```

3. Install dependencies (if on windows10, you will probably have to allow long paths as explaind in [twilio documentation](https://github.com/twilio/twilio-python#installation]))

```bash
> pip install -r requeriments.txt
```

4. Modify config file and replace with your twilio account settings

```bash
> vim configs/config.json
```

5. Run the applications

```bash
> python3 src/server.py
```

## Example

To test update the phone number on the database and start the servce.

Try the following URL (POST):
* http://localhost:5000/alerts/big_enemy/dryrun?reason=nazgul
* http://localhost:5000/alerts/big_enemy/trigger?reason=nazgul
* http://localhost:5000/alerts/small_enemy/trigger?reason=orc
* http://localhost:5000/alerts/small_enemy/trigger?reason=orc

Depending on the alert you call, using the defined rule, user are selected. 
Depending on the serveirty of the alert, different methods are used to contact the users.
And finnaly, the text is written using a template, and the information on the user and alert.
Channels to conntact user can be a text mesage or a call using Twilio api.

## Future work
* Add swagger documentation.
* Add more channels. For example one for slack.
* Add integration with Active Directory.
* Add authentication.
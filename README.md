# Attribute Based Alert API

This is an API that support creation of users, alerts and rules.
Users are the users that will recibe the alerts.
Alerts generate "webhooks" that other applications can activate when they need to send an alert.
Rules match alerts and users to select to wich users to send the alerts.

## Example

If you have this rule defined::

```JSON
{
"id": "ProjectLead",
"conditions": [
  {
	"first": {
	  "object": "User",
	  "value": "projects"
	},
	"op": "contains",
	"second": {
	  "object": "Alert",
	  "value": "project"
	}
  },
  {
	"first": {
	  "object": "User",
	  "value": "role"
	},
	"op": "==",
	"second": {
	  "object": "Value",
	  "value": "Lead"
	}
  }
]
}
```

You could get something like this on a dry_run:

```JSON
{
  "alert": {
    "attributes": {
      "project": "FellowshipOfTheRing",
      "severity": 100
    },
    "id": "ringcreated",
    "template": "The ring has been created in {{alert["attributes"]["location"]}}"
  },
  "chanels": {
    "id": "twilio_1",
    "min_severity": 0,
    "module": "twilio_sms"
  },
  "users": [
    {
      "attributes": {
        "projects": [
          "FellowshipOfTheRing",
          "ProjectB"
        ],
        "role": "Lead"
      },
      "username": "fbagins"
    }
  ]
}
```
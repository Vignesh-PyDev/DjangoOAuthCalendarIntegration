# Django Google Calendar Integration

## Flow of Application

I have created two API end points,

/app/v1/calendar/init/
/app/v1/calendar/redirect/

## Describe your project

When we hit the 1st API,it will take you to a another page to get your credentials to access the calendar.
Once the credentilas ar verified,I then redirect the request to another API.

Things to do:
First Create a Project in Google Cloud using the following url

https://console.cloud.google.com/projectcreate?previousPage=%2Fapis%2Fdashboard%3Fproject%3Dhallowed-digit-384515%26organizationId%3D0&organizationId=0

It asks you to login with your credentials.

Then Enable the calendar API.

Then Configure OAuth Consent Screen.(It basically asks app name,email,scopes.,)

Then go to credentials-->Create Credentials-->OAuth client ID.
  Here select Web application,give a name.
  Carefull at giving the Authorized redirect URIs.(it should be same as the redirect_URI in our code)
  then save.
Now our created credentials is listed in credentials page,then download and rename it as credentials.json(should be placed inside the Project folder.)

Now Google part is done.



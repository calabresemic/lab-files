# These are some custom apps that I'm running from HA to complete more complex tasks.

## apps.yaml
This file is used to tell AppDaemon about apps and pass arguments to the apps themselves.

## AuroraNotify
This app was created based on the builtin aurora integration that is currently broken. The NOAA data is presented with longitude in the 0-360 degree format and not the -180-180 degree format used my Home Assistant (and like everyone else...).

I use this to adjust an input_number that is monitored to alert us when the aurora is visible. This is hopefully a temporary workaround but the github repo has not been touched in two years so I'm not sure how long it will take for the issue to be addressed.

https://www.home-assistant.io/integrations/aurora/

## BlackvueDashCamDownload
This application is for copying data from the Blackvue dashcam to an SMB share on my file server. My wife always wants to show me things from videos but forgets until they're overwritten so this allows us to keep them for as many days as we want. 

One note here is that we have the dual camera version and it does fill up space pretty quick so be aware of that.

I have made some minor adjustments from the original but it's one of those it just works so I'll leave it alone for now things. 

Original link:
https://www.chadmccune.net/2020/05/20/home-assistant-blackvue-dashcam-automatically-archiving-all-footage/
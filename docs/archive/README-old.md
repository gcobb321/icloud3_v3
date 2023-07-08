# iCloud3  Device Tracker Custom Component

[![CurrentVersion](https://img.shields.io/badge/Current_Version-v3.0.0-blue.svg)](https://github.com/gcobb321/icloud3)
[![Released](https://img.shields.io/badge/Released-November,_2022-blue.svg)](https://github.com/gcobb321/icloud3)
[![ProjectStage](https://img.shields.io/badge/Project_Stage-Beta-red.svg)](https://github.com/gcobb321/icloud3)
[![Type](https://img.shields.io/badge/Type-Custom_Component-orange.svg)](https://github.com/gcobb321/icloud3)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/gcobb321/icloud3)

### Introduction

iCloud3 is a device tracker custom component that tracks your iPhones, iPads, Apple Watches, AirPods and other Apple devices. It requests location data from Apple's iCloud  Location Services and monitors various triggers sent from the Home Assistant Companion App (iOS App) to Home Assistant. Sensors are updated with the device's location, distance from zones, travel time to zones, etc. 

Although Home Assistant has it's own official iCloud component, iCloud3 goes far beyond it's capabilities. The important highlights include:

- **HA Integration** - iCloud3 is a Home Assistant custom integration on the *HA Settings > Devices & Services > Integrations* screen.
- *T**he Configurator*** - All of the parameters are updated on configuration screens selected from the *iCloud3 Integrations* entry.
- **Track devices from several sources** - The Family Sharing list, the FindMy App and the HA Companion App (iOS App ).
- **Actively track a device** - Request it's location on a regular interval.
- **Passively monitor a device** - Do not request it's location, just report it when it is available after a tracked device location request.
- **Waze Route Service** - Request the travel time and distance to a zone from the current location. 
- **Waze Route Service History Database** - Save Waze travel time information to a local database. 
- **Track from Multiple Zones** - The device is always tracked from the Home Zone. Now it can also be tracked from another zone (office, second home, parents, etc.) and trigger automations based on that zone. 
- **Improved GPS Accuracy** - GPS wandering errors leading to incorrect zone exits are eliminated.
- **Stationary Zone** - Creates a dynamic *Stationary Zone* by monitoring when the device has not moved for a while (doctors office, store, friend's house) that conserves battery life.
- **Sensors and more sensors** - Many sensors are created and updated with distance, travel time, polling data, battery status,  zone attributes, etc. 
- **Event Log** - Display the current status and event history of every tracked and monitored device,
- **Detailed debugging information** - Several levels location history transactions can be displayed in the Event Log or the Home Assistant Log File.
- **Updating and Restarting** - iCloud3 can be restarted without restarting Home Assistant. The current device_tracker and sensor entity states are restored on a restart.
- **Device_tracker and sensor entities** - iCloud3 devices and sensors are true Home Assistant entities. They are added, deleted and updated using *The Configurator*, not the HA Devices and Entities screens.
- **Nearby Devices** - The location's of all devices is monitored to see if there are any in the same location.
- **And More** - Review the following documentation to see if it will help you track and monitor the locations of your family members and friends.

Below is a Lovelace screen showing some of the information iCloud3 can display,

- The current zone (Home)
- Distance and Travel Time to Home
- Distance since the last location request and the direction you are moving
- The interval between location requests, when the next request will be made and when the last one was made
- Battery level
- Tracking information from the Home zone and the Warehouse zone
- The Event Log highlighting all tracking activity and results

![](images/tracking-gary-home-tfz-evlog.png)

Many sensors are created that can be used to trigger automation and scripts such as:

- Entering a zone (when you arrive home)
- Exiting a zone (When you leave Home)
- Distance or time from another location
- Battery level monitoring (charging is needed or has been completed)
- The location of no-tracked devices
- Presence detection of family members (all Home, some Home, none Home)

The extensive iCloud3 documentation:

- Introduces the many features and components
- Details the installation process
- Highlights the configuration screens and parameters
- Provides example screens, automations and scripts

Review the following chapters and see it is right for you.



*Gary Cobb, aka GeeksterGary*

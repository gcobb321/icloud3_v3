```
# [iCloud3 v3 iDevice Tracker](https://github.com/gcobb321/icloud3_v3)

iCloud3 is a custom component that allows you to track your iDevices (iPhone, iPad, Watch, etc) using location data from your Apple iCloud account and the HA Companion app.

### Highlights of what **iCloud3** can do

- **Track devices from several sources** - Family members on the iCloud Account Family Sharing list, those who are sharing their location on FindMy App and devices that have installed the HA Companion App (iOS App) can be tracked.
- **Actively track a device** - The device will request it's location on a regular interval.
- **Passively monitor a device** - The device does not request it's location but is tracked when another tracked device requests theirs.
- **Waze Route Service** - The travel time and route distance to a tracked zone (Home) is provided by Waze.
- **Stationary Zone** - A dynamic *Stationary Zone* is created when the device has not moved for a while (doctors office, store, friend's house). This helps conserve battery life.
- **Sensors and more sensors** - Many sensors are created and updated with distance, travel time, polling data, battery status, zone attributes, etc. The sensors that are created is customizable.
- **Nearby Devices** - The location of all devices is monitored and the distance between devices is determined. Information from devices close to each other is shared.
- **Event Log** - The current status and event history of every tracked and monitored device is displayed on the iCloud3 Event Log custom Lovelace card. It shows information about devices that can be tracked, errors and alerts, nearby devices, tracking results, debug information and location request results.

## Useful Links

* [README](https://github.com/gcobb321/icloud3_v3/blob/master/README.md)
* [Documentation](https://gcobb321.github.io/icloud3_v3/#/)
* [Repository](https://github.com/gcobb321/icloud3_v3)
```
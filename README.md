# Mijia Temperature and Humidity Monitor Clock Integration for Home Assistant

![mi-temperature-and-humidity-monitor-pro-lywsd02mmc-1](https://github.com/user-attachments/assets/15d6fccc-e40a-4344-8360-9a40797efc55) 

This Home Assistant integration allows you to control Mijia Temperature and Humidity Monitor (LYWSD02MMC) clocks. You can set the time and configure the devices seamlessly using the Home Assistant interface.

## Features

- **Set time**: Adjust the clock's time by specifying the desired time and time zone.
- **Set temperature units**: Set the temperature units to Celsius or Fahrenheit.

## Installation

### HACS (Home Assistant Community Store)

1. **Install HACS**:
   - If you haven't already, install [HACS](https://hacs.xyz/), following the [official guide](https://hacs.xyz/docs/setup/download).

2. **Add Custom Repository**:
   - Navigate to `HACS` in the Home Assistant sidebar.
   - Click on the `Integrations` tab.
   - Click on the three-dot menu in the upper-right corner and select `Custom repositories`.
   - Enter the repository URL `https://github.com/ov1d1u/mijia_thermometer_clock` in the dialog box.
   - Select `Integration` as the category and click `Add`.

3. **Install the Integration**:
   - Search for "Mijia Temperature and Humidity Monitor Clock" in the HACS integrations.
   - Click `Install` to add it to your Home Assistant setup.

4. **Restart Home Assistant**:
   - After installation, restart your Home Assistant instance to activate the integration.

### Manual Installation

1. **Clone or Download**:
   - Clone or download this repository to your Home Assistant `custom_components` directory.
   - Ensure it is located under `custom_components/mijia_thermometer_clock`.

2. **Restart Home Assistant**:
   - Restart your Home Assistant instance to activate the integration.

## Configuration

1. **Navigate**:
   - Go to the Home Assistant configuration page.
   
2. **Add Integration**:
   - Add the Mijia Temperature and Humidity Monitor Clock from the available integrations.
   - Follow the on-screen instructions to discover and configure your devices.

## Service Calls

The integration supports the following service call:

### `set_time`

| Field      | Required | Description                       | Example                   |
|------------|----------|-----------------------------------|---------------------------|
| `device_id`| Yes      | The device ID of the clock.       |                           |
| `time`     | Yes      | The time in YYYY-MM-DD HH:MM:SS format. | 2022-02-22 13:30:00       |
| `timezone` | Yes      | Timezone in IANA format.          | Europe/Bucharest          |

To use this service, call it from your Home Assistant with the necessary parameters.

## Troubleshooting

- **Device Not Discovering**: Ensure that your clock is powered on and in range. If issues persist, try entering the MAC address manually.
- **Connection Errors**: Check your device's compatibility with the supported service data.

## Disclaimer

This is the very first release of the Mijia Temperature and Humidity Monitor Clock integration. It may contain bugs, and features might change in future updates. Please report any issues on the repository to help with ongoing development and improvements.

## Support

For further assistance, ensure to check the issues section of this GitHub repository.

## License

This project is licensed under the Apache 2.0 license.

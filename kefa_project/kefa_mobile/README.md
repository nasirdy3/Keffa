# KEFA Mobile App (Flutter)

This directory contains the source code for the native KEFA mobile application (Chapter 15).

## Prerequisites

1.  **Install Flutter SDK**: [Download here](https://docs.flutter.dev/get-started/install)
2.  **Install VS Code or Android Studio**.
3.  **Emulator**: Set up an Android Emulator or iOS Simulator.

## How to Run

1.  Open your terminal/command prompt.
2.  Navigate to this directory:
    ```bash
    cd kefa_mobile
    ```
3.  Install dependencies:
    ```bash
    flutter pub get
    ```
4.  Run the app:
    ```bash
    flutter run
    ```

## Project Structure

- `lib/main.dart`: Entry point and Theme configuration.
- `lib/screens/`: Individual screen UIs (Home, Tournaments, Chat, Profile).
- `pubspec.yaml`: Project configuration and dependencies.

## Note
This is a high-fidelity frontend prototype. To fully functionalize it, you must implement the API calls to your Django backend in `lib/services/api_service.dart`.

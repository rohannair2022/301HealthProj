# Super Heart


## Overview
SuperHeart is a project aimed at improving health metrics using a combination of React, Flask, CSS, and HTML. It is a comprehensive heart health monitoring platform designed to bridge the gap between patients and healthcare providers while leveraging modern wearable technology.

Benefits:
For Patients: Take control of your heart health with comprehensive monitoring, professional oversight, and actionable insights.
Health Data Upload, Fitbit Integration, Doctor connect, Progress Tracking, Overall Health Score

For Healthcare Providers: Gain a holistic view of patient health between visits, enabling more informed care decisions and timely interventions.
Patient management, Patient document access, Daily patient health data

For Healthcare Systems: Bridge gaps in continuous care with a platform that connects patients and providers through meaningful health data.

## [Product Demo](https://drive.google.com/file/d/129VqskSWf071mU7eiozLB-5TdyyEWTBp/view?usp=sharing) 
[![image](https://github.com/user-attachments/assets/3320e297-afed-4d01-8437-e4c5ece62792)](https://drive.google.com/file/d/129VqskSWf071mU7eiozLB-5TdyyEWTBp/view?usp=sharing) 

This is a video

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Contributing](#contributing)
- [Contact](#contact)

## Installation
To get started with Super-Heart, clone the repository and install the necessary dependencies.

```bash
git clone https://github.com/rohannair2022/301HealthProj.git
cd 301HealthProj
```

Make sure you have Node.js and Python installed on your machine. Then, run the following commands to install the dependencies:

```bash
# For JavaScript dependencies
npm install

# For Python dependencies
pip install -r requirements.txt
```

## Usage
After installation, you can start the project by running the following command:

```bash
# For the JavaScript part
cd frontend/super-heart
npm start

# For the Python part
cd backend
python app.py
```
If you want to use the [fibit feature](https://dev.fitbit.com/build/reference/web-api/developer-guide/getting-started/) add your Fitbit key in the env file as:
```bash
CLIENT_ID:<fitbit-client-id>
CLIENT_SECRET:<fitbit-client-secret>
FITBIT_REDIRECT_URI:localhost:5001/watch
```
Open your browser and navigate to `http://localhost:3000` to see the application in action.

## Features
- **React**: Front-end functionality for interactive health tracking.
- **Flask**: Back-end processing and data analysis.
- **TailwindCSS**: Styling for the application.
- **HTML**: Structure of the web application.

## Contributing
We welcome contributions! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -m 'Add some feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Open a pull request.


## Contact
For any questions, feel free to open an issue.


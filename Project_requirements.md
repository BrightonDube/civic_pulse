# Requirements Document: CivicPulse

## Introduction

CivicPulse is a centralized, AI-powered platform that enables citizens to report infrastructure issues (potholes, water leaks, illegal dumping, broken streetlights) through geotagged photos. The system uses AI to automatically categorize and prioritize issues, providing community managers with real-time visibility through an interactive heat map to optimize resource deployment.

## Glossary

- **System**: The CivicPulse platform (backend, frontend, and AI components)
- **User**: A citizen who reports infrastructure issues
- **Admin**: A maintenance manager who reviews and manages reported issues
- **Report**: A submitted infrastructure issue with photo, location, and metadata
- **Issue**: A specific infrastructure problem (pothole, water leak, vandalism, etc.)
- **Severity_Score**: An AI-generated numeric value (1-10) indicating issue urgency
- **Heat_Map**: A visual representation showing geographic clusters of issues
- **GPS_Coordinates**: Latitude and longitude values extracted from photo metadata or device
- **AI_Vision_API**: The external AI service (OpenAI Vision or similar) for image analysis
- **Status**: The current state of a report (Reported, In Progress, Fixed)
- **Duplicate_Report**: A report submitted for an issue already in the system
- **Offline_Draft**: A report created without network connectivity
- **Leaderboard**: A ranked list of users by number of reports submitted

## Requirements

### Requirement 1: Geotagged Photo Reporting

**User Story:** As a user, I want to report infrastructure issues by uploading a photo with automatic location capture, so that I can quickly document problems without manual data entry.

#### Acceptance Criteria

1. WHEN a user uploads a photo, THE System SHALL extract GPS coordinates from the photo's EXIF metadata
2. IF the photo lacks EXIF GPS data, THEN THE System SHALL use the device's current GPS location
3. WHEN GPS coordinates are obtained, THE System SHALL display the location on a map preview before submission
4. WHEN a user submits a report, THE System SHALL store the photo, GPS coordinates, and timestamp
5. IF GPS coordinates cannot be obtained from either source, THEN THE System SHALL prompt the user to manually place a pin on the map

### Requirement 2: AI-Powered Image Analysis and Categorization

**User Story:** As a user, I want the system to automatically categorize and prioritize my report, so that I don't have to fill out lengthy forms.

#### Acceptance Criteria

1. WHEN a photo is uploaded, THE System SHALL send the image to the AI_Vision_API for analysis
2. WHEN the AI_Vision_API returns results, THE System SHALL extract the issue category (Pothole, Water Leak, Vandalism, Broken Streetlight, Illegal Dumping, Other)
3. WHEN the AI_Vision_API returns results, THE System SHALL extract a Severity_Score between 1 and 10
4. IF the AI_Vision_API fails or returns an error, THEN THE System SHALL assign a default category of "Other" and a Severity_Score of 5
5. WHEN AI analysis completes, THE System SHALL store the category and Severity_Score with the report
6. THE System SHALL allow users to override the AI-generated category if incorrect

### Requirement 3: Interactive Heat Map Dashboard

**User Story:** As an admin, I want to view all reported issues on an interactive heat map, so that I can identify high-priority areas and deploy resources efficiently.

#### Acceptance Criteria

1. WHEN an admin accesses the dashboard, THE System SHALL display all active reports on an interactive map
2. WHEN displaying reports on the map, THE System SHALL use color coding based on Severity_Score (red for 8-10, yellow for 4-7, green for 1-3)
3. WHEN multiple reports exist in close proximity, THE System SHALL display them as a cluster with a count indicator
4. WHEN an admin clicks on a report marker, THE System SHALL display the photo, category, Severity_Score, status, and submission timestamp
5. THE System SHALL allow admins to filter reports by category, status, and date range
6. THE System SHALL update the heat map in real-time when new reports are submitted

### Requirement 4: Report Status Tracking and Notifications

**User Story:** As a user, I want to receive updates when my report status changes, so that I know the issue is being addressed.

#### Acceptance Criteria

1. WHEN a report is submitted, THE System SHALL set the initial status to "Reported"
2. WHEN an admin changes a report status, THE System SHALL update the status to "In Progress" or "Fixed"
3. WHEN a report status changes, THE System SHALL send an email notification to the user who submitted the report
4. WHEN a report status changes, THE System SHALL send an SMS notification to the user who submitted the report
5. WHEN a user views their report, THE System SHALL display the current status and timestamp of the last status change
6. THE System SHALL maintain a status history log for each report

### Requirement 5: Duplicate Detection and Report Upvoting

**User Story:** As a user, I want to upvote existing reports for the same issue, so that we avoid duplicate submissions and show community consensus.

#### Acceptance Criteria

1. WHEN a user submits a report, THE System SHALL search for existing reports within 50 meters of the GPS_Coordinates
2. IF an existing report is found within 50 meters with the same category, THEN THE System SHALL prompt the user to upvote the existing report instead
3. WHEN a user upvotes an existing report, THE System SHALL increment the upvote count for that report
4. WHEN a user upvotes a report, THE System SHALL add the user to the notification list for that report
5. THE System SHALL display the upvote count on each report in the heat map and user views
6. THE System SHALL prevent a user from upvoting the same report multiple times

### Requirement 6: Offline Mode Support

**User Story:** As a user, I want to create reports when I have no network connection, so that I can document issues immediately and have them submitted automatically when connectivity is restored.

#### Acceptance Criteria

1. WHEN a user has no network connectivity, THE System SHALL allow the user to create an Offline_Draft
2. WHEN creating an Offline_Draft, THE System SHALL store the photo, GPS_Coordinates, and timestamp locally in the browser
3. WHEN network connectivity is restored, THE System SHALL automatically detect the connection
4. WHEN connectivity is restored, THE System SHALL upload all Offline_Drafts to the server
5. WHEN an Offline_Draft is successfully uploaded, THE System SHALL remove it from local storage
6. THE System SHALL display a visual indicator showing the number of pending Offline_Drafts
7. IF an Offline_Draft upload fails, THEN THE System SHALL retry the upload with exponential backoff

### Requirement 7: Public Leaderboard

**User Story:** As a user, I want to see a leaderboard of top reporters in my neighborhood, so that I feel motivated to contribute to community improvement.

#### Acceptance Criteria

1. THE System SHALL maintain a count of submitted reports for each user
2. WHEN a user accesses the leaderboard, THE System SHALL display the top 10 users by report count
3. WHEN displaying the leaderboard, THE System SHALL show the user's rank, username, and total report count
4. THE System SHALL allow users to filter the leaderboard by neighborhood or geographic area
5. THE System SHALL update leaderboard rankings in real-time when new reports are submitted
6. WHERE a user opts out of leaderboard participation, THE System SHALL exclude that user from public leaderboard displays

### Requirement 8: User Authentication and Authorization

**User Story:** As a user, I want to create an account and log in securely, so that I can track my reports and receive notifications.

#### Acceptance Criteria

1. WHEN a user registers, THE System SHALL require an email address, password, and phone number
2. WHEN a user registers, THE System SHALL send a verification email to confirm the email address
3. WHEN a user logs in, THE System SHALL validate credentials against stored hashed passwords
4. THE System SHALL implement role-based access control with "User" and "Admin" roles
5. WHEN an admin logs in, THE System SHALL grant access to the admin dashboard and heat map
6. THE System SHALL maintain user sessions with secure, HTTP-only cookies
7. WHEN a user requests a password reset, THE System SHALL send a time-limited reset link via email

### Requirement 9: Report Management for Admins

**User Story:** As an admin, I want to manage reports by updating their status and assigning them to maintenance teams, so that I can coordinate issue resolution efficiently.

#### Acceptance Criteria

1. WHEN an admin views a report, THE System SHALL display all report details including photo, location, category, Severity_Score, and upvote count
2. THE System SHALL allow admins to change report status to "In Progress" or "Fixed"
3. THE System SHALL allow admins to add internal notes to reports
4. THE System SHALL allow admins to reassign the AI-generated category if incorrect
5. THE System SHALL allow admins to adjust the Severity_Score if the AI assessment is inaccurate
6. WHEN an admin marks a report as "Fixed", THE System SHALL archive the report and remove it from the active heat map
7. THE System SHALL maintain an audit log of all admin actions on reports

### Requirement 10: Data Persistence and Geographic Queries

**User Story:** As a system architect, I want to store report data with geographic indexing, so that location-based queries are fast and efficient.

#### Acceptance Criteria

1. THE System SHALL store all reports in a PostgreSQL database with PostGIS extension
2. THE System SHALL store GPS_Coordinates as PostGIS POINT geometry types
3. WHEN querying for nearby reports, THE System SHALL use PostGIS spatial indexes for performance
4. THE System SHALL store photos as binary data or file references with associated metadata
5. THE System SHALL implement database constraints to ensure data integrity (non-null GPS coordinates, valid status values)
6. THE System SHALL create indexes on frequently queried fields (status, category, submission timestamp)

### Requirement 11: API Design and Integration

**User Story:** As a developer, I want a well-documented REST API, so that the frontend and potential third-party integrations can interact with the system reliably.

#### Acceptance Criteria

1. THE System SHALL expose a REST API using FastAPI with OpenAPI documentation
2. THE System SHALL implement API endpoints for report submission, retrieval, status updates, and user authentication
3. WHEN an API request is made, THE System SHALL validate request payloads against defined schemas
4. WHEN an API request fails validation, THE System SHALL return a 400 status code with descriptive error messages
5. THE System SHALL implement rate limiting to prevent abuse (100 requests per minute per user)
6. THE System SHALL require authentication tokens for all endpoints except registration and login
7. THE System SHALL return appropriate HTTP status codes (200, 201, 400, 401, 403, 404, 500)

### Requirement 12: Frontend User Interface

**User Story:** As a user, I want an intuitive and responsive interface, so that I can easily report issues and track their status on any device.

#### Acceptance Criteria

1. THE System SHALL provide a Progressive Web App (PWA) built with React and TypeScript
2. WHEN a user accesses the app, THE System SHALL display a responsive interface that works on mobile, tablet, and desktop
3. THE System SHALL implement a map view using Leaflet.js or Mapbox for displaying and selecting locations
4. THE System SHALL provide a camera interface for capturing photos directly from mobile devices
5. THE System SHALL display a user dashboard showing all reports submitted by the logged-in user
6. THE System SHALL implement loading states and error messages for all asynchronous operations
7. WHERE the user is offline, THE System SHALL display a clear indicator and enable offline mode features


# Enhanced Learning Management System (LMS)

## Project Overview

The **Enhanced LMS** is a modern, role-based learning management system designed to streamline online education for institutions, instructors, students, and sponsors. With a focus on usability, security, and scalability, this LMS provides dedicated features for each user role, including robust course management, assessments, dashboards, sponsorships, notification systems, and AI-enhanced tools.

---

## Roles & Responsibilities

| **Role**     | **Access & Features**                                                                                   |
|--------------|--------------------------------------------------------------------------------------------------------|
| **Admin**    | Full control: manage users, courses, assessments, view dashboards, analytics.                          |
| **Instructor** | Create/update courses & assessments, view enrolled students, receive engagement notifications.         |
| **Student**  | Enroll in courses, complete assessments, view notifications and course progress.                       |
| **Sponsor**  | Fund students/courses, track student progress, receive progress email notifications.                   |

---

## Features

- **Multi-Role Authentication:** Secure login with role-based access for Admin, Instructor, Student, and Sponsor.
- **Course Management:** Create, update, delete, and enroll in courses.
- **Assessment Module:** Manage quizzes, assignments, and exams with automated grading.
- **Sponsorship:** Sponsors can fund courses or students and receive regular progress updates.
- **Dashboards & Analytics:** Real-time dashboards for admins and instructors.
- **Notifications:** In-app and email notifications for important activities and progress.
- **User Management:** Admin panel to manage all user accounts and permissions.
- **Progress Tracking:** Students and sponsors can track course and assessment completion.
- **Scalable & Modular:** Designed for easy extension and deployment.

### AI Features

- **AI-Powered Course Description Generation**:  
  When creating a new course, the LMS uses AI (Groq/OpenAI GPT-OSS-20B) to automatically generate a course description based on the course name and difficulty level, ensuring high-quality and engaging course listings even if instructors do not provide a description.

---

## API Endpoints

| **Method** | **Endpoint**                       | **Description**                                 | **Access**         |
|------------|------------------------------------|-------------------------------------------------|--------------------|
| `POST`     | `/login`                  | User login                                      | All roles          |
| `POST`     | `/register`               | Register a new user                             | All roles          |
| `GET`      | `/courses`                     | List all courses                                | All roles          |
| `POST`     | `/courses`                     | Create a new course (AI description support)    | Instructor, Admin  |
| `PUT`      | `/courses/{course_id}`         | Update course details                           | Instructor, Admin  |
| `DELETE`   | `/courses/{course_id}`         | Delete a course                                 | Instructor, Admin  |
| `GET`      | `/courses/{course_id}/students`| View enrolled students                          | Instructor, Admin  |
| `POST`     | `/assessments`                 | Create an assessment                            | Instructor, Admin  |
| `GET`      | `/assessments/{id}`            | View assessment details                         | All roles          |
| `POST`     | `/assessments/{id}/submit`     | Submit assessment answers                       | Student            |
| `GET`      | `/notifications`               | List user notifications                         | All roles          |
| `POST`     | `/sponsorships`                | Sponsor a student/course                        | Sponsor            |
| `GET`      | `/sponsorships`                | View sponsorships and progress                  | Sponsor            |
| `GET`      | `/dashboard`                   | Analytics dashboard                             | Admin, Instructor  |

*Note: Replace `{course_id}` and `{id}` with actual IDs.*

## For other API Endpoint
```
https://documenter.getpostman.com/view/33338845/2sB3QNp8fS
```
---

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/Anoj-07/Enhanced-Learning-Management-System-.git
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**
   ```bash
   python manage.py runserver
   ```

---

## Technologies Used

- **Python** (100%)
- Django 
- RESTful API standards
- **AI Integration**: Groq/OpenAI GPT-OSS for dynamic text generation

---

## License

This project is licensed under the MIT License.

---

## Contact

For questions, issues, or contributions, please reach out via [GitHub Issues](https://github.com/Anoj-07/Enhanced-Learning-Management-System-/issues).

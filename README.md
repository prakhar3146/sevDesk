# **sevDesk Contact Sync Portal**

## **Overview**
This repository contains the source code for automating the **sevDesk to HubSpot contact sync** process. The project aims to improve efficiency, reduce manual errors, and streamline operations using a Flask-based backend deployed on AWS EC2.

**Proof of Concept:**
- **GitHub:** [sevDesk Repository](https://github.com/prakhar3146/sevDesk.git)


## **Tech Stack**
- **Backend:** Python (Flask)
- **Frontend:** HTML, CSS, JavaScript
- **Server:** AWS EC2 (Ubuntu) with Apache2 & Gunicorn
- **Version Control:** GitHub

### **Tools Used**
- Visual Studio Code (IDE)
- Postman (API Testing)
- GitHub Desktop (Version Control)
- MS Excel (Data Analysis)

## **Features**
- ✅ Automated **contact synchronization** between sevDesk and HubSpot
- ✅ API integration for **retrieving and processing contacts**
- ✅ Secure authentication with **2FA**
- ✅ **Logging & Monitoring** for analysis and debugging
- ✅ **Automated email notifications** on sync completion

## **Installation & Setup**
### **1. Clone the Repository**
```bash
git clone https://github.com/prakhar3146/sevDesk.git
cd sevDesk
```

### **2. Create & Activate a Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Set Environment Variables**
Create a `.env` file and add:
```bash
API_KEY=""
SEVAPI=""
HUBAPI=""
SEVURL=""
SEVUSERNAME=""
SEVPASSWORD=""
HUBURL=""
HUBUSERNAME=""
HUBPASSWORD=""
SENDERPASSKEY=""
SENDERMAIL=""
SENDEREMAILPASSWORD=""
SMTP=""
SEVEMAILAPIURL=""
```

### **5. Run the Application Locally**
```bash
flask run --host=0.0.0.0 --port=5000
```

### **6. Running with Gunicorn (Production)**
```bash
gunicorn -w 3 -b 0.0.0.0:5000 app:app
```
Additional information : 
** The gunicorn server can be used as a proxy and apache2 as reverse proxy **
** The gunicorn server can be run in daemon mode to ensure uptime **

## **Operations Workflow**
1. **User initiates sync** via the UI.
2. **System processes the request** and validates data.
3. **Data is retrieved from sevDesk and HubSpot APIs**.
4. **Contacts are created in HubSpot** if they exist in sevDesk but not in HubSpot.
5. **Logs and reports** are generated for monitoring, analysis, and debugging.
6. **Email notifications** are sent upon completion.

## **Deployment Strategy**
- **Code is stored in GitHub** for version control.
- **Continuous Integration (CI/CD) pipelines** are set up for deployment.
- **AWS EC2 instance** hosts the backend.
- **Gunicorn & Apache2** handle application hosting.
- **Database** can be used to store relevant information(Optional).

## **Security Considerations**
- **Authentication & Authorization** using **2FA**.
- **Environment variables** for sensitive information (e.g., API credentials).
- **Firewall & Security Groups** configured in AWS.
- **Regular security audits** to identify vulnerabilities.


## **Contributing**
1. Fork the repository.
2. Create a new branch (`feature-branch`).
3. Commit your changes.
4. Open a pull request.


## **Contact**
📧 **Email:** mr.prakhar@gmail.com  
📞 **WhatsApp/Mobile:** +91-9625708656  
🌍 **Website:** [appsbyprakhar.in](http://www.appsbyprakhar.in)


# mucp-viewer-django-web

---

# MUCP Django Viewer

## 📖 Introduction

Le Maitre et al. (2012) developed a generic species and area prioritization model Management Unit Control Plan (MUCP) Tool for use in prioritising invasive alien plant control operations in South Africa using spatial data (Forsyth et al. 2012).

It schedules treatments of invasions in the catchment, taking into account:

* Current state of invasions
* Benefits of clearing
* Treatments required
* Resources available in its budget

⚠️ The MUCP tool does **not** generate a detailed annual schedule of operations. The DEA–Natural Resources Management (NRM) programme provides an Annual Plan of Operations tool for that purpose.

This viewer provides a **web version** of the MUCP tool, built with **Django**. It can be run either:

1. Locally (on Windows/Linux, untested on macOS)
2. Using Docker (recommended for production)

---

## 🚀 Installation Options

### Option 1: Local Installation (Standalone)

#### 1. Get the Code

```bash
# Install Git if needed
# Windows: https://git-scm.com/download/win
# Ubuntu/Debian
sudo apt update && sudo apt install git

# Clone the repository
git clone https://gitlab.com/kirodh/mucp-viewer-django-web.git
cd mucp-viewer-django
```

#### 2. Install Python

* Windows: [Download Python 3.11+](https://www.python.org/downloads/)
  ✅ Make sure to check **"Add Python to PATH"** during installation.
* Linux (Debian/Ubuntu):

```bash
sudo apt update
sudo apt install python3 python3-pip
```

Verify installation:

```bash
python --version
```

#### 3. Setup a Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate it
# Windows (cmd):
venv\Scripts\activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux:
source venv/bin/activate
```

Deactivate later with:

```bash
deactivate
```

#### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 5. Initial Django Setup

```bash
# Apply migrations
python manage.py makemigrations
python manage.py migrate

# Create an admin user
python manage.py createsuperuser

# Collect static files (optional for dev, required for prod)
python manage.py collectstatic
```

#### 6. Run the Development Server

```bash
python manage.py runserver
```

* Viewer: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* Admin Panel: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

To allow access from other devices on your network:

```bash
python manage.py runserver 0.0.0.0:8000
```

---

### Option 2: Docker Installation (Recommended, for production)

Please see the manual for the full instructions on certificates, assigning a DNS, and other setup procedures before using Docker to spin up this MUCP tool.  

#### 1. Install Docker & Docker Compose

* [Docker Desktop (Windows/Mac)](https://www.docker.com/products/docker-desktop/)
* Linux:

```bash
sudo apt update
sudo apt install docker.io docker-compose -y
```

Verify installation:

```bash
docker --version
docker-compose --version
```

#### 2. Clone the Repository

```bash
git clone https://gitlab.com/kirodh/mucp-viewer-django-web.git
cd mucp-viewer-django
```

#### 3. Build and Start the Containers

```bash
docker-compose up --build -d
```

This will:

* Build the Django app
* Run migrations
* Start the web server


#### 4. Access the Application

* Viewer: [http://localhost:8000/](http://localhost:8000/)
* Admin Panel: [http://localhost:8000/admin/](http://localhost:8000/admin/)

#### 5. Create a Superuser (First-Time Setup)

```bash
docker-compose exec django python src/manage.py createsuperuser
```

---

## 🛠 Support & Debugging

For troubleshooting:

* Django Docs: [https://docs.djangoproject.com/](https://docs.djangoproject.com/)
* StackOverflow: [https://stackoverflow.com/](https://stackoverflow.com/)
* Youtube tutorials
* AI tools like ChatGPT for debugging assistance

---

## 📚 References

* Le Maitre et al. (2012). Generic species and area prioritization model for invasive alien plant control.
* Forsyth et al. (2012). Application of the MUCP tool in South Africa.

---

## Code Authors
- Kirodh Boodhraj

## 🌟 Special Mentions

We would like to extend our gratitude to the following individuals who contributed their knowledge, support, and vision to the development of the MUCP tool:

- **Greg Forsyth** — for his invaluable input on the theory, communication, and clear description of how the tool works.  
- **Ryan Blanchard** — for his assistance in understanding the core concepts and the project as a whole.  
- **William Stafford** — for his dedicated support, deep understanding of the broader economy surrounding the tool, and for helping to shape future uses and features. His exceptional insights into diverse industries (forestry, industrial, waste, etc.) greatly enriched the tool.  
- **Andrew Wannenburgh** — for initially funding the tool, contributing a key algorithm, and providing ongoing support for its continued development.  
- **David Le Maitre** *(in memoriam)* — who brought a profound understanding of ecological processes and was instrumental in developing the core theory of the MUCP tool. This tool is partially dedicated to his legacy.  

---
## License
Open-source. 

---
## 🙏 Funding & Acknowledgements

This project was developed under the funding and support of:

South Africa Department of Forestry, Fisheries and the Environment (DFFE)
🌍 https://www.dffe.gov.za

Council for Scientific and Industrial Research (CSIR)
🌍 https://www.csir.co.za

If you make use of this code or incorporate it in research or applications, please reference and acknowledge DFFE and CSIR.

---

END
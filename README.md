# TaskManager — Infraestructura DevOps en AWS

Sistema de gestión de tareas desplegado con arquitectura DevOps moderna en Amazon Web Services.

## Tecnologías utilizadas

| Componente | Tecnología |
|---|---|
| Cloud | Amazon Web Services (EC2, VPC, CloudWatch) |
| Contenedores | Docker + Docker Compose |
| Orquestación | Docker Swarm |
| CI/CD | GitHub Actions |
| Backend | Python / FastAPI |
| Base de datos | PostgreSQL 15 |
| Frontend | HTML + Nginx |
| Monitoreo | AWS CloudWatch |

## Arquitectura
Usuario → Load Balancer (ALB) → Docker Swarm (2 réplicas)
├── Backend (FastAPI)
├── Frontend (Nginx)
└── Base de datos (PostgreSQL)
GitHub → GitHub Actions → Build + Test → Deploy automático → EC2

## Estructura del proyecto
taskmanager/
├── backend/
│   ├── main.py          # API REST con FastAPI
│   ├── models.py        # Modelos de base de datos
│   ├── auth.py          # Autenticación JWT
│   ├── database.py      # Conexión PostgreSQL
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html       # Interfaz web
│   └── Dockerfile
├── docker-compose.yml   # Desarrollo local
├── docker-stack.yml     # Docker Swarm producción
└── .github/
└── workflows/
└── ci-cd.yml    # Pipeline CI/CD

## Endpoints de la API

| Método | Endpoint | Descripción |
|---|---|---|
| POST | /register | Registrar usuario |
| POST | /token | Login (JWT) |
| GET | /tasks | Listar tareas |
| POST | /tasks | Crear tarea |
| PUT | /tasks/{id} | Actualizar tarea |
| DELETE | /tasks/{id} | Eliminar tarea |
| GET | /stats | Estadísticas |
| GET | /health | Health check |

## Despliegue

```bash
# Clonar repositorio
git clone https://github.com/TU-USUARIO/taskmanager.git
cd taskmanager

# Levantar con Docker Compose (desarrollo)
docker-compose up -d --build

# Levantar con Docker Swarm (producción)
docker swarm init
docker build -t taskmanager-backend:latest ./backend
docker build -t taskmanager-frontend:latest ./frontend
docker stack deploy -c docker-stack.yml taskmanager
```

## Pipeline CI/CD

El pipeline de GitHub Actions ejecuta automáticamente:

1. Checkout del código
2. Verificación de sintaxis Python
3. Build de imágenes Docker
4. Deploy automático a EC2 via SSH

## Acceso

- Frontend: `http://IP-EC2`
- API Swagger: `http://IP-EC2:8000/docs`
- Health check: `http://IP-EC2:8000/health`

## Autor 

David Chiroy

Proyecto Final — Sistemas Operativos II

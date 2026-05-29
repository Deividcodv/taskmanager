from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr
import models, auth
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Manager API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Schemas -----
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class CategoryCreate(BaseModel):
    name: str
    color: str = "#3B82F6"

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: models.PriorityEnum = models.PriorityEnum.medium
    status: models.StatusEnum = models.StatusEnum.pending
    due_date: Optional[date] = None   # Cambiado de datetime a date
    category_id: Optional[int] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[models.PriorityEnum] = None
    status: Optional[models.StatusEnum] = None
    due_date: Optional[date] = None   # Cambiado de datetime a date
    category_id: Optional[int] = None

# ----- Endpoints -----
@app.post("/register", status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=auth.hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "Usuario creado", "id": db_user.id}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    return {"access_token": auth.create_access_token({"sub": user.username}), "token_type": "bearer"}

@app.get("/me")
def get_me(current_user=Depends(auth.get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "email": current_user.email}

@app.post("/categories", status_code=201)
def create_category(cat: CategoryCreate, db: Session = Depends(get_db), cu=Depends(auth.get_current_user)):
    c = models.Category(**cat.dict(), user_id=cu.id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

@app.get("/categories")
def get_categories(db: Session = Depends(get_db), cu=Depends(auth.get_current_user)):
    return db.query(models.Category).filter(models.Category.user_id == cu.id).all()

@app.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db), cu=Depends(auth.get_current_user)):
    c = db.query(models.Category).filter(models.Category.id == category_id, models.Category.user_id == cu.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")
    db.delete(c)
    db.commit()

@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate, db: Session = Depends(get_db), cu=Depends(auth.get_current_user)):
    due_dt = None
    if task.due_date:
        due_dt = datetime.combine(task.due_date, datetime.min.time())
    task_dict = task.dict(exclude={'due_date'})
    t = models.Task(**task_dict, user_id=cu.id, due_date=due_dt)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

@app.get("/tasks")
def get_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
    cu=Depends(auth.get_current_user)
):
    q = db.query(models.Task).filter(models.Task.user_id == cu.id)
    if status:
        q = q.filter(models.Task.status == status)
    if priority:
        q = q.filter(models.Task.priority == priority)
    if category_id:
        q = q.filter(models.Task.category_id == category_id)
    return q.order_by(models.Task.created_at.desc()).all()

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db), cu=Depends(auth.get_current_user)):
    t = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == cu.id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    update_data = task_update.dict(exclude_unset=True)
    if 'due_date' in update_data and update_data['due_date'] is not None:
        update_data['due_date'] = datetime.combine(update_data['due_date'], datetime.min.time())
    for k, v in update_data.items():
        setattr(t, k, v)
    if task_update.status == models.StatusEnum.completed:
        t.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(t)
    return t

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db), cu=Depends(auth.get_current_user)):
    t = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == cu.id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    db.delete(t)
    db.commit()

@app.get("/stats")
def get_stats(db: Session = Depends(get_db), cu=Depends(auth.get_current_user)):
    q = db.query(models.Task).filter(models.Task.user_id == cu.id)
    total = q.count()
    completed = q.filter(models.Task.status == "completed").count()
    pending = q.filter(models.Task.status == "pending").count()
    in_progress = q.filter(models.Task.status == "in_progress").count()
    return {"total": total, "completed": completed, "pending": pending, "in_progress": in_progress}

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}

"""用户注册 / 登录 / 会话 / 生成历史接口。"""
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from .. import db

router = APIRouter()


class AuthIn(BaseModel):
    username: str
    password: str
    nickname: str = ""


class HistoryIn(BaseModel):
    name: str
    title: str = ""
    poster_url: str = ""


def _token_from_header(authorization: str) -> str:
    return authorization.removeprefix("Bearer ").strip()


def current_user(authorization: str = Header(default="")) -> dict:
    user = db.user_from_token(_token_from_header(authorization))
    if user is None:
        raise HTTPException(status_code=401, detail="请先登录")
    return user


@router.post("/api/auth/register")
def register(body: AuthIn):
    try:
        user = db.create_user(body.username, body.password, body.nickname)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    token, _ = db.verify_login(body.username, body.password)
    return {"token": token, "user": user}


@router.post("/api/auth/login")
def login(body: AuthIn):
    try:
        token, user = db.verify_login(body.username, body.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"token": token, "user": user}


@router.post("/api/auth/logout")
def logout(authorization: str = Header(default="")):
    db.drop_token(_token_from_header(authorization))
    return {"ok": True}


@router.get("/api/auth/me")
def me(user: dict = Depends(current_user)):
    return {"user": user}


@router.get("/api/auth/history")
def get_history(user: dict = Depends(current_user)):
    return {"items": db.list_history(user["id"])}


@router.post("/api/auth/history")
def add_history(body: HistoryIn, user: dict = Depends(current_user)):
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="产品名不能为空")
    item = db.add_history(user["id"], body.name, body.title, body.poster_url)
    return {"item": item}


@router.delete("/api/auth/history/{hid}")
def delete_history(hid: int, user: dict = Depends(current_user)):
    if not db.delete_history(user["id"], hid):
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"ok": True}

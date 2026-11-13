from fastapi.concurrency import run_in_threadpool
from fastapi import HTTPException, status
import bcrypt
from user import user_schemas
from user import user_repository
from user import user_jwt
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

settings_mail = user_schemas.Settings_Mail()

mail_config = ConnectionConfig(
    MAIL_USERNAME=settings_mail.MAIL_USERNAME,
    MAIL_PASSWORD=settings_mail.MAIL_PASSWORD,
    MAIL_FROM=settings_mail.MAIL_FROM,
    MAIL_SERVER=settings_mail.MAIL_SERVER,
    MAIL_PORT=settings_mail.MAIL_PORT,
    MAIL_STARTTLS=settings_mail.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings_mail.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings_mail.USE_CREDENTIALS,
    VALIDATE_CERTS=settings_mail.VALIDATE_CERTS
)


async def sign_up(user: user_schemas.UserRegistration) -> dict:
    db_user = await user_repository.get_by_email(user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    hashed_password = await run_in_threadpool(
        lambda: bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    )
    await user_repository.create(email=user.email, name=user.name, password_hash=hashed_password)
    return {"message": "Регистрация прошла успешно", "email": user.email}


async def login(user: user_schemas.UserAuthorization) -> dict:
    db_user = await user_repository.get_by_email(user.email)
    if not db_user:
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")

    password_bytes = user.password.encode('utf-8')
    hashed_password = db_user["password_hash"].encode('utf-8')

    is_password_correct = await run_in_threadpool(
        lambda: bcrypt.checkpw(password_bytes, hashed_password)
    )
    if not is_password_correct:
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")

    token_data = {"id": db_user["id"], "email": db_user["email"], "purpose": "access"}
    access_token = user_jwt.create_access_token(data=token_data, TIME_TO_END_TOKEN_MIN=20160)
    return {"message": "Успешный вход.", "JWT_token": access_token, "token_type": "bearer"}


async def get_me(payload_of_token: dict) -> dict:
    db_user = await user_repository.get_by_id(payload_of_token["id"])
    return {"email": db_user["email"], "name": db_user["name"], "created_at": db_user["created_at"]}


async def password_recovery(email: str) -> dict:
    db_user = await user_repository.get_by_email(email)
    if not db_user:
        return {"message": "Если аккаунт существует, инструкции отправлены на email"}

    token_data = {"id": db_user["id"], "email": db_user["email"], "purpose": "password_recovery"}
    access_token = user_jwt.create_access_token(token_data, TIME_TO_END_TOKEN_MIN=15)

    # Ссылка на фронтенд (из .env)
    reset_link = f"{settings_mail.FRONTEND_URL}/reset-password/{access_token}"

    html_content = f"""
        <p>Вы запросили восстановление пароля.</p>
        <p>Для сброса пароля перейдите по ссылке (ссылка действительна 15 минут):</p>
        <a href="{reset_link}">{reset_link}</a>
        <p>Если вы не запрашивали восстановление, просто проигнорируйте это письмо.</p>
        """

    message = MessageSchema(
        subject="Восстановление пароля",
        recipients=[db_user["email"]],
        body=html_content,
        subtype=MessageType.html,
        mail_from=settings_mail.MAIL_FROM
    )

    fm = FastMail(mail_config)
    await fm.send_message(message)
    return {"message": "Если аккаунт существует, инструкции отправлены на email"}


async def password_recovery_change(new_password: str, payload_of_token: dict):
    db_user = await user_repository.get_by_id(payload_of_token["id"])
    password_hash = await run_in_threadpool(
        lambda: bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    )
    await user_repository.change(db_user["id"], db_user["email"], db_user["name"], password_hash)
    return {"message": "Пароль успешно изменен"}


async def profile_update(userData: user_schemas.UserUpdate, payload_of_token: dict):
    db_user = await user_repository.get_by_id(payload_of_token["id"])
    new_name = userData.name if userData.name is not None else db_user["name"]

    if new_name != db_user["name"]:
        await user_repository.change(db_user["id"], db_user["email"], new_name, db_user["password_hash"])

    if userData.email is not None and userData.email != db_user["email"]:
        db_new_email = await user_repository.get_by_email(userData.email)
        if not db_new_email:
            token_data = {"id": db_user["id"], "email": db_user["email"], "new_email": userData.email,
                          "purpose": "email_change"}
            access_token = user_jwt.create_access_token(token_data, TIME_TO_END_TOKEN_MIN=15)

            # Ссылка на фронтенд (из .env)
            reset_link = f"{settings_mail.FRONTEND_URL}/confirm-email/{access_token}"

            html_content = f"""
                <p>Вы запросили смену почты в профиле.</p>
                <p>Для подтверждения нового адреса перейдите по ссылке:</p>
                <a href="{reset_link}">{reset_link}</a>
            """
            message = MessageSchema(
                subject="Подтверждение смены почты",
                recipients=[userData.email],
                body=html_content,
                subtype=MessageType.html,
                mail_from=settings_mail.MAIL_FROM
            )
            fm = FastMail(mail_config)
            await fm.send_message(message)
        return {"message": "Если почта не занята, то подтверждение отправлено"}
    return {"message": "Данные успешно изменены"}


async def confirm_email_change(payload_of_token: dict) -> dict:
    db_user = await user_repository.get_by_id(payload_of_token["id"])
    new_email = payload_of_token["new_email"]
    if await user_repository.get_by_email(new_email):
        raise HTTPException(status_code=400, detail="Не удалось обновить почту")
    await user_repository.change(db_user["id"], new_email, db_user["name"], db_user["password_hash"])
    return {"message": "Почта успешно обновлена"}


async def password_update(passwordUpdate: user_schemas.PasswordUpdate, payload_of_token: dict):
    db_user = await user_repository.get_by_id(payload_of_token["id"])
    is_valid = await run_in_threadpool(
        lambda: bcrypt.checkpw(passwordUpdate.old_password.encode('utf-8'), db_user["password_hash"].encode('utf-8'))
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail="Старый пароль введен неверно")

    password_hash = await run_in_threadpool(
        lambda: bcrypt.hashpw(passwordUpdate.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    )
    await user_repository.change(db_user["id"], db_user["email"], db_user["name"], password_hash)
    return {"message": "Пароль успешно изменен"}
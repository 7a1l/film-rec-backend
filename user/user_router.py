from fastapi import APIRouter, status, Depends
from user import user_schemas
from user import user_controller
from user import user_jwt

router = APIRouter(prefix="/user", tags=["User"])

@router.post("/sign-up", status_code=status.HTTP_201_CREATED)
async def sign_up(user: user_schemas.UserRegistration):
    return await user_controller.sign_up(user)

@router.post("/login")
async def login(user: user_schemas.UserAuthorization):
    return await user_controller.login(user)

@router.post("/password-recovery")
async def password_recovery(passwordRecovery: user_schemas.PasswordRecovery):
    return await user_controller.password_recovery(passwordRecovery.email)

# --- ВОТ ЭТИХ ДВУХ НЕ ХВАТАЕТ ---

@router.patch("/password-recovery-change")
async def password_recovery_change(
    passwordChange: user_schemas.PasswordRecoveryChange,
    payload_of_token: dict = Depends(user_jwt.require_token_purpose("password_recovery"))
):
    return await user_controller.password_recovery_change(passwordChange.new_password, payload_of_token)

@router.patch("/confirm-email-change")
async def confirm_email_change(
    payload_of_token: dict = Depends(user_jwt.require_token_purpose("email_change"))
):
    return await user_controller.confirm_email_change(payload_of_token)

# ----------------------------------

@router.get("/me")
async def get_me(payload_of_token: dict = Depends(user_jwt.require_token_purpose("access"))):
    return await user_controller.get_me(payload_of_token)

@router.patch("/profile-update")
async def profile_update(userData: user_schemas.UserUpdate, payload_of_token: dict = Depends(user_jwt.require_token_purpose("access"))):
    return await user_controller.profile_update(userData, payload_of_token)

@router.patch("/password-update")
async def password_update(passwordUpdate: user_schemas.PasswordUpdate, payload_of_token: dict = Depends(user_jwt.require_token_purpose("access"))):
    return await user_controller.password_update(passwordUpdate, payload_of_token)
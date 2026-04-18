from src.services.storage import log_email


async def send_user_data(user_id: str, email: str) -> None:
    await log_email(user_id=user_id, email=email)

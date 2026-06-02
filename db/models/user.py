from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class User:
    """User model matching the database schema"""
    id: UUID
    user_id: Optional[str]
    name: str
    phone: Optional[str]
    email: Optional[str]
    role: str  # 'farmer', 'buyer', 'admin'
    region: str
    telegram_id: Optional[str]
    telegram_number: Optional[str]
    whatsapp_number: Optional[str]
    whatsapp_chat_id: Optional[str]
    lang: str  # 'en', 'fr'
    pic_folder: Optional[str]
    created_at: datetime
    updated_at: datetime
    verified: str  # 'true', 'false', 'pending'
    linking_code: Optional[str]
    code_expire_at: Optional[datetime]

    @classmethod
    def from_db_row(cls, row: dict) -> 'User':
        return cls(
            id=row['id'],
            user_id=row['user_id'],
            name=row['name'],
            phone=row['phone'],
            email=row['email'],
            role=row['role'],
            region=row['region'],
            telegram_id=row['telegram_id'],
            telegram_number=row['telegram_number'],
            whatsapp_number=row['whatsapp_number'],
            whatsapp_chat_id=row['whatsapp_chat_id'],
            lang=row['lang'],
            pic_folder=row['pic_folder'],
            verified=row['verified'],
            linking_code=row['linking_code'],
            code_expire_at=row['code_expire_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def is_farmer(self) -> bool:
        return self.role == 'farmer'

    def is_buyer(self) -> bool:
        return self.role == 'buyer'

    def is_admin(self) -> bool:
        return self.role == 'admin'

    def is_verified(self) -> bool:
        return self.verified == 'true'

    def is_pending_verification(self) -> bool:
        return self.verified == 'pending'

    def get_lang_display(self) -> str:
        """Get language display string, handling None"""
        return (self.lang or 'en').upper()

    def get_verification_status_display(self) -> str:
        """Get formatted verification status"""
        if self.verified == 'true':
            return "✅ Verified"
        elif self.verified == 'pending':
            return "⏳ Pending verification"
        else:
            return "❌ Not verified"

"""
موديل PostSurvey — الاستبيان البعدي (سؤالين ثابتين)، علاقة واحد-لواحد مع Student.
مطابق تماماً لجدول post_survey بـ wijhatak_schema_v2.sql.
"""

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import College, OpinionChange


class PostSurvey(Base):
    __tablename__ = "post_survey"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(
        BigInteger,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    opinion_change = Column(SAEnum(OpinionChange, name="opinion_change_enum"), nullable=False)
    preferred_major = Column(SAEnum(College, name="college_enum"), nullable=False)

    answered_at = Column(DateTime, nullable=False, server_default=func.now())

    student = relationship("Student", back_populates="post_survey")
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, JSON, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    subscriptions = relationship("Subscription", back_populates="user")


class Station(Base):
    __tablename__ = "stations"
    
    code = Column(String(10), primary_key=True)
    name = Column(String(255), nullable=False)
    region = Column(String(100))
    is_active = Column(Boolean, default=True)


class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    departure_station = Column(String(10), nullable=False)
    arrival_station = Column(String(10), nullable=False)
    departure_date = Column(Date, nullable=False)
    train_number = Column(String(20))
    seat_type = Column(String(50))
    departure_time_range = Column(String(20))
    check_frequency = Column(Integer, default=10)  # минуты
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_checked = Column(DateTime(timezone=True))
    
    user = relationship("User", back_populates="subscriptions")
    found_tickets = relationship("FoundTicket", back_populates="subscription")


class FoundTicket(Base):
    __tablename__ = "found_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    train_number = Column(String(20))
    departure_time = Column(DateTime(timezone=True))
    arrival_time = Column(DateTime(timezone=True))
    available_seats = Column(JSON)
    prices = Column(JSON)
    found_at = Column(DateTime(timezone=True), server_default=func.now())
    is_notified = Column(Boolean, default=False)
    
    subscription = relationship("Subscription", back_populates="found_tickets")


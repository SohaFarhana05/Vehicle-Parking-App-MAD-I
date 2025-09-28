from flask_sqlalchemy import SQLAlchemy # type: ignore
from datetime import datetime

db = SQLAlchemy()

class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer , primary_key = True)
    username = db.Column(db.String(20) , unique=True , nullable=False)
    password =db.Column(db.String(255),nullable =False)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20),unique=True, nullable=False)
    password = db.Column(db.String(255),nullable=False)
    full_name = db.Column(db.String(100),nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    reservations = db.relationship('Reservation', backref='user', cascade='all, delete-orphan')
    
    def get_current_reservation(self):
        """Get the current active reservation for this user"""
        return Reservation.query.filter_by(
            user_id=self.id, 
            leaving_timestamp=None
        ).first()

class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    maximum_number_of_spots = db.Column(db.Integer, nullable=False)
    spots = db.relationship('ParkingSpot', backref='lot', cascade='all, delete-orphan')

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False)
    status = db.Column(db.String(1), default='A')  # A for Available, R for Reserved, O for Occupied

class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reservation_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    parking_timestamp = db.Column(db.DateTime, nullable=True)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)
    parking_cost = db.Column(db.Float, nullable=True)

    spot = db.relationship('ParkingSpot', backref='reservations')
    
    def get_parking_duration(self):
        """Calculate parking duration in minutes"""
        if not self.parking_timestamp:
            return 0
        
        end_time = self.leaving_timestamp or datetime.utcnow()
        duration = end_time - self.parking_timestamp
        return duration.total_seconds() / 60
    
    def get_parking_duration_formatted(self):
        """Get parking duration in human-readable format"""
        minutes = self.get_parking_duration()
        if minutes == 0:
            return "Not parked"
        
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        
        if hours > 0:
            return f"{hours}h {mins}m"
        else:
            return f"{mins}m"
    
    def calculate_cost(self, lot_price):
        """Calculate parking cost based on actual time parked"""
        if not self.parking_timestamp:
            return 0.0
        
        end_time = self.leaving_timestamp or datetime.utcnow()
        time_difference = end_time - self.parking_timestamp
        
        # Convert to minutes for accurate billing
        total_minutes = time_difference.total_seconds() / 60
        
        # If parked for less than 1 minute, no charge
        if total_minutes < 1:
            return 0.0
        
        # Calculate cost based on minutes (lot_price is per hour, so divide by 60)
        cost_per_minute = lot_price / 60
        return round(total_minutes * cost_per_minute, 2)
    
    def get_status(self):
        """Get current status of the reservation"""
        if self.leaving_timestamp:
            return "Completed"
        elif self.parking_timestamp:
            return "Occupied"
        else:
            return "Reserved"
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import os
from models.models import db, Admin, User, ParkingLot, ParkingSpot, Reservation

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vehicle_parking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if not os.path.exists('./instance'):
    os.makedirs('./instance')

db.init_app(app)
bcrypt = Bcrypt(app)

with app.app_context():
    db.create_all()
    # Create Admin if not exists
    if not Admin.query.filter_by(username='admin').first():
        hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = Admin(username='admin', password=hashed_password)
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and bcrypt.check_password_hash(admin.password, password):
            session['admin_id'] = admin.id
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('user_dashboard'))
        
        flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/registration', methods=['POST', 'GET'])
def registration():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        if not username or not password or not full_name or not email or not phone:
            flash('All fields are required!', 'error')
            return render_template('registration.html')
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists!', 'error')
            return render_template('registration.html')
        
        try:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(
                username=username,
                password=hashed_password,
                full_name=full_name,
                email=email,
                phone=phone
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
    
    return render_template('registration.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('login'))
    
    lots = ParkingLot.query.all()
    users = User.query.all()
    total_spots = ParkingSpot.query.count()
    occupied_spots = ParkingSpot.query.filter_by(status='O').count()
    reserved_spots = ParkingSpot.query.filter_by(status='R').count()
    available_spots = ParkingSpot.query.filter_by(status='A').count()
    all_reservations = Reservation.query.order_by(Reservation.reservation_timestamp.desc()).all()
    
    return render_template('admin_dashboard.html', 
                         lots=lots, 
                         users=users, 
                         total_spots=total_spots,
                         occupied_spots=occupied_spots,
                         reserved_spots=reserved_spots,
                         available_spots=available_spots,
                         all_reservations=all_reservations)

@app.route('/create_lot', methods=['GET', 'POST'])
def create_lot():
    if 'admin_id' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        price_str = request.form.get('price')
        address = request.form.get('address')
        pin_code = request.form.get('pin_code')
        max_spots_str = request.form.get('max_spots')
        
        if not all([name, price_str, address, pin_code, max_spots_str]):
            flash('All fields are required!', 'error')
            return render_template('create_lot.html')
        
        try:
            price = float(price_str) if price_str else 0.0
            max_spots = int(max_spots_str) if max_spots_str else 0

            new_lot = ParkingLot(
                prime_location_name=name,
                price=price,
                address=address,
                pin_code=pin_code,
                maximum_number_of_spots=max_spots
            )
            
            db.session.add(new_lot)
            db.session.commit()
            
            # Create parking spots automatically
            for i in range(max_spots):
                spot = ParkingSpot(lot_id=new_lot.id, status='A')
                db.session.add(spot)
            
            db.session.commit()
            flash('Parking lot created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating lot: {str(e)}', 'error')
    
    return render_template('create_lot.html')

@app.route('/edit_lot/<int:lot_id>', methods=['GET', 'POST'])
def edit_lot(lot_id):
    if 'admin_id' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('login'))
    
    lot = ParkingLot.query.get_or_404(lot_id)
    
    if request.method == 'POST':
        lot.prime_location_name = request.form.get('name')
        price_str = request.form.get('price')
        if price_str:
            lot.price = float(price_str)
        lot.address = request.form.get('address')
        lot.pin_code = request.form.get('pin_code')
        
        try:
            db.session.commit()
            flash('Parking lot updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating lot: {str(e)}', 'error')
    
    return render_template('edit_lot.html', lot=lot)

@app.route('/delete_lot/<int:lot_id>')
def delete_lot(lot_id):
    if 'admin_id' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('login'))
    
    lot = ParkingLot.query.get_or_404(lot_id)
    
    try:
        db.session.delete(lot)
        db.session.commit()
        flash('Parking lot deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting lot: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/lot_details/<int:lot_id>')
def lot_details(lot_id):
    if 'admin_id' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('login'))
    
    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    
    return render_template('lot_details.html', lot=lot, spots=spots)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if 'admin_id' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.full_name = request.form.get('full_name')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')
        
        try:
            db.session.commit()
            flash('User details updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'error')
    
    return render_template('edit_user.html', user=user)

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'admin_id' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get_or_404(user_id)
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    lots = ParkingLot.query.all()
    
    # Get user's current active reservation
    current_reservation = user.get_current_reservation()
    
    # Get user's parking history
    history = Reservation.query.filter_by(user_id=user.id).order_by(Reservation.reservation_timestamp.desc()).all()
    
    return render_template('user_dashboard.html', 
                         user=user, 
                         lots=lots, 
                         current_reservation=current_reservation,
                         history=history)

@app.route('/view_lots')
def view_lots():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    lots = ParkingLot.query.all()
    lot_info = []
    
    for lot in lots:
        available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
        total_spots = ParkingSpot.query.filter_by(lot_id=lot.id).count()
        lot_info.append({
            'lot': lot,
            'available_spots': available_spots,
            'total_spots': total_spots
        })
    
    return render_template('view_lots.html', lot_info=lot_info)

@app.route('/reserve_spot/<int:lot_id>')
def reserve_spot(lot_id):
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    # Check if user already has an active reservation
    existing_reservation = Reservation.query.filter_by(
        user_id=session['user_id'], 
        leaving_timestamp=None
    ).first()
    
    if existing_reservation:
        flash('You already have an active parking reservation!', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Find first available spot in the lot
    available_spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='A').first()
    
    if not available_spot:
        flash('No available spots in this parking lot!', 'error')
        return redirect(url_for('view_lots'))
    
    try:
        # Reserve the spot (not occupy yet)
        available_spot.status = 'R'
        
        # Create reservation record
        reservation = Reservation(
            spot_id=available_spot.id,
            user_id=session['user_id']
        )
        
        db.session.add(reservation)
        db.session.commit()
        
        flash('Parking spot reserved successfully! You can now occupy it.', 'success')
        return redirect(url_for('user_dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error reserving spot: {str(e)}', 'error')
        return redirect(url_for('view_lots'))

@app.route('/occupy_spot')
def occupy_spot():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    # Get user's current reservation
    reservation = Reservation.query.filter_by(
        user_id=session['user_id'], 
        leaving_timestamp=None
    ).first()
    
    if not reservation:
        flash('You do not have any active reservation!', 'error')
        return redirect(url_for('user_dashboard'))
    
    try:
        # Update parking timestamp to current time (occupy the spot)
        reservation.parking_timestamp = datetime.utcnow()
        
        # Change spot status from Reserved to Occupied
        spot = ParkingSpot.query.get(reservation.spot_id)
        spot.status = 'O'
        
        db.session.commit()
        
        flash('Parking spot occupied successfully! Timer started.', 'success')
        return redirect(url_for('user_dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error occupying spot: {str(e)}', 'error')
        return redirect(url_for('user_dashboard'))

@app.route('/release_spot')
def release_spot():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    # Get user's current reservation
    reservation = Reservation.query.filter_by(
        user_id=session['user_id'], 
        leaving_timestamp=None
    ).first()
    
    if not reservation:
        flash('You do not have any active reservation!', 'error')
        return redirect(url_for('user_dashboard'))
    
    try:
        # Get spot and lot information
        spot = ParkingSpot.query.get(reservation.spot_id)
        if not spot:
            flash('Error: Parking spot not found!', 'error')
            return redirect(url_for('user_dashboard'))
            
        lot = ParkingLot.query.get(spot.lot_id)
        if not lot:
            flash('Error: Parking lot not found!', 'error')
            return redirect(url_for('user_dashboard'))
        
        # Calculate parking cost only if user actually occupied the spot
        cost = 0
        if reservation.parking_timestamp:
            parking_duration = datetime.utcnow() - reservation.parking_timestamp
            hours = parking_duration.total_seconds() / 3600
            cost = hours * lot.price
        
        # Update reservation
        reservation.leaving_timestamp = datetime.utcnow()
        reservation.parking_cost = round(cost, 2)
        
        # Release the spot
        spot.status = 'A'
        
        db.session.commit()
        
        if cost > 0:
            flash(f'Parking spot released! Total cost: ${cost:.2f}', 'success')
        else:
            flash('Reservation cancelled. No charges applied.', 'success')
        return redirect(url_for('user_dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error releasing spot: {str(e)}', 'error')
        return redirect(url_for('user_dashboard'))

@app.route('/parking_history')
def parking_history():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    # Get all user's reservations with lot information
    reservations = db.session.query(Reservation, ParkingSpot, ParkingLot).join(
        ParkingSpot, Reservation.spot_id == ParkingSpot.id
    ).join(
        ParkingLot, ParkingSpot.lot_id == ParkingLot.id
    ).filter(
        Reservation.user_id == session['user_id']
    ).order_by(Reservation.reservation_timestamp.desc()).all()
    
    return render_template('parking_history.html', reservations=reservations)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)
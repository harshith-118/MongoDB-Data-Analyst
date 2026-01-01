"""
Script to create a cinema database in MongoDB with sample collections and data.

This script creates:
- movies: Movie information
- theaters: Cinema theater locations
- showtimes: Movie showtimes at theaters
- customers: Customer information
- tickets: Ticket bookings
- reviews: Movie reviews
- staff: Theater staff members
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId
import random
from src.mongodb_analyst.config import MONGODB_URI

# Database name for cinema
CINEMA_DB_NAME = "cinema_db"

# Sample data
MOVIES = [
    {
        "title": "The Dark Knight",
        "genre": ["Action", "Crime", "Drama"],
        "director": "Christopher Nolan",
        "release_date": datetime(2008, 7, 18),
        "duration_minutes": 152,
        "rating": "PG-13",
        "imdb_rating": 9.0,
        "description": "Batman faces the Joker in this epic crime thriller.",
        "cast": ["Christian Bale", "Heath Ledger", "Aaron Eckhart"],
        "language": "English",
        "budget": 185000000,
        "box_office": 1005000000
    },
    {
        "title": "Inception",
        "genre": ["Sci-Fi", "Action", "Thriller"],
        "director": "Christopher Nolan",
        "release_date": datetime(2010, 7, 16),
        "duration_minutes": 148,
        "rating": "PG-13",
        "imdb_rating": 8.8,
        "description": "A thief enters people's dreams to steal secrets.",
        "cast": ["Leonardo DiCaprio", "Marion Cotillard", "Tom Hardy"],
        "language": "English",
        "budget": 160000000,
        "box_office": 836800000
    },
    {
        "title": "The Matrix",
        "genre": ["Sci-Fi", "Action"],
        "director": "Lana Wachowski",
        "release_date": datetime(1999, 3, 31),
        "duration_minutes": 136,
        "rating": "R",
        "imdb_rating": 8.7,
        "description": "A computer hacker learns about the true nature of reality.",
        "cast": ["Keanu Reeves", "Laurence Fishburne", "Carrie-Anne Moss"],
        "language": "English",
        "budget": 63000000,
        "box_office": 467200000
    },
    {
        "title": "Parasite",
        "genre": ["Thriller", "Drama", "Comedy"],
        "director": "Bong Joon-ho",
        "release_date": datetime(2019, 5, 30),
        "duration_minutes": 132,
        "rating": "R",
        "imdb_rating": 8.5,
        "description": "A poor family schemes to become employed by a wealthy family.",
        "cast": ["Song Kang-ho", "Lee Sun-kyun", "Cho Yeo-jeong"],
        "language": "Korean",
        "budget": 11400000,
        "box_office": 258800000
    },
    {
        "title": "Interstellar",
        "genre": ["Sci-Fi", "Drama", "Adventure"],
        "director": "Christopher Nolan",
        "release_date": datetime(2014, 11, 7),
        "duration_minutes": 169,
        "rating": "PG-13",
        "imdb_rating": 8.6,
        "description": "A team of explorers travel through a wormhole in space.",
        "cast": ["Matthew McConaughey", "Anne Hathaway", "Jessica Chastain"],
        "language": "English",
        "budget": 165000000,
        "box_office": 677500000
    },
    {
        "title": "Spirited Away",
        "genre": ["Animation", "Adventure", "Family"],
        "director": "Hayao Miyazaki",
        "release_date": datetime(2001, 7, 20),
        "duration_minutes": 125,
        "rating": "PG",
        "imdb_rating": 8.6,
        "description": "A young girl enters a world of spirits.",
        "cast": ["Rumi Hiiragi", "Miyu Irino", "Mari Natsuki"],
        "language": "Japanese",
        "budget": 19000000,
        "box_office": 395800000
    },
    {
        "title": "The Shawshank Redemption",
        "genre": ["Drama"],
        "director": "Frank Darabont",
        "release_date": datetime(1994, 9, 23),
        "duration_minutes": 142,
        "rating": "R",
        "imdb_rating": 9.3,
        "description": "Two imprisoned men bond over a number of years.",
        "cast": ["Tim Robbins", "Morgan Freeman", "Bob Gunton"],
        "language": "English",
        "budget": 25000000,
        "box_office": 58300000
    },
    {
        "title": "Pulp Fiction",
        "genre": ["Crime", "Drama"],
        "director": "Quentin Tarantino",
        "release_date": datetime(1994, 10, 14),
        "duration_minutes": 154,
        "rating": "R",
        "imdb_rating": 8.9,
        "description": "The lives of two mob hitmen, a boxer, and others intertwine.",
        "cast": ["John Travolta", "Uma Thurman", "Samuel L. Jackson"],
        "language": "English",
        "budget": 8000000,
        "box_office": 214200000
    }
]

THEATERS = [
    {
        "name": "CinemaMax Downtown",
        "location": {
            "address": "123 Main Street",
            "city": "New York",
            "state": "NY",
            "zipcode": "10001",
            "coordinates": {"lat": 40.7128, "lng": -74.0060}
        },
        "screens": 8,
        "total_seats": 1200,
        "amenities": ["IMAX", "3D", "Dolby Atmos", "Reclining Seats", "Snack Bar"],
        "phone": "+1-212-555-0101",
        "email": "downtown@cinemamax.com"
    },
    {
        "name": "CinemaMax Uptown",
        "location": {
            "address": "456 Broadway",
            "city": "New York",
            "state": "NY",
            "zipcode": "10013",
            "coordinates": {"lat": 40.7282, "lng": -74.0776}
        },
        "screens": 6,
        "total_seats": 900,
        "amenities": ["3D", "Dolby Atmos", "Reclining Seats", "Snack Bar", "Arcade"],
        "phone": "+1-212-555-0102",
        "email": "uptown@cinemamax.com"
    },
    {
        "name": "CinemaMax Central",
        "location": {
            "address": "789 Park Avenue",
            "city": "New York",
            "state": "NY",
            "zipcode": "10021",
            "coordinates": {"lat": 40.7681, "lng": -73.9719}
        },
        "screens": 10,
        "total_seats": 1500,
        "amenities": ["IMAX", "3D", "4DX", "Dolby Atmos", "VIP Lounge", "Restaurant"],
        "phone": "+1-212-555-0103",
        "email": "central@cinemamax.com"
    }
]

CUSTOMER_NAMES = [
    ("John", "Smith", "john.smith@email.com"),
    ("Sarah", "Johnson", "sarah.j@email.com"),
    ("Michael", "Brown", "michael.brown@email.com"),
    ("Emily", "Davis", "emily.davis@email.com"),
    ("David", "Wilson", "david.wilson@email.com"),
    ("Jessica", "Martinez", "jessica.m@email.com"),
    ("James", "Anderson", "james.anderson@email.com"),
    ("Lisa", "Taylor", "lisa.taylor@email.com"),
    ("Robert", "Thomas", "robert.t@email.com"),
    ("Amanda", "Jackson", "amanda.jackson@email.com"),
    ("William", "White", "william.white@email.com"),
    ("Ashley", "Harris", "ashley.harris@email.com"),
    ("Christopher", "Martin", "chris.martin@email.com"),
    ("Michelle", "Thompson", "michelle.t@email.com"),
    ("Daniel", "Garcia", "daniel.garcia@email.com"),
    ("Stephanie", "Martinez", "stephanie.m@email.com"),
    ("Matthew", "Robinson", "matt.robinson@email.com"),
    ("Nicole", "Clark", "nicole.clark@email.com"),
    ("Anthony", "Rodriguez", "anthony.r@email.com"),
    ("Melissa", "Lewis", "melissa.lewis@email.com")
]

STAFF_NAMES = [
    ("Alice", "Manager", "Manager"),
    ("Bob", "Cashier", "Cashier"),
    ("Charlie", "Projectionist", "Projectionist"),
    ("Diana", "Usher", "Usher"),
    ("Eve", "Concessions", "Concessions"),
    ("Frank", "Security", "Security"),
    ("Grace", "Manager", "Manager"),
    ("Henry", "Cashier", "Cashier")
]


def generate_phone():
    """Generate a random phone number"""
    return f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"


def generate_showtimes(movie_ids, theater_ids):
    """Generate showtimes for movies at theaters"""
    showtimes = []
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Generate showtimes for the next 7 days
    for day in range(7):
        date = base_date + timedelta(days=day)
        
        for theater_id in theater_ids:
            # Each theater shows 3-5 movies per day
            movies_for_theater = random.sample(movie_ids, random.randint(3, min(5, len(movie_ids))))
            
            for movie_id in movies_for_theater:
                # Each movie has 3-5 showtimes per day
                num_showtimes = random.randint(3, 5)
                times = [10, 13, 16, 19, 22]  # Common showtimes
                selected_times = random.sample(times, min(num_showtimes, len(times)))
                
                for hour in selected_times:
                    screen_num = random.randint(1, 8)
                    showtime = {
                        "movie_id": movie_id,
                        "theater_id": theater_id,
                        "screen_number": screen_num,
                        "show_datetime": date.replace(hour=hour, minute=0),
                        "available_seats": random.randint(50, 200),
                        "total_seats": random.randint(150, 250),
                        "ticket_price": round(random.uniform(8.00, 15.00), 2),
                        "format": random.choice(["2D", "3D", "IMAX", "4DX"])
                    }
                    showtimes.append(showtime)
    
    return showtimes


def generate_tickets(customer_ids, showtime_ids):
    """Generate ticket bookings"""
    tickets = []
    
    # Generate 50-100 tickets
    num_tickets = random.randint(50, 100)
    
    for _ in range(num_tickets):
        customer_id = random.choice(customer_ids)
        showtime_id = random.choice(showtime_ids)
        num_seats = random.randint(1, 4)
        
        ticket = {
            "customer_id": customer_id,
            "showtime_id": showtime_id,
            "booking_date": datetime.now() - timedelta(days=random.randint(0, 30)),
            "num_seats": num_seats,
            "total_price": round(random.uniform(10.00, 60.00), 2),
            "payment_method": random.choice(["Credit Card", "Debit Card", "Cash", "Online"]),
            "status": random.choice(["Confirmed", "Cancelled", "Used"]),
            "seat_numbers": [f"{chr(65 + random.randint(0, 10))}{random.randint(1, 20)}" for _ in range(num_seats)]
        }
        tickets.append(ticket)
    
    return tickets


def generate_reviews(movie_ids, customer_ids):
    """Generate movie reviews"""
    reviews = []
    
    # Generate 30-50 reviews
    num_reviews = random.randint(30, 50)
    
    review_texts = [
        "Amazing movie! Highly recommend it.",
        "Great storyline and acting. Worth watching.",
        "One of the best movies I've seen this year.",
        "Good movie but could have been better.",
        "Not my cup of tea, but well made.",
        "Brilliant cinematography and direction.",
        "A masterpiece! Will watch again.",
        "Entertaining but predictable plot.",
        "Outstanding performance by the cast.",
        "Disappointing ending, but good overall."
    ]
    
    for _ in range(num_reviews):
        movie_id = random.choice(movie_ids)
        customer_id = random.choice(customer_ids)
        rating = random.randint(1, 5)
        
        review = {
            "movie_id": movie_id,
            "customer_id": customer_id,
            "rating": rating,
            "review_text": random.choice(review_texts),
            "review_date": datetime.now() - timedelta(days=random.randint(0, 90)),
            "helpful_count": random.randint(0, 50)
        }
        reviews.append(review)
    
    return reviews


def create_cinema_database():
    """Main function to create the cinema database with all collections"""
    print("🎬 Setting up Cinema Database...")
    print("=" * 60)
    
    # Connect to MongoDB
    try:
        client = MongoClient(MONGODB_URI)
        print(f"✅ Connected to MongoDB at {MONGODB_URI}")
        
        # Create/access database
        db = client[CINEMA_DB_NAME]
        print(f"✅ Using database: {CINEMA_DB_NAME}")
        
        # Clear existing collections if they exist
        print("\n🗑️  Clearing existing collections...")
        for collection_name in ["movies", "theaters", "showtimes", "customers", "tickets", "reviews", "staff"]:
            db[collection_name].drop()
            print(f"   - Dropped {collection_name}")
        
        # Insert Movies
        print("\n📽️  Inserting movies...")
        movies_result = db.movies.insert_many(MOVIES)
        movie_ids = movies_result.inserted_ids
        print(f"   ✅ Inserted {len(movie_ids)} movies")
        
        # Insert Theaters
        print("\n🏢 Inserting theaters...")
        theaters_result = db.theaters.insert_many(THEATERS)
        theater_ids = theaters_result.inserted_ids
        print(f"   ✅ Inserted {len(theater_ids)} theaters")
        
        # Insert Customers
        print("\n👥 Inserting customers...")
        customers = []
        for first_name, last_name, email in CUSTOMER_NAMES:
            customer = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": generate_phone(),
                "date_of_birth": datetime(1980 + random.randint(0, 30), random.randint(1, 12), random.randint(1, 28)),
                "membership_status": random.choice(["Regular", "Premium", "VIP", "None"]),
                "join_date": datetime.now() - timedelta(days=random.randint(0, 365)),
                "total_bookings": random.randint(0, 50)
            }
            customers.append(customer)
        
        customers_result = db.customers.insert_many(customers)
        customer_ids = customers_result.inserted_ids
        print(f"   ✅ Inserted {len(customer_ids)} customers")
        
        # Insert Staff
        print("\n👔 Inserting staff...")
        staff = []
        for first_name, last_name, role in STAFF_NAMES:
            staff_member = {
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "email": f"{first_name.lower()}.{last_name.lower()}@cinemamax.com",
                "phone": generate_phone(),
                "hire_date": datetime.now() - timedelta(days=random.randint(30, 1095)),
                "theater_id": random.choice(theater_ids),
                "salary": round(random.uniform(30000, 60000), 2)
            }
            staff.append(staff_member)
        
        staff_result = db.staff.insert_many(staff)
        print(f"   ✅ Inserted {len(staff_result.inserted_ids)} staff members")
        
        # Insert Showtimes
        print("\n🎫 Generating showtimes...")
        showtimes = generate_showtimes(movie_ids, theater_ids)
        showtimes_result = db.showtimes.insert_many(showtimes)
        showtime_ids = showtimes_result.inserted_ids
        print(f"   ✅ Inserted {len(showtime_ids)} showtimes")
        
        # Insert Tickets
        print("\n🎟️  Generating tickets...")
        tickets = generate_tickets(customer_ids, showtime_ids)
        tickets_result = db.tickets.insert_many(tickets)
        print(f"   ✅ Inserted {len(tickets_result.inserted_ids)} tickets")
        
        # Insert Reviews
        print("\n⭐ Generating reviews...")
        reviews = generate_reviews(movie_ids, customer_ids)
        reviews_result = db.reviews.insert_many(reviews)
        print(f"   ✅ Inserted {len(reviews_result.inserted_ids)} reviews")
        
        # Create indexes for better query performance
        print("\n📊 Creating indexes...")
        
        # Movies indexes
        db.movies.create_index("title")
        db.movies.create_index("genre")
        db.movies.create_index("director")
        print("   ✅ Movies indexes created")
        
        # Theaters indexes
        db.theaters.create_index("name")
        db.theaters.create_index("location.city")
        print("   ✅ Theaters indexes created")
        
        # Showtimes indexes
        db.showtimes.create_index("movie_id")
        db.showtimes.create_index("theater_id")
        db.showtimes.create_index("show_datetime")
        db.showtimes.create_index([("movie_id", 1), ("theater_id", 1), ("show_datetime", 1)])
        print("   ✅ Showtimes indexes created")
        
        # Customers indexes
        db.customers.create_index("email", unique=True)
        db.customers.create_index("last_name")
        print("   ✅ Customers indexes created")
        
        # Tickets indexes
        db.tickets.create_index("customer_id")
        db.tickets.create_index("showtime_id")
        db.tickets.create_index("booking_date")
        print("   ✅ Tickets indexes created")
        
        # Reviews indexes
        db.reviews.create_index("movie_id")
        db.reviews.create_index("customer_id")
        db.reviews.create_index("rating")
        print("   ✅ Reviews indexes created")
        
        # Staff indexes
        db.staff.create_index("theater_id")
        db.staff.create_index("role")
        print("   ✅ Staff indexes created")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📈 Database Summary:")
        print("=" * 60)
        print(f"   Movies:      {db.movies.count_documents({})}")
        print(f"   Theaters:    {db.theaters.count_documents({})}")
        print(f"   Showtimes:   {db.showtimes.count_documents({})}")
        print(f"   Customers:   {db.customers.count_documents({})}")
        print(f"   Tickets:     {db.tickets.count_documents({})}")
        print(f"   Reviews:     {db.reviews.count_documents({})}")
        print(f"   Staff:       {db.staff.count_documents({})}")
        print("=" * 60)
        print("\n✅ Cinema database setup complete!")
        print(f"\n💡 To use this database, update your .env file:")
        print(f"   MONGODB_DATABASE={CINEMA_DB_NAME}")
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise


if __name__ == "__main__":
    create_cinema_database()

